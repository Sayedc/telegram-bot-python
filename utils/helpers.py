import yt_dlp
import random
from datetime import datetime


# =========================
# VIDEO INFO
# =========================
def get_video_info(url: str):
    """يجلب معلومات الفيديو بدون تحميل"""
    try:
        opts = {
            "quiet": True,
            "no_warnings": True,
        }

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)

            duration = info.get("duration", 0)
            size = info.get("filesize_approx", 0)

            return {
                "title": info.get("title", "Unknown"),
                "duration": f"{duration//60}:{duration%60:02d}" if duration else "Unknown",
                "size": f"{round(size/1048576, 2)} MB" if size else "Unknown",
                "platform": info.get("extractor", "unknown"),
                "uploader": info.get("uploader", "unknown"),
                "views": info.get("view_count", 0),
            }

    except Exception:
        return None


# =========================
# LINK PARSER
# =========================
def extract_link(text: str):
    import re

    patterns = [
        r"(https?://(?:www\.)?tiktok\.com/[^\s]+)",
        r"(https?://vt\.tiktok\.com/[^\s]+)",
        r"(https?://(?:www\.)?youtube\.com/watch\?v=[^\s&]+)",
        r"(https?://youtu\.be/[^\s]+)",
        r"(https?://(?:www\.)?instagram\.com/[^\s]+)",
        r"(https?://(?:www\.)?facebook\.com/[^\s]+)",
        r"(https?://fb\.watch/[^\s]+)",
        r"(https?://[^\s]+)",
    ]

    for p in patterns:
        match = re.search(p, text)
        if match:
            return match.group(0)

    return None


# =========================
# PLATFORM DETECTOR
# =========================
def get_platform(url: str):
    url = url.lower()

    if "tiktok" in url:
        return "TikTok"
    if "youtube" in url or "youtu.be" in url:
        return "YouTube"
    if "instagram" in url:
        return "Instagram"
    if "facebook" in url or "fb.watch" in url:
        return "Facebook"
    if "twitter" in url or "x.com" in url:
        return "Twitter"

    return "Unknown"


# =========================
# RANDOM UI TEXTS
# =========================
def get_random_processing_text():
    return random.choice([
        "⏳ جاري التحميل...",
        "🔥 بيتم تجهيز الفيديو...",
        "⚡ لحظات بس...",
        "📥 جاري المعالجة..."
    ])


def get_random_success_text():
    return random.choice([
        "✅ تم التحميل بنجاح!",
        "🔥 جاهز يا باشا!",
        "📦 اتبعت الفيديو!",
    ])


def get_random_error_text():
    return random.choice([
        "❌ حصل خطأ أثناء التحميل",
        "⚠️ فشل التحميل، حاول تاني",
        "🚫 الرابط مش شغال",
    ])


def get_random_sticker():
    return random.choice([
        "🎉",
        "🔥",
        "⚡",
        "🚀"
    ])
