# services/tiktok_repost.py
import os
import asyncio
from playwright.async_api import async_playwright


class TikTokRepostManager:
    """مدير حذف الريبوستات من تيك توك باستخدام QR Login"""

    def __init__(self, download_path="downloads"):
        self.download_path = download_path
        os.makedirs(download_path, exist_ok=True)
        self.sessions = {}  # {user_id: {playwright, browser, context, page}}

    async def start_login(self, user_id: int):
        """فتح المتصفح، جلب QR، وإرجاع صورة"""
        try:
            playwright = await async_playwright().start()

            browser = await playwright.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled",
                ],
            )

            context = await browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
            )

            page = await context.new_page()

            await page.goto(
                "https://www.tiktok.com/login/qrcode",
                wait_until="networkidle",
                timeout=60000,
            )

            await asyncio.sleep(5)

            # محاولة الضغط على "Use QR code" لو الصفحة طلبت
            try:
                await page.click("text=Use QR code", timeout=5000)
                await asyncio.sleep(3)
            except:
                pass

            # أخذ لقطة شاشة للـ QR
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

                # لو اتغير الرابط عن صفحة تسجيل الدخول
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
                wait_until="networkidle",
                timeout=60000,
            )

            await asyncio.sleep(5)

            deleted = 0

            # 30 جولة كحد أقصى (سلامة)
            for _ in range(30):
                # البحث عن أزرار "إلغاء الريبوست"
                buttons = await page.query_selector_all(
                    "[data-e2e='repost-unrepost-btn'], "
                    "[data-e2e='repost-btn']"
                )

                if not buttons:
                    # نزول لأسفل لتحميل المزيد
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

                # معالجة 5 أزرار في المرة
                for btn in buttons[:5]:
                    try:
                        await btn.click()
                        await asyncio.sleep(1.5)

                        # زر التأكيد
                        confirm = await page.query_selector(
                            "button:has-text('Remove'), "
                            "button:has-text('إزالة'), "
                            "[data-e2e='confirm-btn']"
                        )

                        if confirm:
                            await confirm.click()

                        deleted += 1

                        # تأخير بين الحذف والتاني (عشان الحساب مياخدش بان)
                        await asyncio.sleep(4)

                    except Exception as e:
                        print(f"⚠️ Delete one error: {e}")
                        continue

                # نزول لتحميل المزيد
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

        qr = os.path.join(self.download_path, f"tiktok_qr_{user_id}.png")
        if os.path.exists(qr):
            try:
                os.remove(qr)
            except:
                pass


# Singleton
repost_manager = TikTokRepostManager()
