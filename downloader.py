# downloader.py - محرك التحميل المنفصل
import asyncio
import os
from datetime import datetime
import yt_dlp

class Downloader:
    def __init__(self, downloads_path):
        self.downloads_path = downloads_path
        self.queue = asyncio.Queue()
        self.active_downloads = 0
        self.max_concurrent = 3
        self.stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "avg_time": 0
        }
    
    async def add_to_queue(self, url, quality, audio, user_id):
        """إضافة طلب إلى قائمة الانتظار"""
        await self.queue.put({
            "url": url,
            "quality": quality,
            "audio": audio,
            "user_id": user_id,
            "time": datetime.now()
        })
        return len(self.queue._queue)
    
    async def process_queue(self):
        """معالجة قائمة الانتظار"""
        while True:
            if self.active_downloads < self.max_concurrent and not self.queue.empty():
                task = await self.queue.get()
                self.active_downloads += 1
                asyncio.create_task(self.download(task))
            await asyncio.sleep(0.1)
    
    async def download(self, task):
        """تنفيذ التحميل الفعلي"""
        start = datetime.now()
        try:
            result = await self._download_media(task["url"], task["quality"], task["audio"])
            self.stats["success"] += 1
            return result
        except Exception as e:
            self.stats["failed"] += 1
            raise e
        finally:
            self.active_downloads -= 1
            elapsed = (datetime.now() - start).total_seconds()
            self.stats["avg_time"] = (self.stats["avg_time"] + elapsed) / 2
    
    async def _download_media(self, url, quality, audio):
        """التحميل الفعلي (زي ما هو موجود في main.py)"""
        # نفس كود download_media القديم
        pass
    
    def get_stats(self):
        """إحصائيات الأداء"""
        queue_size = len(self.queue._queue)
        return {
            **self.stats,
            "queue_size": queue_size,
            "active": self.active_downloads
        }
