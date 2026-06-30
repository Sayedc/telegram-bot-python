import re
import yt_dlp
import random

# =========================
# استخراج اللينك من أي نص
# =========================
def extract_link(text: str):
    patterns = [
        r'(https?://(?:www\.)?tiktok\.com/[^\s]+)',
        r'(https?://vt\.tiktok\.com/[^\s]+)',
        r'(https?://(?:www\.)?youtube\.com/watch\?v=[^\s&]+)',
        r'(https?://youtu\.be/[^\s]+)',
        r'(https?://(?:www\.)?youtube\.com/shorts/[^\s]+)',
        r'(https?://(?:www\.)?instagram\.com/[^\s]+)',
        r'(https?://(?:www\.)?facebook\.com/[^\s]+)',
        r'(https?://fb\.watch/[^\s]+)',
        r'(https?://[^\s]+)',
    ]

    for p in patterns:
        m = re.search(p, text)
        if m:
            return m.group(0)

    return None


# =========================
# معلومات الفيديو
# =========================
async def get_video_info(url: str):
    opts = {
        "quiet": True,
        "no_warnings": True,
    }

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)

            duration = info.get("duration", 0)

            if duration:
                minutes = duration // 60
                seconds = duration % 60
                duration_str = f"{minutes}:{seconds:02d}"
            else:
                duration_str = "غير معروف"

            size = info.get("filesize_approx", 0)

            if size:
                size_mb = size / 1048576
                size_str = f"{size_mb:.1f} MB"
            else:
                size_str = "غير معروف"

            return {
                "title": info.get("title", "غير معروف"),
                "duration": duration_str,
                "size": size_str,
            }

    except Exception:
        return None

def get_platform(url: str):
    url = url.lower()

    if "tiktok" in url:
        return "TikTok"
    elif "youtube" in url or "youtu.be" in url:
        return "YouTube"
    elif "instagram" in url:
        return "Instagram"
    elif "facebook" in url or "fb.watch" in url:
        return "Facebook"
    elif "twitter" in url or "x.com" in url:
        return "Twitter"
    elif "soundcloud" in url:
        return "SoundCloud"
    elif "spotify" in url:
        return "Spotify"
    elif "deezer" in url:
        return "Deezer"
    else:
        return "Website"

def get_random_sticker():
    stickers = [
        "🎉",
        "🔥",
        "⚡",
        "💯",
        "🚀",
        "😂",
        "👍",
        "😍",
        "💀",
        "🤖"
    ]

    return random.choice(stickers)

