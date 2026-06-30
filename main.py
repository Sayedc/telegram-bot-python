# main.py - PRO STABLE VERSION

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
from config import BOT_TOKEN, ADMIN_IDS, DOWNLOADS_PATH

# ==========================
# SYSTEM CLASSES
# ==========================
from downloader import Downloader
from metrics import Metrics
from rate_limiter import RateLimiter

# ==========================
# DATABASE
# ==========================
from database.user_repository import init_db


# =====================================================
# GLOBAL SINGLE INSTANCES (IMPORTANT FIX - NO DUPLICATE)
# =====================================================
downloader = Downloader(DOWNLOADS_PATH, max_concurrent=3)
metrics = Metrics()
rate_limiter = RateLimiter(max_requests=10, time_window=60)

START_TIME = datetime.now()

SIGNATURE = "✨ ✨ 𝓐𝓵𝓱𝓪𝔀𝔂 ✨ ✨"
BOT_USERNAME = "@SK_Download_bot"


# ==========================
# HELPERS
# ==========================
def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def get_uptime() -> str:
    delta = datetime.now() - START_TIME
    return str(delta).split('.')[0]


# ==========================
# INIT
# ==========================
os.makedirs(DOWNLOADS_PATH, exist_ok=True)


# ==========================
# POST INIT
# ==========================
async def post_init(app):
    await downloader.start()


# ==========================
# CALLBACK HANDLER (FIXED UI BUG)
# ==========================
async def callback(update, context):
    q = update.callback_query
    await q.answer()

    user_id = update.effective_user.id

    if q.data.startswith("q_"):
        value = q.data[2:]

        if value == "audio":
            context.user_data["audio"] = True
            context.user_data["quality"] = None
        else:
            context.user_data["audio"] = False
            context.user_data["quality"] = value

        await q.edit_message_text(
            text=f"⚡ تم التحديث: {value}",
        )

    elif q.data == "back":
        await q.edit_message_text("🏠 Main Menu")


# ==========================
# BOT START
# ==========================
def main():
    # init db safely
    init_db()

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    # ==========================
    # CORE HANDLERS
    # ==========================
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
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
    # LOGS
    # ==========================
    print("=" * 55)
    print(f"🤖 BOT: {BOT_USERNAME}")
    print("🚀 STATUS: PRODUCTION MODE ACTIVE")
    print(f"⏱ STARTED: {START_TIME}")
    print("=" * 55)

    # ==========================
    # RUN BOT
    # ==========================
    app.run_polling()


if __name__ == "__main__":
    main()
