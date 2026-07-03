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
# رسائل الأخطاء للمستخدم
# =========================

ERROR_MESSAGES = {
    "FORMAT_NOT_AVAILABLE": (
        "⚠️ نوع المشكلة\n\n"
        "📹 الجودة غير متوفرة\n\n"
        "💡 جرّب جودة أقل."
    ),

    "COOKIES_REQUIRED": (
        "⚠️ نوع المشكلة\n\n"
        "🍪 يلزم تسجيل الدخول إلى YouTube."
    ),

    "PRIVATE_VIDEO": (
        "⚠️ نوع المشكلة\n\n"
        "🔒 الفيديو خاص."
    ),

    "VIDEO_UNAVAILABLE": (
        "⚠️ نوع المشكلة\n\n"
        "🚫 الفيديو غير متاح."
    ),

    "AGE_RESTRICTED": (
        "⚠️ نوع المشكلة\n\n"
        "🔞 الفيديو مقيد بالعمر."
    ),

    "RATE_LIMIT": (
        "⚠️ نوع المشكلة\n\n"
        "🚦 تم تجاوز الحد المسموح.\n"
        "حاول مرة أخرى بعد قليل."
    ),

    "TIMEOUT": (
        "⚠️ نوع المشكلة\n\n"
        "⌛ انتهت مهلة التحميل."
    ),

    "FILE_NOT_FOUND": (
        "⚠️ نوع المشكلة\n\n"
        "📁 لم يتم العثور على الملف."
    ),

    "UNKNOWN_ERROR": (
        "⚠️ حدث خطأ غير متوقع."
    )
}

# =========================
# شريط التقدم
# =========================

PROGRESS_BAR = [
    "⬜⬜⬜⬜⬜",
    "🟩⬜⬜⬜⬜",
    "🟩🟩⬜⬜⬜",
    "🟩🟩🟩⬜⬜",
    "🟩🟩🟩🟩⬜",
    "🟩🟩🟩🟩🟩",
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
