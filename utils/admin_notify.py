# utils/admin_notify.py
"""Send download-failure reports to the admins (throttled, plain text)."""

import time
from datetime import datetime

from config import ADMIN_IDS
from utils.signature import SIGNATURE

# Codes that are the user's problem, not worth waking the admin for.
USER_SIDE_CODES = {
    "INVALID_URL", "PRIVATE_VIDEO", "VIDEO_UNAVAILABLE", "AGE_RESTRICTED",
    "LIVE", "TOO_LARGE", "NO_VIDEO",
}

_EMOJIS = {
    "COOKIES_REQUIRED": "🍪", "IP_BLOCKED": "🌐", "RATE_LIMIT": "⏳",
    "FFMPEG_MISSING": "🎬", "NO_FORMATS": "📹", "EXTRACTOR_BROKEN": "🛠️",
    "TIMEOUT": "⏰", "FILE_NOT_FOUND": "📁", "DOWNLOAD_ERROR": "⚠️",
    "PHOTO_DEPENDENCY_MISSING": "📦", "PHOTO_DOWNLOAD_FAILED": "🖼️",
    "EXCEPTION": "💥",
}

_ADVICE = {
    "COOKIES_REQUIRED": "الكوكيز ناقصة أو منتهية. حدّثها (YOUTUBE_COOKIES / INSTAGRAM_COOKIES / FACEBOOK_COOKIES).",
    "IP_BLOCKED": "الـ IP بتاع السيرفر ممكن يكون محظور مؤقتاً. جرب PROXY أو استنى.",
    "RATE_LIMIT": "المنصة بتحدد الطلبات. قلل الضغط أو استخدم PROXY.",
    "FFMPEG_MISSING": "ثبّت FFmpeg على السيرفر.",
    "NO_FORMATS": "حدّث yt-dlp وتأكد إن node أو deno موجود على PATH (يوتيوب محتاج JS runtime).",
    "EXTRACTOR_BROKEN": "غالباً المنصة غيّرت شكلها. حدّث yt-dlp: pip install -U 'yt-dlp[default]'.",
    "TIMEOUT": "التحميل بطيء أو الفيديو كبير.",
    "FILE_NOT_FOUND": "yt-dlp خلص من غير ملف ناتج. راجع اللوج.",
    "PHOTO_DEPENDENCY_MISSING": "أضف gallery-dl إلى requirements.txt وأعد النشر.",
    "PHOTO_DOWNLOAD_FAILED": "حدّث gallery-dl وجرب مجدداً.",
}

_THROTTLE_SECONDS = 600
_last_sent = {}


async def notify_admins(bot, user_id, url, platform, error_code, details):
    """Send at most one report per (platform, error code) every 10 minutes."""
    code = error_code or "UNKNOWN"
    if code in USER_SIDE_CODES or not ADMIN_IDS:
        return

    key = (platform, code)
    now = time.time()
    if now - _last_sent.get(key, 0) < _THROTTLE_SECONDS:
        return
    _last_sent[key] = now

    report = (
        f"{_EMOJIS.get(code, '❌')} تقرير خطأ في التحميل\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        f"👤 المستخدم: {user_id}\n"
        f"📱 المنصة: {platform}\n"
        f"🔗 الرابط: {(url or '')[:150]}\n"
        f"📋 الكود: {code}\n"
        f"⏱️ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        f"💡 {_ADVICE.get(code, 'راجع اللوج.')}\n\n"
        f"📄 التفاصيل:\n{(details or '')[:900]}\n"
        f"{SIGNATURE}"
    )

    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, report[:4000])
        except Exception as exc:  # noqa: BLE001
            print(f"Failed to send error report to admin {admin_id}: {exc}", flush=True)
