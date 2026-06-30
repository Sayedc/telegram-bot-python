# main.py - PRO VERSION FIXED

import os
from datetime import datetime

from telegram.ext import Application, MessageHandler, CallbackQueryHandler, CommandHandler, filters

# ========== handlers ==========
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

# ========== config ==========
from config import BOT_TOKEN, ADMIN_IDS, DOWNLOADS_PATH

# ========== system ==========
from downloader import Downloader
from metrics import Metrics
from rate_limiter import RateLimiter

# ========== db ==========
from database.user_repository import init_db


# ==========================
# GLOBAL INSTANCES (IMPORTANT FIX)
# ==========================
downloader = Downloader(DOWNLOADS_PATH, max_concurrent=3)
metrics = Metrics()
rate_limiter = RateLimiter(10, 60)

START_TIME = datetime.now()

SIGNATURE = "✨ ✨ 𝓐𝓵𝓱𝓪𝔀𝔂 ✨ ✨"
BOT_USERNAME = "@SK_Download_bot"


# ==========================
# HELPERS
# ==========================
def is_admin(user_id: int):
    return user_id in ADMIN_IDS


def get_uptime():
    delta = datetime.now() - START_TIME
    return str(delta).split('.')[0]


# ==========================
# POST INIT
# ==========================
async def post_init(app):
    await downloader.start()


# ==========================
# CALLBACK HANDLER (FIXED)
# ==========================
async def callback(update, context):
    q = update.callback_query
    await q.answer()

    user_id = update.effective_user.id

    if q.data.startswith("q_"):
        value = q.data[2:]

        context.user_data["audio"] = (value == "audio")
        if value != "audio":
            context.user_data["quality"] = value

        await q.edit_message_text(
            f"⚡ تم التحديث: {value}",
            reply_markup=None
        )

    elif q.data == "back":
        await q.edit_message_text("🏠 الرئيسية")


# ==========================
# BOT START
# ==========================
def main():
    init_db()

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    # ===== handlers =====
    app.add_handler(CommandHandler("start", start))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # ===== callback =====
    app.add_handler(CallbackQueryHandler(callback))

    # ===== ADMIN COMMANDS (FIX IMPORTANT) =====
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
    print("🚀 STATUS: RUNNING PRO MODE")
    print("=" * 50)

    app.run_polling()


if __name__ == "__main__":
    main()
