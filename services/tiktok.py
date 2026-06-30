# services/tiktok.py
import os
import yt_dlp
from config import DOWNLOADS_PATH, COOKIES_FILE


async def download_tiktok(url: str, quality: str = "720", audio: bool = False):
    """
    تحميل فيديو من تيك توك بدون علامة مائية
    """
    try:
        opts = {
            "outtmpl": f"{DOWNLOADS_PATH}/tiktok_%(id)s.%(ext)s",
            "quiet": True,
            "no_warnings": True,
            "extractor_args": {
                "tiktok": {
                    "without_watermark": ["true"],
                }
            },
            "cookiefile": COOKIES_FILE if os.path.exists(COOKIES_FILE) else None,
        }

        # إذا كان طلب صوت فقط
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
            # تحميل الفيديو
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
        # محاولة بديلة بدون علامة مائية
        try:
            opts = {
                "outtmpl": f"{DOWNLOADS_PATH}/tiktok_%(id)s.%(ext)s",
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
                    "title": info.get("title", "TikTok Video"),
                    "duration": info.get("duration", 0),
                    "platform": "TikTok",
                }

        except Exception as e2:
            return {
                "success": False,
                "error": f"TikTok download failed: {str(e2)[:100]}",
            }
