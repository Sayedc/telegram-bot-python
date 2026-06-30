from downloader import Downloader
from metrics import Metrics
from rate_limiter import RateLimiter
from config import DOWNLOADS_PATH

downloader = Downloader(DOWNLOADS_PATH, max_concurrent=3)
metrics = Metrics()
rate_limiter = RateLimiter(max_requests=10, time_window=60)
