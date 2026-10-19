import random
import re
import yt_dlp


def get_video_info(url: str):
    try:
        with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
            info = ydl.extract_info(url, download=False)
        if not info:
            return None
        duration = info.get("duration") or 0
        size = info.get("filesize_approx") or info.get("filesize") or 0
        return {
            "title": info.get("title", "Unknown"),
            "duration": f"{duration // 60}:{duration % 60:02d}" if duration else "Unknown",
            "size": f"{round(size / 1048576, 2)} MB" if size else "Unknown",
            "platform": info.get("extractor", "unknown"),
            "uploader": info.get("uploader", "unknown"),
            "views": info.get("view_count", 0),
        }
    except Exception:
        return None


def extract_link(text: str):
    """Extract links; repair spaces accidentally inserted inside TikTok photo IDs."""
    if not text:
        return None
    # Prioritize Photo Mode URLs because a copied ID may contain an accidental space.
    photo = re.search(
        r"https?://(?:www\.)?tiktok\.com/@[^/\s]+/photo/[0-9][0-9 \t]*(?:\?[^\s]*)?",
        text, re.IGNORECASE,
    )
    if photo:
        url = photo.group(0).rstrip(".,;!)]}>")
        url = re.sub(r"(?<=/photo/)[0-9][0-9 \t]*", lambda m: re.sub(r"\s+", "", m.group(0)), url, count=1)
        return url

    patterns = [
        r"(https?://(?:www\.)?tiktok\.com/[^\s]+)",
        r"(https?://vt\.tiktok\.com/[^\s]+)",
        r"(https?://(?:www\.)?youtube\.com/watch\?v=[^\s]+)",
        r"(https?://youtu\.be/[^\s]+)",
        r"(https?://(?:www\.)?instagram\.com/[^\s]+)",
        r"(https?://(?:www\.)?facebook\.com/[^\s]+)",
        r"(https?://fb\.watch/[^\s]+)",
        r"(https?://(?:www\.)?x\.com/[^\s]+)",
        r"(https?://(?:www\.)?twitter\.com/[^\s]+)",
        r"(https?://[^\s]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).rstrip(".,;!)]}>")
    return None


def get_platform(url: str):
    url = (url or "").lower()
    if "tiktok.com" in url: return "TikTok"
    if "youtube.com" in url or "youtu.be" in url: return "YouTube"
    if "instagram.com" in url: return "Instagram"
    if "facebook.com" in url or "fb.watch" in url: return "Facebook"
    if "twitter.com" in url or "x.com" in url: return "Twitter"
    return "Unknown"


def get_random_processing_text():
    return random.choice(["⏳ جاري التحميل...", "🔥 بيتم تجهيز الفيديو...", "⚡ لحظات بس...", "📥 جاري المعالجة..."])


def get_random_success_text():
    return random.choice(["✅ تم التحميل بنجاح!", "🔥 جاهز يا باشا!", "📦 اتبعت الملف!"])


def get_random_error_text():
    return random.choice(["❌ حصل خطأ أثناء التحميل", "⚠️ فشل التحميل، حاول تاني", "🚫 الرابط مش شغال"])


def get_random_sticker():
    return random.choice(["🎉", "🔥", "⚡", "🚀"])
