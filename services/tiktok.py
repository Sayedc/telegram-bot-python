# services/tiktok.py
import os
import yt_dlp
from config import DOWNLOADS_PATH


async def download_tiktok(url: str, quality: str = "720", audio: bool = False):
    """
    تحميل فيديو من تيك توك بدون علامة مائية
    """
    try:
        opts = {
            "outtmpl": f"{DOWNLOADS_PATH}/tiktok_%(id)s.%(ext)s",
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": True,
            "extractor_args": {
                "tiktok": {
                    "without_watermark": ["true"],
                }
            },
        }

        # إضافة impersonate عشان يتجاوز الحماية
        opts["impersonate"] = "chrome-120"

        # استخدام الكوكيز لو موجودة
        if os.path.exists("cookies.txt"):
            opts["cookiefile"] = "cookies.txt"

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
            opts["format"] = "best"

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)

            if audio:
                file_path = os.path.splitext(file_path)[0] + ".mp3"

            return {
                "success": True,
                "file_path": file_path,
                "title": info.get("title", "TikTok Video"),
                "duration": info.get("duration", 0),
                "platform": "TikTok",
            }

    except Exception as e:
        return {
            "success": False,
            "error": f"TikTok download failed: {str(e)[:100]}",
        }
