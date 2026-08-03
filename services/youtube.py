# services/youtube.py - النسخة النهائية (مع هيدرز وكوكيز)

import os
import glob
import yt_dlp
from config import DOWNLOADS_PATH


COOKIES_FILES = [
    "cookies_youtube.txt",
    "/app/cookies_youtube.txt",
    "cookies.txt",
    "/app/cookies.txt",
]


def _get_cookie_file():
    for path in COOKIES_FILES:
        if os.path.exists(path):
            return path
    return None


def _video_format(quality: str):
    return f"best[height<={quality}]"


def _audio_options():
    return {
        "format": "bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    }


def _video_options(quality):
    return {
        "format": _video_format(quality),
        "merge_output_format": "mp4",
    }


def _base_options():
    opts = {
        "outtmpl": os.path.join(
            DOWNLOADS_PATH,
            "%(title).150s.%(ext)s"
        ),
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": False,
        "noplaylist": True,
        "retries": 10,
        "fragment_retries": 10,
        "socket_timeout": 30,
        "nocheckcertificate": True,
        "geo_bypass": True,
        "geo_bypass_country": "US",
        "concurrent_fragment_downloads": 4,
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-us,en;q=0.5",
            "Sec-Fetch-Mode": "navigate",
        },
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web"],
                "skip": ["dash", "hls"],
            }
        },
    }

    cookie = _get_cookie_file()
    if cookie:
        opts["cookiefile"] = cookie
        print(f"🍪 Using cookies: {cookie}")
    else:
        print("⚠️ No cookies file found - might cause issues")

    return opts


def _find_downloaded_file(path):
    if os.path.exists(path):
        return path

    base = os.path.splitext(path)[0]

    exts = [
        ".mp4",
        ".mkv",
        ".webm",
        ".mov",
        ".m4a",
        ".mp3",
    ]

    for ext in exts:
        candidate = base + ext
        if os.path.exists(candidate):
            return candidate

    files = glob.glob(base + ".*")
    if files:
        return files[0]

    return None


async def download_youtube(
    url: str,
    quality: str = "720",
    audio: bool = False,
):
    """
    Professional YouTube Downloader
    """

    os.makedirs(DOWNLOADS_PATH, exist_ok=True)

    opts = _base_options()

    if audio:
        opts.update(_audio_options())
    else:
        opts.update(_video_options(quality))

    # قائمة واسعة من الصيغ للمحاولة
    formats = [
        opts["format"],
        "best[height<=720]",
        "best[height<=480]",
        "best[height<=360]",
        "bestvideo+bestaudio",
        "best",
        "18",
        "22",
    ]

    last_error = None

    for fmt in formats:
        try:
            current = opts.copy()
            current["format"] = fmt

            with yt_dlp.YoutubeDL(current) as ydl:
                print(f"⏳ Running yt-dlp with format: {fmt}")
                info = ydl.extract_info(url, download=True)

                if not info:
                    raise Exception("Unable to fetch video information.")

                file_path = ydl.prepare_filename(info)

                if audio:
                    file_path = os.path.splitext(file_path)[0] + ".mp3"

                file_path = _find_downloaded_file(file_path)

                if not file_path:
                    raise FileNotFoundError("Downloaded file not found.")

                print(f"✅ Success with format: {fmt}")
                return {
                    "success": True,
                    "file_path": file_path,
                    "title": info.get("title", "YouTube Video"),
                    "duration": info.get("duration", 0),
                    "platform": "YouTube",
                    "quality": quality,
                    "uploader": info.get("uploader", ""),
                    "thumbnail": info.get("thumbnail", ""),
                    "view_count": info.get("view_count", 0),
                }

        except Exception as e:
            print(f"❌ yt-dlp DOWNLOAD ERROR with format {fmt}: {e}")
            last_error = str(e)
            continue

    return {
        "success": False,
        "error": last_error or "Unknown YouTube error.",
    }
