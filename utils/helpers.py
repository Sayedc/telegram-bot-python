import random
import re
from datetime import datetime

SIGNATURE = "✨ 𝓐𝓵𝓱𝓪𝔀𝔂 ✨"

STICKERS = {
    "processing": ["🔄", "⚙️", "⏳", "⌛", "📥", "🔧", "⚡", "💨", "🚀"],
    "success": ["🎉", "✅", "🤍", "🔥", "💎", "⭐"],
    "error": ["❌", "⚠️", "🚫", "💔"]
}

PROCESSING_TEXTS = [
    "يتم التحميل يا {name} ⚡",
    "شوية صبر يا {name} 🎬",
    "على توكل على الله يا {name} 🚀",
    "استنى بس يا {name} 🤍"
]

SUCCESS_TEXTS = [
    "🎬 خد الفيديو يا باشا",
    "✅ تم يا فنان",
    "🔥 ألف هنا"
]

ERROR_TEXTS = [
    "❌ معلش الفيديو معدش موجود",
    "⚠️ حاجة غلطت",
    "🚫 جرب رابط آخر"
]

WELCOME_RESPONSES = [
    "🎬 اهلاً بيك يا باشا {name}",
    "💫 نورت يا فنان {name}",
    "🔥 يا مرحباً يا كبير {name}"
]


def get_random_sticker(category):
    return random.choice(STICKERS.get(category, ["🎉"]))


def get_random_processing_text(name):
    return random.choice(PROCESSING_TEXTS).format(name=name)


def get_random_success_text():
    return random.choice(SUCCESS_TEXTS)


def get_random_error_text():
    return random.choice(ERROR_TEXTS)


def get_response(responses, name=None):
    text = responses[datetime.now().second % len(responses)]
    return text.format(name=name) if name else text


def extract_link(text):
    patterns = [
        r'(https?://(?:www\.)?tiktok\.com/[^\s]+)',
        r'(https?://vt\.tiktok\.com/[^\s]+)',
        r'(https?://(?:www\.)?youtube\.com/watch\?v=[^\s&]+)',
        r'(https?://youtu\.be/[^\s]+)',
        r'(https?://(?:www\.)?instagram\.com/[^\s]+)',
        r'(https?://(?:www\.)?facebook\.com/[^\s]+)',
        r'(https?://fb\.watch/[^\s]+)',
        r'(https?://(?:www\.)?twitter\.com/[^\s]+)',
        r'(https?://(?:www\.)?x\.com/[^\s]+)',
        r'(https?://[^\s]+)',
    ]

    for p in patterns:
        m = re.search(p, text, re.I)
        if m:
            return m.group(0)

    return None


def get_platform(url):
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

    return "Website"
