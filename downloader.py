# downloader.py - مع رسائل خطأ مفصلة
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
                return {
                    "success": False,
                    "error": "⏰ استغرق التحميل وقتاً طويلاً (تم إلغاؤه)",
                    "error_code": "TIMEOUT"
                }

            except Exception as e:
                self.failed += 1
                return {
                    "success": False,
                    "error": f"⚠️ حدث خطأ: {str(e)[:100]}",
                    "error_code": "UNKNOWN"
                }

            finally:
                self.active -= 1

    def _download_sync(self, url, quality, audio):
        opts = self._build_opts(quality, audio, url)

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)

                if info is None:
                    return {
                        "success": False,
                        "error": "❌ الرابط غير صحيح أو غير مدعوم",
                        "error_code": "INVALID_URL"
                    }

                file_path = ydl.prepare_filename(info)

                if audio:
                    file_path = os.path.splitext(file_path)[0] + ".mp3"

                if not os.path.exists(file_path):
                    return {
                        "success": False,
                        "error": "❌ الملف لم يتم تحميله بنجاح",
                        "error_code": "FILE_NOT_FOUND"
                    }

                return {
                    "success": True,
                    "file_path": file_path,
                    "title": info.get("title", "Unknown"),
                    "duration": info.get("duration", 0),
                }

        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e)

            # ===== رسائل خطأ مفصلة =====
            if "Sign in to confirm" in error_msg:
                return {
                    "success": False,
                    "error": "🔐 يوتيوب طلب تسجيل دخول\n💡 الحل: حمّل ملف cookies.txt وارفعه على GitHub",
                    "error_code": "COOKIES_REQUIRED"
                }

            if "Private video" in error_msg:
                return {
                    "success": False,
                    "error": "🔒 الفيديو خاص (Private)\n💡 الحل: استخدم رابط فيديو عام",
                    "error_code": "PRIVATE_VIDEO"
                }

            if "Video unavailable" in error_msg:
                return {
                    "success": False,
                    "error": "🚫 الفيديو غير متاح\n💡 ممكن اتحذف أو اتغيرت صلاحياته",
                    "error_code": "VIDEO_UNAVAILABLE"
                }

            if "This video is age-restricted" in error_msg:
                return {
                    "success": False,
                    "error": "🔞 الفيديو مقيد بعمر (Age Restricted)\n💡 الحل: استخدم حساب مسجل الدخول",
                    "error_code": "AGE_RESTRICTED"
                }

            if "Requested format is not available" in error_msg:
                return {
                    "success": False,
                    "error": "📹 الجودة المطلوبة غير متاحة\n💡 الحل: جرب جودة أقل (480p مثلاً)",
                    "error_code": "FORMAT_NOT_AVAILABLE"
                }

            if "rate limit" in error_msg.lower():
                return {
                    "success": False,
                    "error": "⏳ تم تجاوز حد التحميل\n💡 انتظر شوية وحاول تاني",
                    "error_code": "RATE_LIMIT"
                }

            if "cookies" in error_msg.lower():
                return {
                    "success": False,
                    "error": "🍪 مشكلة في ملف الكوكيز\n💡 الحل: جيب كوكيز جديدة وارفعها",
                    "error_code": "COOKIES_ERROR"
                }

            # لو مش من الحالات دي
            return {
                "success": False,
                "error": f"⚠️ خطأ في التحميل: {error_msg[:100]}",
                "error_code": "DOWNLOAD_ERROR"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"⚠️ حدث خطأ: {str(e)[:100]}",
                "error_code": "UNKNOWN_ERROR"
            }

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

        opts = {
            "outtmpl": os.path.join(self.download_path, "%(title)s.%(ext)s"),
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": True,
            "noplaylist": True,
        }

        # كوكيز
        cookies_file = self._get_cookies_file(url)
        if cookies_file and os.path.exists(cookies_file):
            opts["cookiefile"] = cookies_file
        else:
            # لو مفيش كوكيز، ننبه المستخدم
            if url and ("youtube" in url or "facebook" in url):
                print("⚠️ No cookies file found for YouTube/Facebook")

        # تيك توك
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
                "format": fmt,
                "merge_output_format": "mp4",
            })

        return opts

    def _get_cookies_file(self, url):
        """تحديد ملف الكوكيز حسب المنصة"""
        if not url:
            return None

        base_dir = os.path.dirname(__file__)

        if "youtube.com" in url or "youtu.be" in url:
            path = os.path.join(base_dir, "cookies_youtube.txt")
            if os.path.exists(path):
                return path

        if "facebook.com" in url or "fb.watch" in url:
            path = os.path.join(base_dir, "cookies_facebook.txt")
            if os.path.exists(path):
                return path

        if "instagram.com" in url:
            path = os.path.join(base_dir, "cookies_instagram.txt")
            if os.path.exists(path):
                return path

        if "twitter.com" in url or "x.com" in url:
            path = os.path.join(base_dir, "cookies_twitter.txt")
            if os.path.exists(path):
                return path

        default_path = os.path.join(base_dir, "cookies.txt")
        if os.path.exists(default_path):
            return default_path

        return None
