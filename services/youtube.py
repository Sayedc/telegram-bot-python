# services/youtube.py

import os
import yt_dlp
from config import DOWNLOADS_PATH


async def download_youtube(url: str, quality: str = "720", audio: bool = False):
    """
    Download YouTube video or audio using yt-dlp
    """

    print("\n==============================")
    print("🎬 YouTube Download Started")
    print(f"URL: {url}")
    print(f"Quality: {quality}")
    print(f"Audio Mode: {audio}")
    print("==============================")

    try:
        os.makedirs(DOWNLOADS_PATH, exist_ok=True)

        opts = {
            "outtmpl": f"{DOWNLOADS_PATH}/%(title).150s.%(ext)s",
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": False,
            "noplaylist": True,

            # تحسين الاستقرار
            "retries": 10,
            "fragment_retries": 10,
            "socket_timeout": 30,

            # إصلاح مشاكل YouTube الحديثة
            "extractor_args": {
                "youtube": {
                    "player_client": ["android", "web"]
                }
            }
        }

        # ===========================
        # Cookies
        # ===========================

        cookies_file = None

        if os.path.exists("cookies_youtube.txt"):
            cookies_file = "cookies_youtube.txt"

        elif os.path.exists("/app/cookies_youtube.txt"):
            cookies_file = "/app/cookies_youtube.txt"

        elif os.path.exists("cookies.txt"):
            cookies_file = "cookies.txt"

        if cookies_file:
            opts["cookiefile"] = cookies_file
            print(f"🍪 Using cookies: {cookies_file}")
        else:
            print("⚠️ No cookies file found")

        # ===========================
        # Audio
        # ===========================

        if audio:

            opts.update({
                "format": "bestaudio/best",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
            })

            print("🎵 Audio Mode Enabled")

        # ===========================
        # Video
        # ===========================

        else:

            video_format = (
                f"bestvideo*[height<={quality}]"
                f"+bestaudio/"
                f"best[height<={quality}]"
                f"/best"
            )

            opts.update({
                "format": video_format,
                "merge_output_format": "mp4",
            })

            print(f"🎬 Video Format: {video_format}")

        # ===========================
        # Download
        # ===========================

        print("⏳ Running yt-dlp...")

        with yt_dlp.YoutubeDL(opts) as ydl:

            info = ydl.extract_info(url, download=True)

            if info is None:
                raise Exception("Failed to fetch video information.")

            file_path = ydl.prepare_filename(info)

            if audio:
                file_path = os.path.splitext(file_path)[0] + ".mp3"

            if not os.path.exists(file_path):

                # البحث عن الملف النهائي إذا تغير الامتداد
                base = os.path.splitext(file_path)[0]

                for ext in [
                    ".mp4",
                    ".mkv",
                    ".webm",
                    ".mp3",
                    ".m4a"
                ]:
                    candidate = base + ext
                    if os.path.exists(candidate):
                        file_path = candidate
                        break

            if not os.path.exists(file_path):
                raise Exception("Downloaded file not found.")

            print("✅ Download Success")
            print(f"📁 {file_path}")

            return {
                "success": True,
                "file_path": file_path,
                "title": info.get("title", "YouTube Video"),
                "duration": info.get("duration", 0),
                "platform": "YouTube",
                "quality": quality,
            }

    except Exception as e:

        print(f"❌ Download Error: {e}")

        return {
            "success": False,
            "error": str(e),
            }
