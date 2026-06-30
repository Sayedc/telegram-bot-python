# services/youtube.py
import os
import yt_dlp
from config import DOWNLOADS_PATH, COOKIES_FILE


async def download_youtube(url: str, quality: str = "720", audio: bool = False):
    """
    تحميل فيديو من يوتيوب بجودة محددة
    """
    quality_map = {
        "144": "worst[height<=144]",
        "240": "best[height<=240]",
        "360": "best[height<=360]",
        "480": "best[height<=480]",
        "720": "best[height<=720]",
        "1080": "best[height<=1080]",
    }

    # تحديد الصيغة المطلوبة
    fmt = quality_map.get(quality, "best[height<=720]")

    try:
        opts = {
            "outtmpl": f"{DOWNLOADS_PATH}/%(title)s.%(ext)s",
            "quiet": True,
            "no_warnings": True,
            "cookiefile": COOKIES_FILE if os.path.exists(COOKIES_FILE) else None,
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

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)

            if audio:
                file_path = os.path.splitext(file_path)[0] + ".mp3"

            return {
                "success": True,
                "file_path": file_path,
                "title": info.get("title", "YouTube Video"),
                "duration": info.get("duration", 0),
                "platform": "YouTube",
                "quality": quality,
            }

    except Exception as e:
        # محاولة بديلة بأفضل جودة متاحة
        try:
            opts = {
                "outtmpl": f"{DOWNLOADS_PATH}/%(title)s.%(ext)s",
                "quiet": True,
                "no_warnings": True,
                "format": "best",
                "merge_output_format": "mp4",
                "cookiefile": COOKIES_FILE if os.path.exists(COOKIES_FILE) else None,
            }

            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info)

                return {
                    "success": True,
                    "file_path": file_path,
                    "title": info.get("title", "YouTube Video"),
                    "duration": info.get("duration", 0),
                    "platform": "YouTube",
                    "quality": "best",
                }

        except Exception as e2:
            return {
                "success": False,
                "error": f"YouTube download failed: {str(e2)[:100]}",
            }
