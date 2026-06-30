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

    def _build_opts(self, quality="best", audio=False):

        if audio:
            return {
                "format": "bestaudio/best",
                "outtmpl": f"{self.download_path}/%(title)s.%(ext)s",
                "quiet": True,
                "no_warnings": True,
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
            }

        quality_map = {
            "144": "worst[height<=144]",
            "240": "best[height<=240]",
            "360": "best[height<=360]",
            "480": "best[height<=480]",
            "720": "best[height<=720]",
            "1080": "best[height<=1080]",
        }

        fmt = quality_map.get(str(quality), "best")

        return {
            "format": fmt,
            "merge_output_format": "mp4",
            "outtmpl": f"{self.download_path}/%(title)s.%(ext)s",
            "quiet": True,
            "no_warnings": True,
        }

    async def download(self, url: str, quality="720", audio=False):
        async with self.semaphore:
            self.active += 1
            try:
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    self._download_sync,
                    url,
                    quality,
                    audio
                )
                self.success += 1
                return result

            except Exception as e:
                self.failed += 1
                return {"success": False, "error": str(e)}

            finally:
                self.active -= 1

    def _download_sync(self, url, quality, audio):
        opts = self._build_opts(quality, audio)

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)

            if audio:
                file_path = os.path.splitext(file_path)[0] + ".mp3"

            return {
                "success": True,
                "file_path": file_path,
                "title": info.get("title", "Unknown"),
                "duration": info.get("duration", 0),
                "timestamp": datetime.now().isoformat(),
        }
