from telegram import InlineKeyboardButton, InlineKeyboardMarkup


# =========================
# MAIN KEYBOARD (DASHBOARD STYLE)
# =========================
def main_keyboard():
    return InlineKeyboardMarkup([
        # 🔥 Admin Panel (full width row)
        [
            InlineKeyboardButton("👑 لوحة الادمن", callback_data="admin_panel")
        ],

        # 🎯 Actions row 1
        [
            InlineKeyboardButton("🎬 تحميل فيديو", callback_data="help_video"),
            InlineKeyboardButton("🎵 استخراج الصوت", callback_data="help_audio"),
        ],

        # 🎯 Actions row 2
        [
            InlineKeyboardButton("🎁 مشاركة البوت", callback_data="share_bot"),
            InlineKeyboardButton("📊 إحصائياتي", callback_data="my_stats"),
        ],
    ])


# =========================
# ADMIN KEYBOARD (PRO STYLE)
# =========================
def admin_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📊 Stats", callback_data="admin_stats"),
            InlineKeyboardButton("🏆 Top", callback_data="admin_top"),
        ],
        [
            InlineKeyboardButton("👥 Users", callback_data="admin_users"),
            InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast"),
        ],
        [
            InlineKeyboardButton("🧹 Clear", callback_data="admin_clear"),
        ],
        [
            InlineKeyboardButton("🔙 رجوع", callback_data="back"),
        ]
    ])
