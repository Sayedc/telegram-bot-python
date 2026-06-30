import os
import asyncio
from datetime import datetime

import yt_dlp

from config import DOWNLOADS_PATH, MAX_CONCURRENT_DOWNLOADS


class Downloader:
    def __init__(self, download_path=DOWNLOADS_PATH, max_concurrent=MAX_CONCURRENT_DOWNLOADS):
        self.download_path = download_path
        self.semaphore = asyncio.Semaphore(max_concurrent)

        self.active = 0
        self.success = 0
        self.failed = 0

        os.makedirs(self.download_path, exist_ok=True)

    async def start(self):
        print("✅ Downloader Started")

    def get_stats(self):
        return {
            "queue_size": 0,
            "active": self.active,
            "success": self.success,
            "failed": self.failed,
        }

    def _build_opts(self, quality="720", audio=False):
        if audio:
            return {
                "format": "bestaudio/best",
                "outtmpl": os.path.join(self.download_path, "%(title)s.%(ext)s"),
                "quiet": True,
                "noplaylist": True,
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
            }

        quality_map = {
            "144": "best[height<=144]",
            "240": "best[height<=240]",
            "360": "best[height<=360]",
            "480": "best[height<=480]",
            "720": "best[height<=720]",
            "1080": "best[height<=1080]",
        }

        return {
            "format": quality_map.get(str(quality), "best"),
            "merge_output_format": "mp4",
            "outtmpl": os.path.join(self.download_path, "%(title)s.%(ext)s"),
            "quiet": True,
            "noplaylist": True,
        }

    async def download(self, url, quality="720", audio=False):
        async with self.semaphore:
            self.active += 1

            try:
                loop = asyncio.get_running_loop()

                result = await loop.run_in_executor(
                    None,
                    self._download_sync,
                    url,
                    quality,
                    audio,
                )

                if result["success"]:
                    self.success += 1
                else:
                    self.failed += 1

                return result

            finally:
                self.active -= 1

    async def download_url(self, url, quality="720", audio=False):
        return await self.download(url, quality, audio)

    def _download_sync(self, url, quality, audio):
        try:
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

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }


downloader = Downloader()
