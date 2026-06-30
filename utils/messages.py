import random

WELCOME_RESPONSES = [
    "أتمنى لك يوماً سعيداً ❤️",
    "جاهز لتحميل أي رابط 🚀",
    "أرسل الرابط وسأتولى الباقي 😎",
    "مرحباً بك من جديد 🌍",
    "أهلاً بك في أفضل بوت تحميل 🔥"
]

SUCCESS_RESPONSES = [
    "تم التحميل بنجاح ✅",
    "كل شيء جاهز 🎉",
    "استمتع بالفيديو ❤️",
    "تم التنفيذ بنجاح 🚀"
]

ERROR_RESPONSES = [
    "حدث خطأ ❌",
    "تعذر التحميل 😥",
    "حاول مرة أخرى لاحقاً ⚠️"
]

PROCESSING_RESPONSES = [
    "جارى التحميل... ⏳",
    "يرجى الانتظار قليلاً 🚀",
    "جارى معالجة الرابط 📥"
]


def get_response(lst, name=""):
    text = random.choice(lst)
    return text.replace("{name}", name)


def get_random_success_text():
    return random.choice(SUCCESS_RESPONSES)


def get_random_error_text():
    return random.choice(ERROR_RESPONSES)


def get_random_processing_text():
    return random.choice(PROCESSING_RESPONSES)
