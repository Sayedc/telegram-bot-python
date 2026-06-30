# main.py - Clean Production Version

import os
import asyncio
from datetime import datetime

from telegram.ext import (
    Application,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

# ========== handlers ==========
from handlers.start import start
from handlers.message import handle_message
#from handlers.admin import *

# ========== keyboards ==========
from keyboards.main_keyboard import *

# ========== config ==========
from config import BOT_TOKEN, ADMIN_IDS, DOWNLOADS_PATH

# ========== system ==========
from downloader import Downloader
downloader = Downloader(DOWNLOADS_PATH)
from metrics import Metrics
from rate_limiter import RateLimiter

# ========== database ==========
from database.user_repository import init_db

# ==========================
# helpers
# ==========================
def is_admin(user_id):
    return user_id in ADMIN_IDS


# ==========================
# instances
# ==========================
downloader = Downloader(DOWNLOADS_PATH, max_concurrent=3)
metrics = Metrics()
rate_limiter = RateLimiter(max_requests=10, time_window=60)

START_TIME = datetime.now()
SIGNATURE = "✨ BOT ✨"


# ==========================
# init folder
# ==========================
os.makedirs(DOWNLOADS_PATH, exist_ok=True)


# ==========================
# downloader startup
# ==========================
async def post_init(app):
    await downloader.start()


# ==========================
# callback handler
# ==========================
async def callback(update, context):
    q = update.callback_query
    await q.answer()

    user_id = update.effective_user.id

    if q.data.startswith("q_"):
        value = q.data[2:]

        if value == "audio":
            context.user_data["audio"] = True
            await q.edit_message_text("🎵 Audio mode ON")
        else:
            context.user_data["quality"] = value
            context.user_data["audio"] = False
            await q.edit_message_text(f"⚡ Quality: {value}p")

    elif q.data == "back":
        kb = admin_keyboard() if is_admin(user_id) else main_keyboard()
        await q.edit_message_text("🏠 Main Menu", reply_markup=kb)


# ==========================
# bot main
# ==========================
def main():
    init_db()

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    # handlers
    app.add_handler(CallbackQueryHandler(callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("=" * 40)
    print("BOT STARTED SUCCESSFULLY")
    print("=" * 40)

    app.run_polling()


# ==========================
# run
# ==========================
if __name__ == "__main__":
    main()
