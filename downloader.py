# downloader.py
import os
import asyncio
import yt_dlp
from datetime import datetime
from collections import deque


class Downloader:
    def __init__(self, download_path: str, max_concurrent: int = 3):
        self.download_path = download_path
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.queue = deque()
        self.active = 0
        self.success = 0
        self.failed = 0
        self.started = False

        os.makedirs(self.download_path, exist_ok=True)

    async def start(self):
        self.started = True
        print("🚀 Downloader Engine Started")

    def get_stats(self):
        return {
            "queue_size": len(self.queue),
            "active": self.active,
            "success": self.success,
            "failed": self.failed,
        }

    async def download(self, url: str, quality="720", audio=False):
        async with self.semaphore:
            self.active += 1
            try:
                loop = asyncio.get_event_loop()
                result = await asyncio.wait_for(
                    loop.run_in_executor(
                        None,
                        self._download_sync,
                        url,
                        quality,
                        audio
                    ),
                    timeout=120
                )
                self.success += 1
                return result

            except asyncio.TimeoutError:
                self.failed += 1
                return {"success": False, "error": "⚠️ التحميل استغرق وقتاً طويلاً (تم إلغاؤه)"}

            except Exception as e:
                self.failed += 1
                return {"success": False, "error": str(e)}

            finally:
                self.active -= 1

    def _download_sync(self, url, quality, audio):
        opts = self._build_opts(quality, audio, url)

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                # نجيب المعلومات أولاً
                info = ydl.extract_info(url, download=False)
                if info:
                    # ثم نبدأ التحميل
                    ydl.download([url])
                
                if info is None:
                    return {"success": False, "error": "⚠️ الرابط غير صحيح أو غير مدعوم"}

                file_path = ydl.prepare_filename(info)

                if audio:
                    file_path = os.path.splitext(file_path)[0] + ".mp3"

                if not os.path.exists(file_path):
                    return {"success": False, "error": "⚠️ الملف لم يتم تحميله بنجاح"}

                return {
                    "success": True,
                    "file_path": file_path,
                    "title": info.get("title", "Unknown"),
                    "duration": info.get("duration", 0),
                    "timestamp": datetime.now().isoformat(),
                }

        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e)
            if "Sign in to confirm" in error_msg:
                return {"success": False, "error": "⚠️ يوتيوب طلب تسجيل دخول\n💡 حمّل ملف cookies.txt وارفعه على GitHub"}
            return {"success": False, "error": f"⚠️ خطأ في التحميل: {error_msg[:100]}"}

        except Exception as e:
            return {"success": False, "error": f"⚠️ حدث خطأ: {str(e)[:100]}"}

    def _build_opts(self, quality, audio, url=None):
        quality_map = {
            "144": "worst[height<=144]",
            "240": "best[height<=240]",
            "360": "best[height<=360]",
            "480": "best[height<=480]",
            "720": "best[height<=720]",
            "1080": "best[height<=1080]",
        }

        fmt = quality_map.get(quality, "best[height<=720]")

        # تحديد صيغة التحميل
        if quality in ["720", "1080"]:
            format_spec = f"bestvideo[height<={quality}]+bestaudio/best[height<={quality}]"
        else:
            format_spec = fmt

        opts = {
            "outtmpl": os.path.join(self.download_path, "%(title)s.%(ext)s"),
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": True,
            "noplaylist": True,
            "merge_output_format": "mp4",
        }

        # تحديد ملف الكوكيز حسب المنصة
        cookies_file = self._get_cookies_file(url)
        if cookies_file and os.path.exists(cookies_file):
            opts["cookiefile"] = cookies_file
            print(f"🍪 Using cookies: {cookies_file}")

        # معاملة خاصة لتيك توك
        if url and "tiktok" in url:
            opts["extractor_args"] = {
                "tiktok": {
                    "without_watermark": ["true"],
                }
            }

        if audio:
            opts.update({
                "format": "bestaudio/best",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
            })
        else:
            opts.update({
                "format": format_spec,
            })

        return opts

    def _get_cookies_file(self, url):
        """تحديد ملف الكوكيز المناسب حسب المنصة"""
        if not url:
            return None

        base_dir = os.path.dirname(__file__)

        # كوكيز يوتيوب
        if "youtube.com" in url or "youtu.be" in url:
            cookies_path = os.path.join(base_dir, "cookies_youtube.txt")
            if os.path.exists(cookies_path):
                return cookies_path

        # كوكيز فيسبوك
        if "facebook.com" in url or "fb.watch" in url:
            cookies_path = os.path.join(base_dir, "cookies_facebook.txt")
            if os.path.exists(cookies_path):
                return cookies_path

        # كوكيز انستجرام
        if "instagram.com" in url:
            cookies_path = os.path.join(base_dir, "cookies_instagram.txt")
            if os.path.exists(cookies_path):
                return cookies_path

        # كوكيز تويتر
        if "twitter.com" in url or "x.com" in url:
            cookies_path = os.path.join(base_dir, "cookies_twitter.txt")
            if os.path.exists(cookies_path):
                return cookies_path

        # لو مفيش كوكيز مخصصة، جرب الملف الأساسي
        default_cookies = os.path.join(base_dir, "cookies.txt")
        if os.path.exists(default_cookies):
            return default_cookies

        return None
