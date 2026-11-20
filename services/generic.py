# services/generic.py
from services.common import download_with_ytdlp


async def download_generic(url: str, quality: str = "720", audio: bool = False,
                           platform: str = "Website"):
    """أي موقع تاني يدعمه yt-dlp (تويتر، ساوند كلاود، ...)."""
    return await download_with_ytdlp(platform, url, quality, audio)
