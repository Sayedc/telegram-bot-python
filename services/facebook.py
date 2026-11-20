# services/facebook.py
from services.common import download_with_ytdlp


async def download_facebook(url: str, quality: str = "720", audio: bool = False):
    """تحميل فيديو من فيسبوك (cookies: FACEBOOK_COOKIES أو cookies_facebook.txt)."""
    return await download_with_ytdlp("Facebook", url, quality, audio)
