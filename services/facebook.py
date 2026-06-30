# services/facebook.py
import os
import yt_dlp
from config import DOWNLOADS_PATH, COOKIES_FILE


async def download_facebook(url: str, quality: str = "720", audio: bool = False):
    """
    تحميل فيديو من فيسبوك
    """
    try:
        opts = {
            "outtmpl": f"{DOWNLOADS_PATH}/facebook_%(id)s.%(ext)s",
            "quiet": True,
            "no_warnings": True,
            "format": "best",
            "cookiefile": COOKIES_FILE if os.path.exists(COOKIES_FILE) else None,
        }

        if audio:
            opts.update({
                "format": "bestaudio/best",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                }],
            })

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)

            if audio:
                file_path = os.path.splitext(file_path)[0] + ".mp3"

            return {
                "success": True,
                "file_path": file_path,
                "title": info.get("title", "Facebook Video"),
                "duration": info.get("duration", 0),
                "platform": "Facebook",
            }

    except Exception as e:
        return {
            "success": False,
            "error": f"Facebook download failed: {str(e)[:100]}",
        }
