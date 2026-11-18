# keyboards/main_keyboard.py
from urllib.parse import quote

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from utils import texts as T

# ---------------------------------------------------------------------------
# الكيبورد الثابت (جنب خانة الكتابة)
# النصوص ثابتة عن قصد: لو اتغيّرت حسب الحالة هتفضل قديمة في شاشة المستخدم.
# ---------------------------------------------------------------------------
BTN_VIDEO = "🎬 تحميل فيديو"
BTN_AUDIO = "🎵 تحميل صوت"
BTN_QUALITY = "⚡ الجودة"
BTN_SETTINGS = "⚙️ الإعدادات"
BTN_STATS = "📊 إحصائياتي"
BTN_HELP = "❓ المساعدة"
BTN_ADMIN = "👑 لوحة التحكم"

# أول رمز في كل زر -> اسم الإجراء
BUTTON_KEYS = {
    "🎬": "video",
    "🎵": "audio",
    "⚡": "quality",
    "⚙": "settings",
    "📊": "stats",
    "❓": "help",
    "👑": "admin",
}


def main_reply_keyboard(is_admin=False):
    rows = [
        [BTN_VIDEO, BTN_AUDIO],
        [BTN_QUALITY, BTN_SETTINGS],
        [BTN_STATS, BTN_HELP],
    ]
    if is_admin:
        rows.append([BTN_ADMIN])

    return ReplyKeyboardMarkup(
        [[KeyboardButton(text) for text in row] for row in rows],
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="📎 الصق رابط الفيديو هنا…",
    )


def match_menu_button(text):
    """Return the action name if `text` is a press of a persistent-menu button."""
    text = (text or "").strip()
    if not text or len(text) > 24 or "http" in text.lower():
        return None
    return BUTTON_KEYS.get(text[0])


# ---------------------------------------------------------------------------
# أزرار داخل الرسائل (Inline)
# ---------------------------------------------------------------------------
def close_row():
    return [InlineKeyboardButton("✖️ إغلاق", callback_data="menu_close")]


def quality_keyboard(current="720"):
    def btn(q, label):
        mark = "✅ " if str(current) == q else ""
        return InlineKeyboardButton(f"{mark}{label}", callback_data=f"q_{q}")

    return InlineKeyboardMarkup([
        [btn("144", "144p"), btn("240", "240p"), btn("360", "360p")],
        [btn("480", "480p"), btn("720", "720p"), btn("1080", "1080p")],
        [
            InlineKeyboardButton("🔙 رجوع", callback_data="menu_settings"),
            InlineKeyboardButton("✖️ إغلاق", callback_data="menu_close"),
        ],
    ])


def settings_keyboard(bot_username=None):
    rows = [
        [
            InlineKeyboardButton("⚡ جودة التحميل", callback_data="menu_quality"),
            InlineKeyboardButton("🔁 تبديل النمط", callback_data="mode_toggle"),
        ],
        [
            InlineKeyboardButton("🔒 الخصوصية", callback_data="menu_privacy"),
            InlineKeyboardButton("🗑️ حذف بياناتي", callback_data="menu_delete"),
        ],
    ]

    if bot_username:
        link = quote(f"https://t.me/{bot_username}", safe="")
        text = quote(T.SHARE_TEXT, safe="")
        rows.append([
            InlineKeyboardButton(
                "📤 مشاركة البوت",
                url=f"https://t.me/share/url?url={link}&text={text}",
            )
        ])

    rows.append([InlineKeyboardButton("🧰 حذف ريبوستات TikTok", callback_data="delete_reposts")])
    rows.append(close_row())
    return InlineKeyboardMarkup(rows)


def back_to_settings_keyboard():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🔙 رجوع", callback_data="menu_settings"),
        InlineKeyboardButton("✖️ إغلاق", callback_data="menu_close"),
    ]])


def confirm_keyboard():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ نعم، احذف", callback_data="confirm_yes"),
        InlineKeyboardButton("✖️ إلغاء", callback_data="confirm_no"),
    ]])


def confirm_reposts_keyboard():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ نعم، متأكد", callback_data="confirm_delete_reposts"),
        InlineKeyboardButton("✖️ إلغاء", callback_data="menu_settings"),
    ]])


# ---------------------------------------------------------------------------
# لوحة الأدمن
# ---------------------------------------------------------------------------
def admin_panel():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📊 إحصائيات البوت", callback_data="admin_stats"),
            InlineKeyboardButton("🏆 الأكثر نشاطاً", callback_data="admin_top"),
        ],
        [
            InlineKeyboardButton("📢 إعلان للجميع", callback_data="admin_broadcast"),
            InlineKeyboardButton("👥 قائمة المستخدمين", callback_data="admin_users"),
        ],
        [
            InlineKeyboardButton("🚫 تقييد مستخدم", callback_data="admin_block"),
            InlineKeyboardButton("🔓 رفع التقييد", callback_data="admin_unblock"),
        ],
        [
            InlineKeyboardButton("🧹 تنظيف الملفات", callback_data="admin_clear"),
            InlineKeyboardButton("🗑️ حذف المستخدمين", callback_data="admin_delete_all"),
        ],
        [
            InlineKeyboardButton("⏱️ مدة التشغيل", callback_data="admin_uptime"),
            InlineKeyboardButton("📤 نسخة احتياطية", callback_data="admin_backup"),
        ],
        [
            InlineKeyboardButton("📈 مقاييس الأداء", callback_data="admin_metrics"),
            InlineKeyboardButton("📋 سجل الأخطاء", callback_data="admin_logs"),
        ],
        [InlineKeyboardButton("🔄 إعادة تشغيل البوت", callback_data="admin_restart")],
        close_row(),
    ])


def admin_back_keyboard():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🔙 لوحة التحكم", callback_data="admin_panel"),
    ]])


def admin_confirm_delete_keyboard():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ نعم، احذف الكل", callback_data="admin_delete_all_yes"),
        InlineKeyboardButton("✖️ إلغاء", callback_data="admin_panel"),
    ]])
