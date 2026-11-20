# utils/platform.py
import re


def extract_link(text: str) -> str | None:
    """استخراج الرابط من النص"""
    patterns = [
        r"(https?://(?:www\.)?tiktok\.com/[^\s]+)",
        r"(https?://vt\.tiktok\.com/[^\s]+)",
        r"(https?://(?:www\.)?youtube\.com/watch\?v=[^\s&]+)",
        r"(https?://youtu\.be/[^\s]+)",
        r"(https?://(?:www\.)?youtube\.com/shorts/[^\s]+)",
        r"(https?://(?:www\.)?instagram\.com/(?:p|reel|stories)/[^\s/?]+)",
        r"(https?://(?:www\.)?facebook\.com/(?:watch|reel|share|share/r)/[^\s]+)",
        r"(https?://fb\.watch/[^\s]+)",
        r"(https?://(?:www\.)?twitter\.com/[\w]+/status/[\d]+)",
        r"(https?://(?:www\.)?x\.com/[\w]+/status/[\d]+)",
        r"(https?://(?:www\.)?soundcloud\.com/[\w]+/[\w-]+)",
        r"(https?://(?:www\.)?spotify\.com/[\w]+/[\w-]+)",
        r"(https?://(?:www\.)?deezer\.com/[\w]+/[\w-]+)",
        r"(https?://[^\s]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0)

    return None


def get_platform(url: str) -> str:
    """تحديد المنصة من الرابط"""
    url_lower = url.lower()

    if "tiktok" in url_lower:
        return "TikTok"
    if "youtube" in url_lower or "youtu.be" in url_lower:
        return "YouTube"
    if "instagram" in url_lower:
        return "Instagram"
    if "facebook" in url_lower or "fb.watch" in url_lower:
        return "Facebook"
    if "twitter" in url_lower or "x.com" in url_lower:
        return "Twitter"
    if "soundcloud" in url_lower:
        return "SoundCloud"
    if "spotify" in url_lower:
        return "Spotify"
    if "deezer" in url_lower:
        return "Deezer"

    return "Website"
