# downloader.py - النسخة النهائية المعدلة بالكامل

import os
import asyncio
import yt_dlp
from datetime import datetime
from collections import deque


class Downloader:
    def __init__(self, download_path: str, max_concurrent: int = 3):
        self.download_path = download_path
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.queue = deque()
        self.active = 0
        self.success = 0
        self.failed = 0
        self.started = False

        os.makedirs(self.download_path, exist_ok=True)

    async def start(self):
        self.started = True
        print("🚀 Downloader Engine Started")

    def get_stats(self):
        return {
            "queue_size": len(self.queue),
            "active": self.active,
            "success": self.success,
            "failed": self.failed,
        }

    async def download(self, url: str, quality="720", audio=False):
        print(f"\n📥 DOWNLOAD START: {url[:50]}...")
        async with self.semaphore:
            self.active += 1
            try:
                loop = asyncio.get_event_loop()
                result = await asyncio.wait_for(
                    loop.run_in_executor(
                        None,
                        self._download_sync,
                        url,
                        quality,
                        audio
                    ),
                    timeout=120
                )
                self.success += 1
                print(f"✅ DOWNLOAD COMPLETE: {result.get('title', 'Unknown')[:50]}...")
                return result

            except asyncio.TimeoutError:
                self.failed += 1
                print("❌ DOWNLOAD TIMEOUT")
                return {
                    "success": False,
                    "error": "Timed out",
                    "error_code": "TIMEOUT"
                }

            except Exception as e:
                self.failed += 1
                print(f"❌ DOWNLOAD EXCEPTION: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "error_code": "EXCEPTION"
                }

            finally:
                self.active -= 1

    def _find_file(self, path):
        if os.path.exists(path):
            return path

        base = os.path.splitext(path)[0]

        for ext in (
            ".mp4",
            ".mkv",
            ".webm",
            ".mov",
            ".mp3",
            ".m4a",
        ):
            candidate = base + ext
            if os.path.exists(candidate):
                return candidate

        return None

    def _download_sync(self, url, quality, audio):
        print("\n🔍 Starting download...")
        print(f"URL: {url}")
        print(f"Quality: {quality}")
        print(f"Audio: {audio}")

        opts = self._build_opts(quality, audio, url)

        formats = [
            opts["format"],
            "bestvideo+bestaudio/best",
            "best",
            "18",
        ]

        last_error = None

        for fmt in formats:
            current = opts.copy()
            current["format"] = fmt

            try:
                with yt_dlp.YoutubeDL(current) as ydl:
                    print(f"⏳ Running yt-dlp with format: {fmt}")
                    info = ydl.extract_info(url, download=True)
                    print("✅ yt-dlp finished")

                    if not info:
                        continue

                    file_path = ydl.prepare_filename(info)

                    if audio:
                        file_path = (
                            os.path.splitext(file_path)[0]
                            + ".mp3"
                        )

                    file_path = self._find_file(file_path)

                    if not file_path:
                        continue

                    print(f"📁 File path: {file_path}")
                    print(f"📦 File size: {os.path.getsize(file_path)} bytes")
                    print(f"📝 Title: {info.get('title', 'Unknown')}")

                    return {
                        "success": True,
                        "file_path": file_path,
                        "title": info.get("title", "Unknown"),
                        "duration": info.get("duration", 0),
                        "uploader": info.get("uploader", ""),
                        "thumbnail": info.get("thumbnail", ""),
                        "view_count": info.get("view_count", 0),
                    }

            except yt_dlp.utils.DownloadError as e:
                error_msg = str(e)
                print(f"❌ yt-dlp DOWNLOAD ERROR with format {fmt}: {error_msg[:150]}")
                
                # ===== أكواد خطأ محددة =====
                if "Sign in to confirm" in error_msg:
                    return {
                        "success": False,
                        "error": "Sign in required",
                        "error_code": "COOKIES_REQUIRED"
                    }

                if "Private video" in error_msg:
                    return {
                        "success": False,
                        "error": "Video is private",
                        "error_code": "PRIVATE_VIDEO"
                    }

                if "Video unavailable" in error_msg:
                    return {
                        "success": False,
                        "error": "Video unavailable",
                        "error_code": "VIDEO_UNAVAILABLE"
                    }

                if "This video is age-restricted" in error_msg:
                    return {
                        "success": False,
                        "error": "Age restricted",
                        "error_code": "AGE_RESTRICTED"
                    }

                if "Requested format is not available" in error_msg:
                    last_error = "Format not available, trying next format..."
                    continue

                if "rate limit" in error_msg.lower():
                    return {
                        "success": False,
                        "error": "Rate limited",
                        "error_code": "RATE_LIMIT"
                    }

                if "IP address is blocked" in error_msg:
                    return {
                        "success": False,
                        "error": "Your IP address is blocked from accessing this post",
                        "error_code": "IP_BLOCKED"
                    }

                if "ffmpeg is not installed" in error_msg:
                    return {
                        "success": False,
                        "error": "FFmpeg is not installed. Aborting due to -",
                        "error_code": "FFMPEG_MISSING"
                    }

                if "cookies" in error_msg.lower():
                    return {
                        "success": False,
                        "error": "Cookie error",
                        "error_code": "COOKIES_ERROR"
                    }

                last_error = error_msg
                continue

            except Exception as e:
                print(f"❌ EXCEPTION with format {fmt}: {e}")
                last_error = str(e)
                continue

        return {
            "success": False,
            "error": last_error or "Unknown error",
            "error_code": "DOWNLOAD_ERROR",
        }

    def _build_opts(self, quality, audio, url=None):
        quality_map = {
            "144": "worst[height<=144]",
            "240": "best[height<=240]",
            "360": "best[height<=360]",
            "480": "best[height<=480]",
            "720": "best[height<=720]",
            "1080": "best[height<=1080]",
        }

        fmt = quality_map.get(quality, "best[height<=720]")

        opts = {
            "outtmpl": os.path.join(self.download_path, "%(title)s.%(ext)s"),
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": False,
            "noplaylist": True,

            "retries": 10,
            "fragment_retries": 10,
            "extractor_retries": 10,
            "file_access_retries": 10,

            "socket_timeout": 30,
            "geo_bypass": True,
            "nocheckcertificate": True,

            "retry_sleep_functions": {
                "http": lambda n: 2,
            },

            "http_headers": {
                "User-Agent": "Mozilla/5.0",
                "Accept-Language": "en-US,en;q=0.9",
            },

            "extractor_args": {
                "youtube": {
                    "player_client": [
                        "android",
                        "web",
                        "ios",
                    ]
                }
            },

            "concurrent_fragment_downloads": 4,
        }

        cookies_file = self._get_cookies_file(url)
        if cookies_file and os.path.exists(cookies_file):
            opts["cookiefile"] = cookies_file
            print(f"🍪 Using cookies: {cookies_file}")

        if url and "tiktok" in url:
            opts["extractor_args"] = {
                "tiktok": {
                    "without_watermark": ["true"],
                }
            }
            print("🎵 TikTok: without watermark enabled")

        if audio:
            opts.update({
                "format": "bestaudio[ext=m4a]/bestaudio/best",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
            })
            print("🎵 Audio mode: MP3 extraction enabled")
        else:
            opts.update({
                "format": (
                    f"bestvideo*[height<={quality}]"
                    f"+bestaudio/"
                    f"best[height<={quality}]"
                    f"/bestvideo+bestaudio"
                    f"/best"
                    f"/18"
                ),
                "merge_output_format": "mp4",
            })
            print("🎬 Video mode: advanced format with fallback")

        print(f"⚙️ Options: cookies={cookies_file if cookies_file else 'None'}, format={opts.get('format', 'default')}")
        return opts

    def _get_cookies_file(self, url):
        if not url:
            return None

        base_dir = os.path.dirname(__file__)

        if "youtube.com" in url or "youtu.be" in url:
            path = os.path.join(base_dir, "cookies_youtube.txt")
            if os.path.exists(path):
                return path

        if "facebook.com" in url or "fb.watch" in url:
            path = os.path.join(base_dir, "cookies_facebook.txt")
            if os.path.exists(path):
                return path

        if "instagram.com" in url:
            path = os.path.join(base_dir, "cookies_instagram.txt")
            if os.path.exists(path):
                return path

        if "twitter.com" in url or "x.com" in url:
            path = os.path.join(base_dir, "cookies_twitter.txt")
            if os.path.exists(path):
                return path

        default_path = os.path.join(base_dir, "cookies.txt")
        if os.path.exists(default_path):
            return default_path

        print("⚠️ No cookies file found")
        return None
