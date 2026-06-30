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
from handlers.callback import callback_handler  # 👈 لازم تكون دي موجودة في callback.py

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
# CORE SYSTEM
# ==========================
from core import downloader, metrics, rate_limiter, is_admin, get_uptime


BOT_USERNAME = "@SK_Download_bot"
SIGNATURE = "✨ ✨ 𝓐𝓵𝓱𝓪𝔀𝔂 ✨ ✨"

START_TIME = datetime.now()


# ==========================
# POST INIT
# ==========================
async def post_init(app):
    await downloader.start()


# ==========================
# CALLBACK (MAIN FIX)
# ==========================
async def callback(update, context):
    q = update.callback_query
    await q.answer()

    data = q.data

    # 🎯 forward to callback_handler (لو انت عامل ملف منفصل)
    if callback_handler:
        return await callback_handler(update, context)

    # fallback
    await q.edit_message_text("⚠️ Invalid action")


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

    # USER
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # CALLBACK
    app.add_handler(CallbackQueryHandler(callback))

    # ADMIN
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
    print("⚡ CALLBACK FIXED")
    print("=" * 50)

    app.run_polling()


if __name__ == "__main__":
    main()
