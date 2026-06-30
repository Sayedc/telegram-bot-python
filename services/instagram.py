# services/instagram.py
import os
import yt_dlp
from config import DOWNLOADS_PATH


async def download_instagram(url: str, quality: str = "720", audio: bool = False):
    """
    تحميل فيديو أو صورة من انستجرام
    """
    try:
        opts = {
            "outtmpl": f"{DOWNLOADS_PATH}/instagram_%(id)s.%(ext)s",
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": True,
            "format": "best",
        }

        if os.path.exists("cookies.txt"):
            opts["cookiefile"] = "cookies.txt"

        # إضافة impersonate
        opts["impersonate"] = "chrome-120"

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
                "title": info.get("title", "Instagram Content"),
                "duration": info.get("duration", 0),
                "platform": "Instagram",
            }

    except Exception as e:
        return {
            "success": False,
            "error": f"Instagram download failed: {str(e)[:100]}",
        }
