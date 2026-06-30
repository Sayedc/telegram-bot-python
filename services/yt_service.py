# services/yt_service.py
import os
import yt_dlp
from config import DOWNLOADS_PATH, COOKIES_FILE


async def get_audio_only(url: str):
    """
    استخراج الصوت فقط من فيديو يوتيوب
    """
    try:
        opts = {
            "outtmpl": f"{DOWNLOADS_PATH}/%(title)s.%(ext)s",
            "quiet": True,
            "no_warnings": True,
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
            "cookiefile": COOKIES_FILE if os.path.exists(COOKIES_FILE) else None,
        }

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            file_path = os.path.splitext(file_path)[0] + ".mp3"

            return {
                "success": True,
                "file_path": file_path,
                "title": info.get("title", "Audio"),
                "duration": info.get("duration", 0),
                "platform": "YouTube (Audio)",
            }

    except Exception as e:
        return {
            "success": False,
            "error": f"Audio extraction failed: {str(e)[:100]}",
        }


async def get_video_info(url: str):
    """
    جلب معلومات الفيديو بدون تحميل
    """
    try:
        opts = {
            "quiet": True,
            "no_warnings": True,
        }

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)

            return {
                "success": True,
                "title": info.get("title", "Unknown"),
                "duration": info.get("duration", 0),
                "uploader": info.get("uploader", "Unknown"),
                "views": info.get("view_count", 0),
                "likes": info.get("like_count", 0),
                "thumbnail": info.get("thumbnail", ""),
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
          }
