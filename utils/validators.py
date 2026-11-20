# utils/validators.py
import re


def is_valid_url(url: str) -> bool:
    """التحقق من صحة الرابط"""
    if not url:
        return False

    url_pattern = re.compile(
        r"^https?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain...
        r"localhost|"  # localhost...
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )

    return bool(url_pattern.match(url))


def is_supported_platform(url: str) -> bool:
    """التحقق إذا كان الرابط مدعوم"""
    supported = [
        "tiktok",
        "youtube",
        "youtu.be",
        "instagram",
        "facebook",
        "fb.watch",
        "twitter",
        "x.com",
        "soundcloud",
        "spotify",
        "deezer",
    ]

    url_lower = url.lower()

    for platform in supported:
        if platform in url_lower:
            return True

    return False


def sanitize_filename(filename: str) -> str:
    """تنظيف اسم الملف من الأحرف غير المسموحة"""
    # إزالة الأحرف غير المسموحة
    filename = re.sub(r'[\\/*?:"<>|]', "", filename)

    # تقليل المسافات المتتالية
    filename = re.sub(r"\s+", " ", filename)

    # تقليل الطول
    if len(filename) > 100:
        filename = filename[:97] + "..."

    return filename.strip()
