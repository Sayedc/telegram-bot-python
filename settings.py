# handlers/settings.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes


# جودة التحميل الافتراضية
USER_SETTINGS = {}


def get_user_quality(user_id: int) -> str:
    """الحصول على جودة المستخدم المفضلة"""
    return USER_SETTINGS.get(user_id, {}).get("quality", "720")


def set_user_quality(user_id: int, quality: str):
    """تحديد جودة المستخدم المفضلة"""
    if user_id not in USER_SETTINGS:
        USER_SETTINGS[user_id] = {}
    USER_SETTINGS[user_id]["quality"] = quality


async def settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض إعدادات البوت"""
    user_id = update.effective_user.id
    current_quality = get_user_quality(user_id)

    keyboard = [
        [
            InlineKeyboardButton("📱 144p", callback_data="set_q_144"),
            InlineKeyboardButton("📱 240p", callback_data="set_q_240"),
            InlineKeyboardButton("📱 360p", callback_data="set_q_360"),
        ],
        [
            InlineKeyboardButton("📺 480p", callback_data="set_q_480"),
            InlineKeyboardButton("📺 720p 🔥", callback_data="set_q_720"),
            InlineKeyboardButton("📺 1080p 👑", callback_data="set_q_1080"),
        ],
        [
            InlineKeyboardButton("🎵 صوت MP3 افتراضي", callback_data="set_audio_default"),
        ],
        [
            InlineKeyboardButton("🔙 رجوع", callback_data="back"),
        ],
    ]

    text = f"""
⚙️ *إعدادات التحميل*

📌 الجودة الحالية: *{current_quality}p*

اختر الجودة الافتراضية للتحميل:
"""

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def set_quality(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تغيير جودة التحميل من خلال الكول باك"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data

    if data.startswith("set_q_"):
        quality = data.replace("set_q_", "")
        set_user_quality(user_id, quality)

        await query.edit_message_text(
            f"✅ تم ضبط الجودة إلى *{quality}p* بنجاح!",
            parse_mode="Markdown",
        )
