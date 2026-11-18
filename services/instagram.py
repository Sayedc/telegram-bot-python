# services/instagram.py
from services.common import download_with_ytdlp


async def download_instagram(url: str, quality: str = "720", audio: bool = False):
    """تحميل فيديو من انستجرام (cookies: INSTAGRAM_COOKIES أو Instagram.txt)."""
    return await download_with_ytdlp("Instagram", url, quality, audio)
