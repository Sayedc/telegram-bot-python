# services/youtube.py
import os
import yt_dlp
from config import DOWNLOADS_PATH


async def download_youtube(url: str, quality: str = "720", audio: bool = False):
    """
    تحميل فيديو من يوتيوب بجودة محددة
    """
    print(f"\n🎬 YouTube download started")
    print(f"URL: {url}")
    print(f"Quality: {quality}")
    print(f"Audio: {audio}")

    quality_map = {
        "144": "worst[height<=144]",
        "240": "best[height<=240]",
        "360": "best[height<=360]",
        "480": "best[height<=480]",
        "720": "best[height<=720]",
        "1080": "best[height<=1080]",
    }

    fmt = quality_map.get(quality, "best[height<=720]")

    try:
        opts = {
            "outtmpl": f"{DOWNLOADS_PATH}/%(title)s.%(ext)s",
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": True,
            "noplaylist": True,
        }

        # تحديد ملف الكوكيز
        cookies_file = None
        if os.path.exists("cookies_youtube.txt"):
            cookies_file = "cookies_youtube.txt"
        elif os.path.exists("cookies.txt"):
            cookies_file = "cookies.txt"

        if cookies_file:
            opts["cookiefile"] = cookies_file
            print(f"🍪 Using cookies: {cookies_file}")
        else:
            print("⚠️ No cookies file found for YouTube")

        if audio:
            opts.update({
                "format": "bestaudio/best",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
            })
            print("🎵 Audio mode: MP3 extraction enabled")
        else:
            opts.update({
                "format": "bv*+ba/b",
                "merge_output_format": "mp4",
            })
            print("🎬 Video mode: format=bv*+ba/b")

        print("⏳ Running yt-dlp for YouTube...")
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            print("✅ YouTube download complete")

            file_path = ydl.prepare_filename(info)
            print(f"📁 File path: {file_path}")

            if audio:
                file_path = os.path.splitext(file_path)[0] + ".mp3"
                print(f"🎵 Audio file path: {file_path}")

            if os.path.exists(file_path):
                print(f"📦 File size: {os.path.getsize(file_path)} bytes")
            else:
                print("❌ File not found after download")

            return {
                "success": True,
                "file_path": file_path,
                "title": info.get("title", "YouTube Video"),
                "duration": info.get("duration", 0),
                "platform": "YouTube",
                "quality": quality,
            }

    except Exception as e:
        print(f"❌ YouTube download failed: {e}")
        return {
            "success": False,
            "error": f"YouTube download failed: {str(e)[:100]}",
            }
