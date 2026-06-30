from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from keyboards.main_keyboard import main_keyboard, admin_keyboard
from database.user_repository import get_user_stats, get_all_users
from config import ADMIN_IDS


def is_admin(user_id: int):
    return user_id in ADMIN_IDS


# =========================
# MAIN CALLBACK HANDLER
# =========================
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    # =========================
    # AUDIO / VIDEO / QUALITY
    # =========================
    if data == "help_video":
        await query.edit_message_text("🎬 ابعت اللينك وأنا هحمله فيديو")

    elif data == "help_audio":
        await query.edit_message_text("🎵 ابعت اللينك وأنا هحوله صوت")

    elif data == "quality_menu":
        await query.edit_message_text("⚡ اختار الجودة من الإعدادات")

    # =========================
    # SHARE BUTTON (FIXED)
    # =========================
    elif data == "share_bot":
        bot_username = context.bot.username
        link = f"https://t.me/{bot_username}"

        await query.edit_message_text(
            f"🎁 شارك البوت مع أصحابك 👇\n\n{link}"
        )

    # =========================
    # STATS (REAL FIX)
    # =========================
    elif data == "my_stats":
        user_id = query.from_user.id
        stats = get_user_stats(user_id)

        if not stats:
            text = "📊 إحصائياتك فاضية لسه 😅"
        else:
            text = (
                "📊 إحصائياتك:\n\n"
                f"⬇️ تحميلات: {stats.get('downloads', 0)}\n"
                f"🎬 فيديو: {stats.get('videos', 0)}\n"
                f"🎵 صوت: {stats.get('audio', 0)}"
            )

        await query.edit_message_text(text)

    # =========================
    # ADMIN PANEL
    # =========================
    elif data == "admin_panel":
        if not is_admin(query.from_user.id):
            await query.edit_message_text("🚫 مش admin")
            return

        await query.edit_message_text(
            "👑 لوحة الأدمن",
            reply_markup=admin_keyboard()
        )

    elif data == "admin_stats":
        if not is_admin(query.from_user.id):
            return

        users = len(get_all_users())

        await query.edit_message_text(
            f"📊 إحصائيات البوت:\n\n👥 المستخدمين: {users}"
        )

    elif data == "admin_top":
        await query.edit_message_text("🏆 Top users قريباً")

    elif data == "admin_users":
        users = get_all_users()
        await query.edit_message_text(f"👥 عدد المستخدمين: {len(users)}")

    elif data == "admin_clear":
        await query.edit_message_text("🧹 تم التنظيف")

    else:
        await query.edit_message_text("⚠️ Invalid action")
