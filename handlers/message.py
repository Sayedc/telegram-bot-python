import random

# =========================
# رسائل الترحيب
# =========================

WELCOME_RESPONSES = [
    "👋 أهلاً بك في Alhawy Downloader",
    "🚀 أرسل الرابط وسأتولى الباقي.",
    "❤️ جاهز لتحميل أي فيديو أو صوت.",
]

# =========================
# رسائل النجاح
# =========================

SUCCESS_RESPONSES = [
    "✅ تم التحميل بنجاح.",
    "🎉 الفيديو أصبح جاهز.",
    "📥 اكتملت العملية بنجاح.",
]

# =========================
# رسائل المعالجة
# =========================

PROCESSING_MESSAGES = [
    "🔍 جاري فحص الرابط...",
    "🌐 جاري الاتصال بالخادم...",
    "📥 جاري تحميل الملف...",
    "⚙️ جاري تجهيز الملف...",
    "📤 جاري إرسال الملف...",
]

# =========================
# Footer ثابت
# =========================

BOT_FOOTER = (
    "━━━━━━━━━━━━━━━━━━\n\n"
    "👨‍💻 المطور\n"
    "@ALHAWY1\n\n"
    "🤖 Alhawy Downloader\n"
    "@TheAlhawy_Bot\n\n"
    "━━━━━━━━━━━━━━━━━━"
)

# =========================
# رسائل الأخطاء للمستخدم
# =========================

ERROR_MESSAGES = {
    "FORMAT_NOT_AVAILABLE": (
        "━━━━━━━━━━━━━━━━━━\n\n"
        "⚠️ تعذر إكمال العملية\n\n"
        "📹 الجودة المطلوبة غير متوفرة.\n\n"
        "💡 جرّب جودة أقل أو أعد المحاولة لاحقًا.\n\n"
        + BOT_FOOTER
    ),

    "COOKIES_REQUIRED": (
        "━━━━━━━━━━━━━━━━━━\n\n"
        "⚠️ تعذر إكمال العملية\n\n"
        "🍪 يلزم تحديث Cookies الخاصة بـ YouTube.\n\n"
        + BOT_FOOTER
    ),

    "PRIVATE_VIDEO": (
        "━━━━━━━━━━━━━━━━━━\n\n"
        "⚠️ تعذر إكمال العملية\n\n"
        "🔒 الفيديو خاص.\n\n"
        + BOT_FOOTER
    ),

    "VIDEO_UNAVAILABLE": (
        "━━━━━━━━━━━━━━━━━━\n\n"
        "⚠️ الفيديو غير متاح\n\n"
        + BOT_FOOTER
    ),

    "AGE_RESTRICTED": (
        "━━━━━━━━━━━━━━━━━━\n\n"
        "⚠️ تعذر إكمال العملية\n\n"
        "🔞 الفيديو مقيد بالعمر.\n\n"
        + BOT_FOOTER
    ),

    "RATE_LIMIT": (
        "━━━━━━━━━━━━━━━━━━\n\n"
        "⚠️ تعذر إكمال العملية\n\n"
        "🚦 تم تجاوز الحد المسموح.\n"
        "حاول مرة أخرى بعد قليل.\n\n"
        + BOT_FOOTER
    ),

    "TIMEOUT": (
        "━━━━━━━━━━━━━━━━━━\n\n"
        "⚠️ تعذر إكمال العملية\n\n"
        "⌛ انتهت مهلة التحميل.\n\n"
        + BOT_FOOTER
    ),

    "FILE_NOT_FOUND": (
        "━━━━━━━━━━━━━━━━━━\n\n"
        "⚠️ تعذر إكمال العملية\n\n"
        "📁 لم يتم العثور على الملف.\n\n"
        + BOT_FOOTER
    ),

    "UNKNOWN_ERROR": (
        "━━━━━━━━━━━━━━━━━━\n\n"
        "⚠️ حدث خطأ أثناء تنفيذ الطلب.\n\n"
        "يرجى المحاولة مرة أخرى بعد قليل.\n\n"
        + BOT_FOOTER
    )
}

# =========================
# شريط التقدم
# =========================

PROGRESS_BAR = [
    "░░░░░░░░░░ 0%",
    "██░░░░░░░░ 20%",
    "████░░░░░░ 40%",
    "██████░░░░ 60%",
    "████████░░ 80%",
    "██████████ 100%",
]


def get_random_success():
    return random.choice(SUCCESS_RESPONSES)


def get_random_welcome():
    return random.choice(WELCOME_RESPONSES)


def get_processing(step):
    if step < len(PROCESSING_MESSAGES):
        return PROCESSING_MESSAGES[step]
    return PROCESSING_MESSAGES[-1]


def get_error(error_code):
    return ERROR_MESSAGES.get(
        error_code,
        "⚠️ حدث خطأ غير معروف."
    )


def get_random_processing_text():
    return random.choice(PROCESSING_MESSAGES)


# ===========================
# رسائل الحالة
# ===========================

STATUS_MESSAGES = {
    "start": [
        "🚀 بدأنا التحميل...",
        "📥 جاري تجهيز الملف...",
        "⚡ يتم الاتصال بالخادم...",
    ],

    "analyzing": [
        "🔍 تحليل الرابط...",
        "🧠 التعرف على المنصة...",
        "📡 استخراج البيانات...",
    ],

    "downloading": [
        "⬇️ جاري تنزيل الملف...",
        "📥 تحميل الوسائط...",
        "⚙️ يتم تنزيل الفيديو...",
    ],

    "processing": [
        "🛠️ معالجة الملف...",
        "🎬 تجهيز الفيديو...",
        "📦 إنهاء المعالجة...",
    ],

    "uploading": [
        "☁️ رفع الملف إلى تيليجرام...",
        "📤 جاري الإرسال...",
        "🚀 إرسال الملف...",
    ]
}


def get_status_message(stage: str):
    return random.choice(
        STATUS_MESSAGES.get(stage, ["⏳ يرجى الانتظار..."])
    )


def get_response(lst, name=""):
    text = random.choice(lst)
    return text.replace("{name}", name)


def get_random_success_text():
    return get_random_success()


def get_random_error_text():
    return random.choice([
        "حدث خطأ ❌",
        "تعذر التحميل 😥",
        "حاول مرة أخرى لاحقًا ⚠️",
    ])


def get_random_processing_text():
    return random.choice(PROCESSING_MESSAGES)
