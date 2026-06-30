
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


# =========================
# Main Keyboard
# =========================
def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎬 تحميل", callback_data="help_video")],
        [InlineKeyboardButton("🎵 صوت", callback_data="help_audio")],
        [InlineKeyboardButton("📊 إحصائيات", callback_data="my_stats")],
        [InlineKeyboardButton("⚙️ المساعدة", callback_data="help")]
    ])


# =========================
# Admin Keyboard
# =========================
def admin_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Stats", callback_data="admin_stats")],
        [InlineKeyboardButton("👥 Users", callback_data="admin_users")],
        [InlineKeyboardButton("🏆 Top", callback_data="admin_top")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")],
        [InlineKeyboardButton("🧹 Clear", callback_data="admin_clear")],
        [InlineKeyboardButton("🔙 Back", callback_data="back")]
    ])
