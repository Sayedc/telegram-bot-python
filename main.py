import os
from datetime import datetime

from telegram.ext import (
    Application,
    MessageHandler,
    CallbackQueryHandler,
    CommandHandler,
    filters,
)

# ==========================
# HANDLERS
# ==========================
from handlers.start import start
from handlers.message import handle_message

from handlers.admin import (
    admin_stats,
    admin_top,
    broadcast_cmd,
    users_cmd,
    clear_cmd,
    backup_cmd,
    block_user_cmd,
    unblock_user_cmd,
    admin_metrics_cmd
)

# ==========================
# CONFIG
# ==========================
from config import BOT_TOKEN, DOWNLOADS_PATH, ADMIN_IDS

# ==========================
# CORE SYSTEM (IMPORTANT FIX)
# ==========================
from core import downloader, metrics, rate_limiter, is_admin, get_uptime


# ==========================
# BOT INFO
# ==========================
BOT_USERNAME = "@SK_Download_bot"
SIGNATURE = "✨ ✨ 𝓐𝓵𝓱𝓪𝔀𝔂 ✨ ✨"

START_TIME = datetime.now()


# ==========================
# POST INIT
# ==========================
async def post_init(app):
    await downloader.start()


# ==========================
# CALLBACK HANDLER (FIXED & STABLE)
# ==========================
async def callback(update, context):
    q = update.callback_query
    await q.answer()

    data = q.data
    user_id = update.effective_user.id

    # 🎯 quality / audio system
    if data.startswith("q_"):
        value = data.replace("q_", "")

        if value == "audio":
            context.user_data["audio"] = True
            context.user_data["quality"] = None
            await q.edit_message_text("🎵 Audio mode activated")
        else:
            context.user_data["audio"] = False
            context.user_data["quality"] = value
            await q.edit_message_text(f"⚡ Quality set to {value}p")

    # 🔙 back button
    elif data == "back":
        await q.edit_message_text(
            "🏠 Main Menu\n\n✨ اختر من القائمة",
        )

    # 🛡 fallback (prevents dead buttons)
    else:
        await q.edit_message_text("⚠️ Invalid action")


# ==========================
# MAIN FUNCTION
# ==========================
def main():
    from database.user_repository import init_db

    init_db()

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    # ==========================
    # USER HANDLERS
    # ==========================
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # ==========================
    # CALLBACK HANDLER
    # ==========================
    app.add_handler(CallbackQueryHandler(callback))

    # ==========================
    # ADMIN COMMANDS
    # ==========================
    app.add_handler(CommandHandler("stats", admin_stats))
    app.add_handler(CommandHandler("top", admin_top))
    app.add_handler(CommandHandler("broadcast", broadcast_cmd))
    app.add_handler(CommandHandler("users", users_cmd))
    app.add_handler(CommandHandler("clear", clear_cmd))
    app.add_handler(CommandHandler("backup", backup_cmd))
    app.add_handler(CommandHandler("block", block_user_cmd))
    app.add_handler(CommandHandler("unblock", unblock_user_cmd))
    app.add_handler(CommandHandler("metrics", admin_metrics_cmd))

    # ==========================
    # START LOG
    # ==========================
    print("=" * 55)
    print(f"🤖 BOT STARTED: {BOT_USERNAME}")
    print("🚀 STATUS: PRODUCTION MODE")
    print("⚡ CALLBACK FIXED")
    print("🧠 ADMIN SYSTEM READY")
    print("=" * 55)

    app.run_polling()


# ==========================
# RUN
# ==========================
if __name__ == "__main__":
    main()
