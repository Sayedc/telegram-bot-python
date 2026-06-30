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
                return {"success": False, "error": "⚠️ التحميل استغرق وقتاً طويلاً"}

            except Exception as e:
                self.failed += 1
                return {"success": False, "error": str(e)}

            finally:
                self.active -= 1

    def _download_sync(self, url, quality, audio):
        opts = self._build_opts(quality, audio, url)

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)

                if info is None:
                    return {"success": False, "error": "⚠️ الرابط غير صحيح"}

                file_path = ydl.prepare_filename(info)

                if audio:
                    file_path = os.path.splitext(file_path)[0] + ".mp3"

                if not os.path.exists(file_path):
                    return {"success": False, "error": "⚠️ الملف لم يتم تحميله"}

                return {
                    "success": True,
                    "file_path": file_path,
                    "title": info.get("title", "Unknown"),
                    "duration": info.get("duration", 0),
                }

        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e)
            if "Sign in to confirm" in error_msg:
                return {"success": False, "error": "⚠️ يوتيوب طلب تسجيل دخول\n💡 حمّل ملف cookies.txt"}
            return {"success": False, "error": f"⚠️ خطأ: {error_msg[:100]}"}

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

        opts = {
            "outtmpl": os.path.join(self.download_path, "%(title)s.%(ext)s"),
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": True,
            "noplaylist": True,
        }

        # مسار الكوكيز المضمون
        cookies_path = os.path.join(os.path.dirname(__file__), "cookies.txt")
        if os.path.exists(cookies_path):
            opts["cookiefile"] = cookies_path
        else:
            print("⚠️ ملف cookies.txt غير موجود")

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
