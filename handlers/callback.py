from telegram import Update
from telegram.ext import ContextTypes

from keyboards.main_keyboard import main_keyboard, admin_keyboard, admin_panel
from core import is_admin


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    data = q.data
    user_id = update.effective_user.id

    # =========================
    # ADMIN PANEL OPEN
    # =========================
    if data == "admin_panel":
        if is_admin(user_id):
            await q.edit_message_text(
                "👑 لوحة الأدمن",
                reply_markup=admin_panel()
            )
        else:
            await q.edit_message_text("🚫 غير مسموح")

    # =========================
    # HELP VIDEO
    # =========================
    elif data == "help_video":
        await q.edit_message_text("🎬 ابعت الرابط وأنا أحمله كفيديو")

    # =========================
    # HELP AUDIO
    # =========================
    elif data == "help_audio":
        await q.edit_message_text("🎵 ابعت الرابط وأنا أطلع الصوت")

    # =========================
    # SHARE BOT
    # =========================
    elif data == "share_bot":
        await q.edit_message_text("🎁 شارك البوت مع أصحابك ❤️")

    # =========================
    # STATS
    # =========================
    elif data == "my_stats":
        await q.edit_message_text("📊 إحصائياتك هتظهر هنا قريب")

    # =========================
    # BACK
    # =========================
    elif data == "back":
        await q.edit_message_text(
            "🏠 الرئيسية",
            reply_markup=main_keyboard()
        )

    # =========================
    # QUALITY SYSTEM (لو موجود)
    # =========================
    elif data.startswith("q_"):
        value = data.replace("q_", "")

        if value == "audio":
            context.user_data["audio"] = True
            context.user_data["quality"] = None
            await q.edit_message_text("🎵 Audio mode ON")
        else:
            context.user_data["audio"] = False
            context.user_data["quality"] = value
            await q.edit_message_text(f"⚡ Quality: {value}p")

    # =========================
    # FALLBACK
    # =========================
    else:
        await q.edit_message_text("⚠️ Invalid action")
