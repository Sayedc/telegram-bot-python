# main.py - البوت الفاخر النهائي (منظم واحترافي)

import os
import re
import json
import asyncio
import random
import shutil
from datetime import datetime

import yt_dlp

from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

# ========= handlers =========
from handlers.start import start
from handlers.message import handle_message
from handlers.admin import *

# ========= keyboards =========
from keyboards.main_keyboard import *

# ========= config =========
from config import BOT_TOKEN, ADMIN_IDS, DOWNLOADS_PATH

# ========= system modules =========
from downloader import Downloader
from metrics import Metrics
from rate_limiter import RateLimiter

# ========= database =========
from database.user_repository import *

# ==========================
# helper functions
# ==========================
def is_admin(user_id):
    return user_id in ADMIN_IDS


# ==========================
# Downloader instance
# ==========================
downloader = Downloader(DOWNLOADS_PATH, max_concurrent=3)
metrics = Metrics()
rate_limiter = RateLimiter(max_requests=10, time_window=60)

# ==========================
# Init download folder
# ==========================
if os.path.isfile(DOWNLOADS_PATH):
    os.remove(DOWNLOADS_PATH)

os.makedirs(DOWNLOADS_PATH, exist_ok=True)

START_TIME = datetime.now()

SIGNATURE = "✨ 𝓐𝓵𝓱𝓪𝔀𝔂 ✨"


# ==========================
# post_init (تشغيل downloader)
# ==========================
async def post_init(app):
    await downloader.start()


# ==========================
# Callback Handler
# ==========================
async def callback(update, context):
    q = update.callback_query
    await q.answer()

    user_id = update.effective_user.id

    if q.data.startswith("q_"):
        val = q.data[2:]

        if val == "audio":
            context.user_data["audio"] = True
            await q.edit_message_text("🎵 وضع الصوت مفعل")

        else:
            context.user_data["quality"] = val
            context.user_data["audio"] = False
            await q.edit_message_text(f"⚡ الجودة {val}p")

    elif q.data == "back":
        kb = admin_keyboard() if is_admin(user_id) else main_keyboard()
        await q.edit_message_text("🖤 القائمة الرئيسية", reply_markup=kb)


# ==========================
# Bot Startup
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
    app.add_handler(CallbackQueryHandler(callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("=" * 50)
    print("✨ BOT STARTED ✨")
    print(f"👑 ADMINS: {ADMIN_IDS}")
    print("🚀 READY")
    print("=" * 50)

    app.run_polling()


# ==========================
# run
# ==========================
if __name__ == "__main__":
    main()    app.add_handler(CallbackQueryHandler(callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("=" * 50)
    print("✨ BOT STARTED ✨")
    print(f"👑 ADMINS: {ADMIN_IDS}")
    print("🚀 READY")
    print("=" * 50)

    app.run_polling()


# ==========================
# run
# ==========================
if __name__ == "__main__":
    main()
