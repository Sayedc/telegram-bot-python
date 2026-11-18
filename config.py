import os
from dotenv import load_dotenv

# ==========================================
# Load .env
# ==========================================
load_dotenv()

# ==========================================
# Telegram
# ==========================================
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# ==========================================
# Admins
# ==========================================
ADMIN_IDS = [
    int(x)
    for x in os.getenv("ADMIN_IDS", "").split(",")
    if x.strip().isdigit()
]

# ==========================================
# Paths
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DOWNLOADS_PATH = os.path.join(BASE_DIR, "downloads")
COOKIES_FILE = os.path.join(BASE_DIR, "cookies.txt")
LOGS_PATH = os.path.join(BASE_DIR, "logs")

os.makedirs(DOWNLOADS_PATH, exist_ok=True)

if os.path.exists(LOGS_PATH):
    if os.path.isfile(LOGS_PATH):
        os.remove(LOGS_PATH)
    os.makedirs(LOGS_PATH, exist_ok=True)
else:
    os.makedirs(LOGS_PATH, exist_ok=True)

# ==========================================
# Limits
# ==========================================
MAX_VIDEO_SIZE = 2 * 1024 * 1024 * 1024
MAX_CONCURRENT_DOWNLOADS = 3

# ==========================================
# Bot Info
# ==========================================
BOT_NAME = "Alhawy"
VERSION = "2.0.0"

# ==========================================
# Signature (IMPORTANT)
# ==========================================
# لازم تستخدمه من:
# utils/signature.py

from utils.signature import SIGNATURE
