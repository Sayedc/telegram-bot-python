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
from config import BOT_TOKEN, DOWNLOADS_PATH

# ==========================
# CORE (FIX IMPORTANT)
# ==========================
from core import downloader, metrics, rate_limiter, is_admin, get_uptime


START_TIME = datetime.now()

SIGNATURE = "✨ ✨ 𝓐𝓵𝓱𝓪𝔀𝔂 ✨ ✨"
BOT_USERNAME = "@SK_Download_bot"


# ==========================
# POST INIT
# ==========================
async def post_init(app):
    await downloader.start()


# ==========================
# CALLBACK
# ==========================
async def callback(update, context):
    q = update.callback_query
    await q.answer()

    if q.data.startswith("q_"):
        value = q.data[2:]

        context.user_data["audio"] = (value == "audio")
        context.user_data["quality"] = None if value == "audio" else value

        await q.edit_message_text(f"⚡ Updated: {value}")

    elif q.data == "back":
        await q.edit_message_text("🏠 Main Menu")


# ==========================
# MAIN
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

    # handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(callback))

    # admin commands
    app.add_handler(CommandHandler("stats", admin_stats))
    app.add_handler(CommandHandler("top", admin_top))
    app.add_handler(CommandHandler("broadcast", broadcast_cmd))
    app.add_handler(CommandHandler("users", users_cmd))
    app.add_handler(CommandHandler("clear", clear_cmd))
    app.add_handler(CommandHandler("backup", backup_cmd))
    app.add_handler(CommandHandler("block", block_user_cmd))
    app.add_handler(CommandHandler("unblock", unblock_user_cmd))
    app.add_handler(CommandHandler("metrics", admin_metrics_cmd))

    print("=" * 50)
    print(f"🤖 BOT: {BOT_USERNAME}")
    print("🚀 STATUS: PRODUCTION READY")
    print("=" * 50)

    app.run_polling()


if __name__ == "__main__":
    main()
