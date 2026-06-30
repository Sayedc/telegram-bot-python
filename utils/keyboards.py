from telegram import InlineKeyboardButton, InlineKeyboardMarkup


# =========================
# MAIN KEYBOARD (PRO UI)
# =========================
def main_keyboard():
    return InlineKeyboardMarkup([
        # Row 1 (Primary Action)
        [
            InlineKeyboardButton("🎬 تحميل فيديو", callback_data="help_video"),
            InlineKeyboardButton("🎵 تحميل صوت", callback_data="help_audio"),
        ],

        # Row 2 (Info)
        [
            InlineKeyboardButton("📊 إحصائياتي", callback_data="my_stats"),
        ],

        # Row 3 (Support)
        [
            InlineKeyboardButton("⚙️ المساعدة", callback_data="help"),
        ]
    ])


# =========================
# ADMIN KEYBOARD (PRO UI)
# =========================
def admin_keyboard():
    return InlineKeyboardMarkup([
        # Row 1
        [
            InlineKeyboardButton("📊 Stats", callback_data="admin_stats"),
            InlineKeyboardButton("🏆 Top", callback_data="admin_top"),
        ],

        # Row 2
        [
            InlineKeyboardButton("👥 Users", callback_data="admin_users"),
            InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast"),
        ],

        # Row 3
        [
            InlineKeyboardButton("🧹 Clear", callback_data="admin_clear"),
        ],

        # Row 4 (Back separated for UX)
        [
            InlineKeyboardButton("🔙 Back", callback_data="back"),
        ]
    ])
