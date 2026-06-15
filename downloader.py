# downloader.py - محرك التحميل المنفصل مع نظام Queue

import os
import asyncio
from datetime import datetime
import yt_dlp


class Downloader:
    def __init__(self, downloads_path, max_concurrent=3):
        self.downloads_path = downloads_path
        self.max_concurrent = max_concurrent
        self.queue = asyncio.Queue()
        self.active_downloads = 0
        self.is_running = False

        self.stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "avg_time": 0,
            "total_time": 0
        }

    async def start(self):
        """بدء تشغيل معالج قائمة الانتظار"""
        self.is_running = True
        asyncio.create_task(self._process_queue())

    async def add_to_queue(self, url, quality, audio, user_id):
        """إضافة طلب إلى قائمة الانتظار"""

        task = {
            "url": url,
            "quality": quality,
            "audio": audio,
            "user_id": user_id,
            "time": datetime.now(),
            "position": self.queue.qsize() + 1
        }

        await self.queue.put(task)
        return task["position"]

    async def _process_queue(self):
        """معالجة قائمة الانتظار"""

        while self.is_running:

            if (
                self.active_downloads < self.max_concurrent
                and not self.queue.empty()
            ):
                task = await self.queue.get()

                self.active_downloads += 1
                self.stats["total"] += 1

                asyncio.create_task(self._download(task))

            await asyncio.sleep(0.1)

    async def _download(self, task):
        """تنفيذ التحميل الفعلي"""

        start_time = datetime.now()

        result = None
        error = None

        try:
            result = await self._download_media(
                task["url"],
                task["quality"],
                task["audio"]
            )

            self.stats["success"] += 1

        except Exception as e:
            error = str(e)
            self.stats["failed"] += 1

        elapsed = (datetime.now() - start_time).total_seconds()

        self.stats["total_time"] += elapsed

        if self.stats["total"] > 0:
            self.stats["avg_time"] = (
                self.stats["total_time"] / self.stats["total"]
            )

        self.active_downloads -= 1

        if error:
            raise Exception(error)

        return result

    async def _download_media(self, url, quality, audio):
        """تحميل الوسائط"""

        if audio:

            opts = {
                "outtmpl": f"{self.downloads_path}/%(title)s.%(ext)s",
                "quiet": True,
                "no_warnings": True,
                "format": "bestaudio/best",
                "extractor_retries": 5,
                "retries": 5,
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }
                ],
            }

        else:

            fmt = (
                f"bestvideo[height<={quality}]"
                f"+bestaudio/"
                f"best[height<={quality}]"
                f"/best"
            )

            opts = {
                "outtmpl": f"{self.downloads_path}/%(title)s.%(ext)s",
                "quiet": True,
                "no_warnings": True,
                "format": fmt,
                "merge_output_format": "mp4",
                "extractor_retries": 5,
                "retries": 5,
            }

        with yt_dlp.YoutubeDL(opts) as ydl:

            info = ydl.extract_info(url, download=True)

            path = ydl.prepare_filename(info)

            if audio:
                path = os.path.splitext(path)[0] + ".mp3"

            return path, info.get("title", "Media")

    def get_stats(self):
        """إحصائيات الأداء"""

        return {
            "total": self.stats["total"],
            "success": self.stats["success"],
            "failed": self.stats["failed"],
            "avg_time": round(self.stats["avg_time"], 2),
            "queue_size": self.queue.qsize(),
            "active": self.active_downloads
        }

    def get_queue_position(self, user_id):
        """معرفة ترتيب المستخدم في قائمة الانتظار"""

        positions = [
            i
            for i, t in enumerate(self.queue._queue)
            if t.get("user_id") == user_id
        ]

        return positions[0] + 1 if positions else 0

    async def stop(self):
        """إيقاف المعالج"""
        self.is_running = False
