from datetime import datetime
from downloader import Downloader
from metrics import Metrics
from rate_limiter import RateLimiter
from config import DOWNLOADS_PATH, ADMIN_IDS

# shared instances
downloader = Downloader(DOWNLOADS_PATH, max_concurrent=3)
metrics = Metrics()
rate_limiter = RateLimiter(10, 60)

START_TIME = datetime.now()


def is_admin(user_id: int):
    return user_id in ADMIN_IDS


def get_uptime():
    delta = datetime.now() - START_TIME
    return str(delta).split('.')[0]
