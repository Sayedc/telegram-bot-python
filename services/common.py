# services/common.py
"""
Shared helpers for every yt-dlp based downloader.

Why this exists:
* Every request gets its OWN work directory, so two users downloading the
  same video (or videos with the same title) can never overwrite / delete
  each other's files.
* yt-dlp is blocking, so it is always executed in a worker thread
  (asyncio.to_thread) - otherwise the whole bot freezes during a download.
* Cookies are looked up in one place (env var or file, case-insensitive,
  tolerant of names like "cookies_youtube.txt.txt") and copied per request.
* yt-dlp errors are translated into short Arabic messages + an error code.
"""

import asyncio
import os
import re
import shutil
import tempfile
import time

import yt_dlp

from config import BASE_DIR, DOWNLOADS_PATH, MAX_VIDEO_SIZE
from utils.texts import DOWNLOAD_ERRORS

ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")

# Files that yt-dlp leaves next to the real media and that must never be sent.
JUNK_EXTENSIONS = {
    ".part", ".ytdl", ".json", ".jpg", ".jpeg", ".png", ".webp",
    ".txt", ".vtt", ".srt", ".description", ".temp",
}

DOWNLOAD_TIMEOUT = int(os.getenv("DOWNLOAD_TIMEOUT", "900"))


# =========================================================
# Small utilities
# =========================================================

def clean_error(text, limit=500):
    """Strip ANSI colours and the 'ERROR:' prefix from yt-dlp messages."""
    text = ANSI_RE.sub("", str(text or "")).strip()
    text = re.sub(r"^ERROR:\s*", "", text)
    return text[:limit]


def new_workdir(prefix="dl_"):
    os.makedirs(DOWNLOADS_PATH, exist_ok=True)
    return tempfile.mkdtemp(prefix=prefix, dir=DOWNLOADS_PATH)


def remove_path(path):
    """Delete a file or a whole directory, never raising."""
    if not path:
        return
    try:
        if os.path.isdir(path):
            shutil.rmtree(path, ignore_errors=True)
        elif os.path.exists(path):
            os.remove(path)
    except OSError:
        pass


def cleanup_stale(root=None, max_age=3600):
    """Remove entries in the downloads folder older than max_age seconds."""
    root = root or DOWNLOADS_PATH
    removed = 0
    now = time.time()
    try:
        names = os.listdir(root)
    except OSError:
        return 0
    for name in names:
        path = os.path.join(root, name)
        try:
            if now - os.path.getmtime(path) >= max_age:
                remove_path(path)
                removed += 1
        except OSError:
            continue
    return removed


def find_output_file(workdir, prefer_ext=None):
    """Return the real media file inside workdir (largest non-junk file)."""
    candidates = []
    for root, _dirs, files in os.walk(workdir):
        for name in files:
            ext = os.path.splitext(name)[1].lower()
            if ext in JUNK_EXTENSIONS:
                continue
            path = os.path.join(root, name)
            try:
                size = os.path.getsize(path)
            except OSError:
                continue
            if size > 0:
                candidates.append((path, size, ext))

    if not candidates:
        return None

    if prefer_ext:
        preferred = [c for c in candidates if c[2] == prefer_ext]
        if preferred:
            candidates = preferred

    return max(candidates, key=lambda c: c[1])[0]


# =========================================================
# Cookies
# =========================================================

_COOKIE_FILENAMES = {
    "youtube": [
        "cookies_youtube.txt", "cookies_youtube.txt.txt",
        "youtube_cookies.txt", "youtube.txt",
    ],
    "facebook": [
        "cookies_facebook.txt", "cookies_facebook.txt.txt",
        "facebook_cookies.txt", "facebook.txt",
    ],
    "instagram": [
        "cookies_instagram.txt", "instagram_cookies.txt", "instagram.txt",
    ],
    "tiktok": [
        "cookies_tiktok.txt", "tiktok_cookies.txt", "tiktok.txt",
    ],
}
_GENERIC_COOKIE_FILENAMES = ["cookies.txt"]
_NETSCAPE_HEADERS = ("# Netscape HTTP Cookie File", "# HTTP Cookie File")


def _cookie_search_dirs():
    dirs = []
    for d in (BASE_DIR, os.getcwd(), "/app", "/data"):
        if d and d not in dirs and os.path.isdir(d):
            dirs.append(d)
    return dirs


def _find_cookie_source(platform):
    """
    Priority:
      1. <PLATFORM>_COOKIES env var (full cookies.txt content)
      2. <PLATFORM>_COOKIES_FILE env var (path)
      3. cookie files next to the bot (case-insensitive name match)
    """
    key = platform.upper()

    content = os.getenv(f"{key}_COOKIES", "").strip()
    if content:
        return "env", content

    explicit = os.getenv(f"{key}_COOKIES_FILE", "").strip()
    if explicit and os.path.isfile(explicit):
        return "file", explicit

    wanted = [n.lower() for n in _COOKIE_FILENAMES.get(platform.lower(), [])]
    wanted += _GENERIC_COOKIE_FILENAMES

    listings = []
    for d in _cookie_search_dirs():
        try:
            listings.append((d, {n.lower(): n for n in os.listdir(d)}))
        except OSError:
            continue

    for name in wanted:
        for d, listing in listings:
            real = listing.get(name)
            if not real:
                continue
            path = os.path.join(d, real)
            try:
                if os.path.isfile(path) and os.path.getsize(path) > 0:
                    return "file", path
            except OSError:
                continue

    return None


def prepare_cookies(platform, workdir):
    """
    Copy the platform cookies into workdir/cookies.txt and return its path.

    A private copy per request avoids concurrent downloads racing on the same
    file (yt-dlp rewrites the cookie file when it finishes) and fixes CRLF line
    endings / a missing Netscape header. Cookie contents are never printed.
    """
    source = _find_cookie_source(platform)
    if not source:
        return None

    kind, value = source
    try:
        if kind == "env":
            text = value
            if "\n" not in text and "\\n" in text:
                text = text.replace("\\n", "\n")
        else:
            with open(value, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()

        text = text.replace("\r\n", "\n").replace("\r", "\n").strip()
        if not text.startswith(_NETSCAPE_HEADERS):
            text = "# Netscape HTTP Cookie File\n" + text

        dest = os.path.join(workdir, "cookies.txt")
        with open(dest, "w", encoding="utf-8", newline="\n") as f:
            f.write(text + "\n")
        return dest

    except OSError as exc:
        print(f"⚠️ Could not prepare {platform} cookies: {exc}", flush=True)
        return None


# =========================================================
# yt-dlp options
# =========================================================

def js_runtimes():
    """
    YouTube needs a JavaScript runtime to solve its challenges. yt-dlp only
    enables Deno by default - Node/Bun must be switched on explicitly, which
    is why installing Node in the Dockerfile alone was not enough.
    """
    return {name: {} for name in ("deno", "node", "bun") if shutil.which(name)}


def base_options(workdir):
    opts = {
        "outtmpl": os.path.join(workdir, "%(id).100B.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "noplaylist": True,
        "playlist_items": "1",
        "restrictfilenames": True,
        "overwrites": True,
        "retries": 5,
        "fragment_retries": 5,
        "extractor_retries": 3,
        "socket_timeout": 30,
        "concurrent_fragment_downloads": 4,
        "max_filesize": MAX_VIDEO_SIZE,
        "match_filter": yt_dlp.utils.match_filter_func("!is_live"),
        "cachedir": os.path.join(tempfile.gettempdir(), "yt-dlp-cache"),
        "js_runtimes": js_runtimes(),
    }

    proxy = os.getenv("PROXY", "").strip()
    if proxy:
        opts["proxy"] = proxy

    return opts


def video_selection(quality):
    """
    Sorting by res:<N> uses the SHORTER side of the video, so vertical videos
    (Shorts / Reels / TikTok) get the quality the user actually asked for.
    The old `height<=N` filter silently dropped them one step lower.
    """
    try:
        q = max(144, min(int(quality), 4320))
    except (TypeError, ValueError):
        q = 720

    return {
        "format": "bv*+ba/b",
        "format_sort": [f"res:{q}", "codec:h264", "ext:mp4"],
        "merge_output_format": "mp4",
    }


def audio_selection():
    return {
        "format": "bestaudio/best",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }


# =========================================================
# Error classification
# =========================================================

# Messages live in utils/texts.py (single place for all wording).
ERROR_MESSAGES_AR = DOWNLOAD_ERRORS

# Order matters: the first rule that matches wins.
_ERROR_RULES = [
    ("AGE_RESTRICTED", ("confirm your age", "age-restricted", "age restricted",
                        "inappropriate for some users")),
    ("COOKIES_REQUIRED", ("not a bot", "sign in to confirm", "login required",
                          "log in", "use --cookies", "requires login",
                          "cookies are no longer valid")),
    ("PRIVATE_VIDEO", ("private video", "this video is private", "is private")),
    ("LIVE", ("live event", "is live", "live stream", "live_stream")),
    ("TOO_LARGE", ("max-filesize", "larger than max")),
    ("RATE_LIMIT", ("http error 429", "too many requests", "rate limit",
                    "rate-limit")),
    ("IP_BLOCKED", ("http error 403", "403 forbidden")),
    ("VIDEO_UNAVAILABLE", ("video unavailable", "no longer available",
                           "has been removed", "has been terminated",
                           "not available in your country", "blocked it",
                           "video has been deleted", "does not exist",
                           "http error 404", "this video is not available")),
    ("INVALID_URL", ("unsupported url", "is not a valid url",
                     "no suitable extractor")),
    ("FFMPEG_MISSING", ("ffmpeg is not installed", "ffmpeg not found",
                        "ffprobe and ffmpeg not found", "ffmpeg.exe")),
    ("NO_VIDEO", ("there is no video in this post", "no video could be found")),
    ("NO_FORMATS", ("no video formats found",
                    "requested format is not available")),
    ("EXTRACTOR_BROKEN", ("unable to extract", "unable to download webpage")),
    ("TIMEOUT", ("timed out", "timeout")),
]


def classify_error(text):
    """Return (error_code, friendly_arabic_message) for a yt-dlp error."""
    lowered = clean_error(text, limit=2000).lower()
    for code, patterns in _ERROR_RULES:
        if any(p in lowered for p in patterns):
            return code, ERROR_MESSAGES_AR[code]
    return "DOWNLOAD_ERROR", ERROR_MESSAGES_AR["DOWNLOAD_ERROR"]


def failure_result(platform, exc):
    if isinstance(exc, (asyncio.TimeoutError, TimeoutError)) and not str(exc):
        code, message = "TIMEOUT", ERROR_MESSAGES_AR["TIMEOUT"]
        details = "download timed out"
    elif isinstance(exc, FileNotFoundError):
        code, message = "FILE_NOT_FOUND", ERROR_MESSAGES_AR["FILE_NOT_FOUND"]
        details = clean_error(exc)
    elif isinstance(exc, ValueError):
        code, message = "INVALID_URL", ERROR_MESSAGES_AR["INVALID_URL"]
        details = clean_error(exc)
    else:
        details = clean_error(exc)
        code, message = classify_error(details)

    print(f"❌ [{platform}] {code}: {details[:300]}", flush=True)
    return {
        "success": False,
        "error": message,
        "error_code": code,
        "details": details,
        "platform": platform,
    }


# =========================================================
# Main entry point
# =========================================================

def _download_sync(url, opts):
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)

        if not info:
            raise RuntimeError("yt-dlp returned no information for this URL.")

        # Carousels / playlists: use the first entry only.
        if info.get("entries"):
            entries = [e for e in info["entries"] if e]
            if not entries:
                raise RuntimeError("No downloadable entries found.")
            info = entries[0]

        path = None
        for item in info.get("requested_downloads") or []:
            candidate = item.get("filepath") or item.get("_filename")
            if candidate and os.path.isfile(candidate):
                path = candidate
                break

        return info, path


async def download_with_ytdlp(platform, url, quality="720", audio=False,
                              extra_opts=None):
    """
    Download `url` with yt-dlp in a worker thread.

    On success the result contains `workdir`; the caller is responsible for
    deleting it once the file has been sent.
    """
    workdir = new_workdir()

    try:
        opts = base_options(workdir)

        cookie_file = prepare_cookies(platform.lower(), workdir)
        if cookie_file:
            opts["cookiefile"] = cookie_file

        opts.update(audio_selection() if audio else video_selection(quality))
        if extra_opts:
            opts.update(extra_opts)

        info, path = await asyncio.wait_for(
            asyncio.to_thread(_download_sync, url, opts),
            timeout=DOWNLOAD_TIMEOUT,
        )

        prefer = ".mp3" if audio else None
        if audio and path and not path.lower().endswith(".mp3"):
            path = None
        if not path or not os.path.isfile(path):
            path = find_output_file(workdir, prefer)

        if not path:
            if info.get("is_live"):
                raise RuntimeError("live stream")
            raise FileNotFoundError(
                "yt-dlp finished but no media file was produced "
                "(file too large or filtered out)."
            )

        return {
            "success": True,
            "file_path": path,
            "workdir": workdir,
            "title": info.get("title") or f"{platform} media",
            "duration": info.get("duration") or 0,
            "platform": platform,
            "media_type": "audio" if audio else "video",
        }

    except Exception as exc:  # noqa: BLE001 - converted to a friendly result
        remove_path(workdir)
        return failure_result(platform, exc)
