import random

def extract_link(text):
    import re
    match = re.search(r'https?://[^\s]+', text)
    return match.group(0) if match else None


def get_platform(url):
    if "tiktok" in url:
        return "TikTok"
    if "youtube" in url:
        return "YouTube"
    if "instagram" in url:
        return "Instagram"
    return "Unknown"


def get_random_processing_text():
    return random.choice(["⏳ جاري المعالجة...", "⚡ شغال...", "🔥 لحظة بس..."])


def get_random_success_text():
    return random.choice(["تم بنجاح 🎉", "جاهز ✔️"])


def get_random_error_text():
    return random.choice(["حصل خطأ ❌", "حاول تاني"])


def get_random_sticker():
    return None
