# services/tiktok_repost.py
import os
import asyncio
from playwright.async_api import async_playwright

try:
    from playwright_stealth import stealth_async
    STEALTH_AVAILABLE = True
except ImportError:
    STEALTH_AVAILABLE = False
    print("⚠️ playwright-stealth not installed")

try:
    from pyvirtualdisplay import Display
    DISPLAY_AVAILABLE = True
except ImportError:
    DISPLAY_AVAILABLE = False
    print("⚠️ pyvirtualdisplay not installed")


class TikTokRepostManager:
    """مدير حذف الريبوستات من تيك توك باستخدام QR Login"""

    def __init__(self, download_path="downloads"):
        self.download_path = download_path
        os.makedirs(download_path, exist_ok=True)
        self.sessions = {}
        self.displays = {}  # {user_id: Display}

    async def start_login(self, user_id: int):
        """فتح المتصفح، جلب QR، وإرجاع صورة"""
        try:
            # ✅ تشغيل شاشة افتراضية مؤقتة
            if DISPLAY_AVAILABLE:
                display = Display(visible=0, size=(1280, 800))
                display.start()
                self.displays[user_id] = display
                print(f"✅ Xvfb display started for user {user_id}")

            playwright = await async_playwright().start()

            browser = await playwright.chromium.launch(
                headless=False,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-features=IsolateOrigins,site-per-process",
                    "--window-size=1280,800",
                ],
            )

            context = await browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                locale="en-US",
                timezone_id="America/New_York",
            )

            page = await context.new_page()

            if STEALTH_AVAILABLE:
                try:
                    await stealth_async(page)
                    print("✅ Stealth applied")
                except Exception as e:
                    print(f"⚠️ Stealth error: {e}")

            await page.goto(
                "https://www.tiktok.com/login/qrcode",
                wait_until="domcontentloaded",
                timeout=60000,
            )

            await asyncio.sleep(6)

            try:
                await page.click("text=Use QR code", timeout=5000)
                await asyncio.sleep(3)
            except:
                pass

            qr_path = os.path.join(self.download_path, f"tiktok_qr_{user_id}.png")

            qr_element = await page.query_selector(
                "img[alt*='QR'], canvas, [data-e2e='qr-code']"
            )

            if qr_element:
                await qr_element.screenshot(path=qr_path)
            else:
                await page.screenshot(
                    path=qr_path,
                    clip={"x": 400, "y": 200, "width": 480, "height": 480},
                )

            self.sessions[user_id] = {
                "playwright": playwright,
                "browser": browser,
                "context": context,
                "page": page,
            }

            return qr_path

        except Exception as e:
            print(f"❌ TikTok QR Error: {e}")
            return None

    async def wait_login(self, user_id: int, timeout: int = 180):
        """الانتظار لحد ما المستخدم يمسح الـ QR"""
        if user_id not in self.sessions:
            return False

        page = self.sessions[user_id]["page"]
        start = asyncio.get_event_loop().time()

        while (asyncio.get_event_loop().time() - start) < timeout:
            try:
                url = page.url

                if "/login" not in url and "tiktok.com" in url:
                    avatar = await page.query_selector(
                        "[data-e2e='profile-icon'], "
                        "[data-e2e='nav-profile'], "
                        "a[href*='/@']"
                    )
                    if avatar:
                        return True

                await asyncio.sleep(3)

            except Exception as e:
                print(f"⚠️ Login check error: {e}")
                await asyncio.sleep(3)

        return False

    async def delete_reposts(self, user_id: int):
        """حذف كل الريبوستات"""
        if user_id not in self.sessions:
            return {"success": False, "error": "No active session"}

        page = self.sessions[user_id]["page"]

        try:
            await page.goto(
                "https://www.tiktok.com/reposts",
                wait_until="domcontentloaded",
                timeout=60000,
            )

            await asyncio.sleep(6)

            deleted = 0

            for _ in range(30):
                buttons = await page.query_selector_all(
                    "[data-e2e='repost-unrepost-btn'], "
                    "[data-e2e='repost-btn']"
                )

                if not buttons:
                    await page.evaluate(
                        "window.scrollTo(0, document.body.scrollHeight)"
                    )
                    await asyncio.sleep(4)

                    buttons = await page.query_selector_all(
                        "[data-e2e='repost-unrepost-btn'], "
                        "[data-e2e='repost-btn']"
                    )

                    if not buttons:
                        break

                for btn in buttons[:5]:
                    try:
                        await btn.click()
                        await asyncio.sleep(1.5)

                        confirm = await page.query_selector(
                            "button:has-text('Remove'), "
                            "button:has-text('إزالة'), "
                            "[data-e2e='confirm-btn']"
                        )

                        if confirm:
                            await confirm.click()

                        deleted += 1
                        await asyncio.sleep(4)

                    except Exception as e:
                        print(f"⚠️ Delete one error: {e}")
                        continue

                await page.evaluate(
                    "window.scrollTo(0, document.body.scrollHeight)"
                )
                await asyncio.sleep(3)

            return {"success": True, "deleted": deleted}

        except Exception as e:
            print(f"❌ Delete reposts error: {e}")
            return {"success": False, "error": str(e)[:150]}

    async def cleanup(self, user_id: int):
        """تنظيف الجلسة"""
        if user_id in self.sessions:
            try:
                await self.sessions[user_id]["browser"].close()
                await self.sessions[user_id]["playwright"].stop()
            except:
                pass
            del self.sessions[user_id]

        # ✅ إيقاف الشاشة الافتراضية
        if user_id in self.displays:
            try:
                self.displays[user_id].stop()
                print(f"✅ Xvfb display stopped for user {user_id}")
            except:
                pass
            del self.displays[user_id]

        qr = os.path.join(self.download_path, f"tiktok_qr_{user_id}.png")
        if os.path.exists(qr):
            try:
                os.remove(qr)
            except:
                pass


repost_manager = TikTokRepostManager()
