
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def main_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("🎬 تحميل فيديو", callback_data="help_video"),
            InlineKeyboardButton("🎵 استخراج صوت", callback_data="help_audio")
        ],
        [
            InlineKeyboardButton("⚡ اختيار الجودة", callback_data="quality_menu"),
            InlineKeyboardButton("🎁 مشاركة البوت", callback_data="share_bot")
        ],
        [
            InlineKeyboardButton("📊 إحصائياتي", callback_data="my_stats"),
            InlineKeyboardButton("❓ المساعدة", callback_data="help")
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def admin_keyboard():
    keyboard = [
        [InlineKeyboardButton("👑 لوحة الأدمن", callback_data="admin_panel")],
        [
            InlineKeyboardButton("🎬 تحميل فيديو", callback_data="help_video"),
            InlineKeyboardButton("🎵 استخراج صوت", callback_data="help_audio")
        ],
        [
            InlineKeyboardButton("📊 إحصائياتي", callback_data="my_stats"),
            InlineKeyboardButton("🎁 مشاركة البوت", callback_data="share_bot")
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def admin_panel():
    keyboard = [
        [InlineKeyboardButton("📊 إحصائيات البوت", callback_data="admin_stats")],
        [InlineKeyboardButton("🏆 ترتيب المستخدمين", callback_data="admin_top")],
        [InlineKeyboardButton("📢 إعلان", callback_data="admin_broadcast")],
        [InlineKeyboardButton("👥 المستخدمين", callback_data="admin_users")],
        [InlineKeyboardButton("🚫 حظر", callback_data="admin_block")],
        [InlineKeyboardButton("🔓 إلغاء حظر", callback_data="admin_unblock")],
        [InlineKeyboardButton("🗑️ حذف الكاش", callback_data="admin_clear")],
        [InlineKeyboardButton("🗑️ حذف الكل", callback_data="admin_delete_all")],
        [InlineKeyboardButton("⏱️ وقت التشغيل", callback_data="admin_uptime")],
        [InlineKeyboardButton("📤 نسخة احتياطية", callback_data="admin_backup")],
        [InlineKeyboardButton("📊 مقاييس الأداء", callback_data="admin_metrics")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back")],
    ]
    return InlineKeyboardMarkup(keyboard)


def quality_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("144p", callback_data="q_144"),
            InlineKeyboardButton("240p", callback_data="q_240"),
            InlineKeyboardButton("360p", callback_data="q_360"),
        ],
        [
            InlineKeyboardButton("480p", callback_data="q_480"),
            InlineKeyboardButton("720p 🔥", callback_data="q_720"),
            InlineKeyboardButton("1080p 👑", callback_data="q_1080"),
        ],
        [InlineKeyboardButton("🎵 صوت MP3", callback_data="q_audio")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back")],
    ]
    return InlineKeyboardMarkup(keyboard)
