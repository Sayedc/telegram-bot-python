import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(",")))
MAX_FILE_SIZE_MB = 50
DOWNLOADS_PATH = "downloads"
CACHE_PATH = "cache"
SUPPORTED_QUALITIES = ["144p", "240p", "360p", "480p", "720p", "1080p"]
DEFAULT_QUALITY = "720p"
ALLOWED_DOMAINS = [
    "youtube.com", "youtu.be",
    "instagram.com", "fb.watch", "facebook.com",
    "tiktok.com", "twitter.com", "x.com",
    "reddit.com", "pinterest.com", "tumblr.com"
]
