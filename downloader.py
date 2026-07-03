# downloader.py - النسخة النهائية بدون js_runtimes
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

    def _download_sync(self, url, quality, audio):
        print("\n🔍 Starting download...")
        print(f"URL: {url}")
        print(f"Quality: {quality}")
        print(f"Audio: {audio}")

        opts = self._build_opts(quality, audio, url)

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                print("⏳ Running yt-dlp...")
                info = ydl.extract_info(url, download=True)
                print("✅ yt-dlp finished")

                if info is None:
                    print("❌ INFO IS NONE")
                    return {
                        "success": False,
                        "error": "Invalid URL or unsupported platform",
                        "error_code": "INVALID_URL"
                    }

                file_path = ydl.prepare_filename(info)
                print(f"📁 File path: {file_path}")

                if audio:
                    file_path = os.path.splitext(file_path)[0] + ".mp3"
                    print(f"🎵 Audio file path: {file_path}")

                if not os.path.exists(file_path):
                    print(f"❌ FILE NOT FOUND: {file_path}")
                    return {
                        "success": False,
                        "error": "File not found after download",
                        "error_code": "FILE_NOT_FOUND"
                    }

                print(f"📦 File size: {os.path.getsize(file_path)} bytes")
                print(f"📝 Title: {info.get('title', 'Unknown')}")

                return {
                    "success": True,
                    "file_path": file_path,
                    "title": info.get("title", "Unknown"),
                    "duration": info.get("duration", 0),
                }

        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e)
            print(f"❌ yt-dlp DOWNLOAD ERROR: {error_msg[:150]}")

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
                return {
                    "success": False,
                    "error": "Format not available",
                    "error_code": "FORMAT_NOT_AVAILABLE"
                }

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

            return {
                "success": False,
                "error": error_msg[:150],
                "error_code": "DOWNLOAD_ERROR"
            }

        except Exception as e:
            print(f"❌ UNKNOWN EXCEPTION: {e}")
            return {
                "success": False,
                "error": str(e)[:150],
                "error_code": "UNKNOWN_ERROR"
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
            "extractor_retries": 5,

            "socket_timeout": 30,
            "geo_bypass": True,
            "nocheckcertificate": True,

            "http_headers": {
                "User-Agent": "Mozilla/5.0",
                "Accept-Language": "en-US,en;q=0.9",
            },

            "extractor_args": {
                "youtube": {
                    "player_client": ["android", "web", "tv"],
                }
            },

            "concurrent_fragment_downloads": 1,
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
                    "bv*[height<=720]+ba/bv*+ba/"
                    "bestvideo[height<=720]+bestaudio/best"
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
