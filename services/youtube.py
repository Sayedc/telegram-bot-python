# services/youtube.py
# YouTube Downloader - Railway Ready
#
# Supports:
# - cookies_youtube.txt
# - cookies.txt
# - YOUTUBE_COOKIES environment variable
# - optional PROXY
# - YouTube client fallback
# - MP4 / MP3
# - Railway / Docker


import os
import glob
import tempfile

import yt_dlp

from config import DOWNLOADS_PATH


# =========================================================
# Configuration
# =========================================================

COOKIES_FILES = [
    "/app/cookies_youtube.txt",
    "cookies_youtube.txt",
    "/app/cookies.txt",
    "cookies.txt",
]

COOKIE_ENV_NAME = "YOUTUBE_COOKIES"


# =========================================================
# Cookies
# =========================================================

def _create_cookie_file_from_env():
    """
    Create a temporary Netscape cookies file from
    the YOUTUBE_COOKIES environment variable.

    IMPORTANT:
    Never print the cookie content to logs.
    """

    cookies = os.getenv(COOKIE_ENV_NAME)

    if not cookies:
        return None

    cookies = cookies.strip()

    if not cookies:
        return None

    try:
        # Basic validation
        if (
            "# Netscape HTTP Cookie File" not in cookies
            and "# HTTP Cookie File" not in cookies
        ):
            print(
                "⚠️ YOUTUBE_COOKIES exists but does not "
                "look like a Netscape cookies file"
            )

        cookie_path = os.path.join(
            tempfile.gettempdir(),
            "youtube_cookies.txt"
        )

        with open(
            cookie_path,
            "w",
            encoding="utf-8",
            newline="\n",
        ) as f:
            f.write(cookies)

        print(
            "🍪 YouTube cookies loaded from "
            "YOUTUBE_COOKIES environment variable"
        )

        return cookie_path

    except Exception as e:
        print(
            f"❌ Failed to create cookies file: {e}"
        )

        return None


def _get_cookie_file():
    """
    Search for YouTube cookies.

    Priority:
    1. YOUTUBE_COOKIES environment variable
    2. cookies_youtube.txt
    3. cookies.txt
    """

    # -----------------------------------------------------
    # Environment variable
    # -----------------------------------------------------

    env_cookie_file = _create_cookie_file_from_env()

    if env_cookie_file and os.path.exists(
        env_cookie_file
    ):
        return env_cookie_file

    # -----------------------------------------------------
    # Local files
    # -----------------------------------------------------

    for path in COOKIES_FILES:

        if os.path.isfile(path):

            try:

                size = os.path.getsize(path)

                if size <= 0:
                    continue

                print(
                    f"🍪 Found YouTube cookies: {path}"
                )

                return path

            except Exception:
                continue

    print(
        "⚠️ No YouTube cookies file found"
    )

    return None


# =========================================================
# Formats
# =========================================================

def _video_format(quality: str):

    return (
        f"bestvideo[height<={quality}]"
        f"+bestaudio/"
        f"best[height<={quality}]/"
        f"bestvideo+bestaudio/"
        f"best"
    )


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


# =========================================================
# Base yt-dlp options
# =========================================================

def _base_options():

    opts = {

        # -------------------------------------------------
        # Output
        # -------------------------------------------------

        "outtmpl": os.path.join(
            DOWNLOADS_PATH,
            "%(title).150s.%(ext)s"
        ),

        # -------------------------------------------------
        # General
        # -------------------------------------------------

        "quiet": True,
        "no_warnings": False,

        "ignoreerrors": False,

        "noplaylist": True,

        # -------------------------------------------------
        # Retry
        # -------------------------------------------------

        "retries": 10,
        "fragment_retries": 10,
        "extractor_retries": 5,

        # -------------------------------------------------
        # Network
        # -------------------------------------------------

        "socket_timeout": 30,

        "nocheckcertificate": True,

        "geo_bypass": True,
        "geo_bypass_country": "US",

        "concurrent_fragment_downloads": 4,

        # -------------------------------------------------
        # Extraction
        # -------------------------------------------------

        "extract_flat": False,

        # Do not force live_from_start for normal videos.
        # It can cause unnecessary behavior on some videos.
        "live_from_start": False,

        # -------------------------------------------------
        # Format sorting
        # -------------------------------------------------

        "format_sort": [
            "res",
            "codec:h264",
            "ext:mp4",
        ],

        # -------------------------------------------------
        # Browser-like headers
        # -------------------------------------------------

        "http_headers": {

            "User-Agent":
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/140.0.0.0 "
                "Safari/537.36",

            "Accept":
                "text/html,"
                "application/xhtml+xml,"
                "application/xml;q=0.9,"
                "image/avif,"
                "image/webp,"
                "*/*;q=0.8",

            "Accept-Language":
                "en-US,en;q=0.9",

        },

        # -------------------------------------------------
        # YouTube clients
        #
        # We intentionally don't force only one client.
        # yt-dlp can choose available formats/clients.
        # -------------------------------------------------

        "extractor_args": {
            "youtube": {
                "player_client": [
                    "android_vr",
                    "tv",
                    "ios",
                    "web_safari",
                ],
                "player_skip": [],
            }
        },

        # -------------------------------------------------
        # Cache
        # -------------------------------------------------

        "cachedir": os.path.join(
            DOWNLOADS_PATH,
            ".yt-dlp-cache"
        ),

    }

    # =====================================================
    # Optional Proxy
    # =====================================================

    proxy = os.getenv("PROXY")

    if proxy:

        proxy = proxy.strip()

        if proxy:

            opts["proxy"] = proxy

            print(
                "🌐 YouTube proxy enabled"
            )

    # =====================================================
    # Cookies
    # =====================================================

    cookie = _get_cookie_file()

    if cookie:

        opts["cookiefile"] = cookie

        print(
            "🍪 YouTube authentication cookies enabled"
        )

    return opts


# =========================================================
# Find downloaded file
# =========================================================

def _find_downloaded_file(path):

    if not path:
        return None

    if os.path.exists(path):
        return path

    base = os.path.splitext(path)[0]

    extensions = [
        ".mp4",
        ".mkv",
        ".webm",
        ".mov",
        ".m4a",
        ".mp3",
    ]

    for ext in extensions:

        candidate = base + ext

        if os.path.exists(candidate):
            return candidate

    files = glob.glob(
        base + ".*"
    )

    if files:
        return files[0]

    return None


# =========================================================
# Detect YouTube bot/auth errors
# =========================================================

def _is_youtube_bot_error(error_text: str):

    if not error_text:
        return False

    error_text = error_text.lower()

    patterns = [
        "sign in to confirm you're not a bot",
        "sign in to confirm you’re not a bot",
        "confirm you're not a bot",
        "confirm you’re not a bot",
        "use --cookies-from-browser",
        "use --cookies",
    ]

    return any(
        pattern in error_text
        for pattern in patterns
    )


# =========================================================
# Friendly error
# =========================================================

def _friendly_youtube_error(error_text: str):

    if _is_youtube_bot_error(error_text):

        return (
            "⚠️ YouTube رفض الطلب مؤقتًا لأنه اعتبر "
            "السيرفر طلبًا آليًا.\n\n"
            "🍪 يلزم إعداد YouTube Cookies صحيحة "
            "للسيرفر أو استخدام إعداد PO Token عند الحاجة."
        )

    return error_text


# =========================================================
# Main YouTube Downloader
# =========================================================

async def download_youtube(
    url: str,
    quality: str = "720",
    audio: bool = False,
):

    """
    Professional YouTube Downloader.

    Supports:
    - Video
    - Audio
    - Cookies
    - Proxy
    - Railway
    - Docker
    """

    os.makedirs(
        DOWNLOADS_PATH,
        exist_ok=True
    )

    # -----------------------------------------------------
    # Base options
    # -----------------------------------------------------

    opts = _base_options()

    # -----------------------------------------------------
    # Audio / Video
    # -----------------------------------------------------

    if audio:

        opts.update(
            _audio_options()
        )

    else:

        opts.update(
            _video_options(quality)
        )

    # -----------------------------------------------------
    # Download
    # -----------------------------------------------------

    try:

        print(
            "▶️ Starting YouTube download"
        )

        print(
            f"🎥 Quality: {quality}p"
        )

        print(
            f"🎵 Audio mode: {audio}"
        )

        print(
            f"⏳ Format: {opts['format']}"
        )

        with yt_dlp.YoutubeDL(
            opts
        ) as ydl:

            info = ydl.extract_info(
                url,
                download=True
            )

            if not info:

                raise Exception(
                    "Unable to fetch video information."
                )

            # -------------------------------------------------
            # Prepare file
            # -------------------------------------------------

            file_path = ydl.prepare_filename(
                info
            )

            if audio:

                file_path = (
                    os.path.splitext(
                        file_path
                    )[0]
                    + ".mp3"
                )

            file_path = _find_downloaded_file(
                file_path
            )

            if not file_path:

                raise FileNotFoundError(
                    "Downloaded file not found."
                )

            # -------------------------------------------------
            # File size
            # -------------------------------------------------

            try:

                file_size_mb = (
                    os.path.getsize(
                        file_path
                    )
                    / (1024 * 1024)
                )

            except Exception:

                file_size_mb = 0

            print(
                "✅ YouTube download completed"
            )

            print(
                f"📦 File size: "
                f"{file_size_mb:.2f} MB"
            )

            # -------------------------------------------------
            # Result
            # -------------------------------------------------

            return {

                "success": True,

                "file_path": file_path,

                "title": info.get(
                    "title",
                    "YouTube Video"
                ),

                "duration": info.get(
                    "duration",
                    0
                ),

                "platform": "YouTube",

                "quality": quality,

                "uploader": info.get(
                    "uploader",
                    ""
                ),

                "thumbnail": info.get(
                    "thumbnail",
                    ""
                ),

                "view_count": info.get(
                    "view_count",
                    0
                ),

                "file_size_mb":
                    file_size_mb,

            }

    except Exception as e:

        error_text = str(e)

        print(
            "❌ yt-dlp DOWNLOAD ERROR:"
        )

        print(
            error_text
        )

        # -----------------------------------------------------
        # Bot detection
        # -----------------------------------------------------

        friendly_error = (
            _friendly_youtube_error(
                error_text
            )
        )

        return {

            "success": False,

            "error": friendly_error,

}
