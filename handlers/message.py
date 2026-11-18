# handlers/message.py
import os
import re
import asyncio
import traceback
from datetime import datetime
from urllib.parse import urlsplit

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from config import SIGNATURE, ADMIN_IDS
from core import metrics, rate_limiter
from utils.helpers import extract_link, get_platform
from utils.messages import get_random_success, get_error
from database.user_repository import increase_downloads, add_user, get_user
from security import is_blocked
from handlers.download import handle_download


def platform_icon(platform: str):
    if "youtube" in platform.lower():
        return "▶️ 𝗬𝗼𝘂𝗧𝘂𝗯𝗲"
    if "tiktok" in platform.lower():
        return "🎵 𝗧𝗶𝗸𝗧𝗼𝗸"
    if "facebook" in platform.lower():
        return "📘 𝗙𝗮𝗰𝗲𝗯𝗼𝗼𝗸"
    if "instagram" in platform.lower():
        return "📸 𝗜𝗻𝘀𝘁𝗮𝗴𝗿𝗮𝗺"
    return "▶️ 𝗠𝗲𝗱𝗶𝗮"


developer_button = InlineKeyboardMarkup([
    [InlineKeyboardButton("👨‍💻 تواصل مع المطور", url="https://t.me/ALHAWY1")]
])


async def start(update, context):
    await update.message.reply_text(
        "━━━━━━━━━━━━━━━━━━\n\n"
        "🤖 𝗔𝗹𝗵𝗮𝘄𝘆 𝗗𝗼𝘄𝗻𝗹𝗼𝗮𝗱𝗲𝗿\n\n"
        "⚡ Fast • Clean • Unlimited\n\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "📎 أرسل أي رابط...\n\n"
        "━━━━━━━━━━━━━━━━━━"
    )


async def handle_message(update, context):
    user = update.effective_user
    if not user or not update.message or not update.message.text:
        return

    user_id = user.id
    message_text = update.message.text
    state = context.user_data.get("admin_state") if user_id in ADMIN_IDS else None

    # ------------------------------------------------------------------
    # Admin conversation states (only admins can ever have one)
    # ------------------------------------------------------------------
    if state == "broadcast":
        if message_text.strip().lower() == "إلغاء":
            context.user_data.pop("admin_state", None)
            await update.message.reply_text("❌ تم إلغاء العملية.")
            return

        from database.user_repository import get_all_users
        users = get_all_users()
        sent = 0
        for uid in users:
            try:
                await context.bot.send_message(int(uid), message_text)
                sent += 1
            except Exception:
                pass
            await asyncio.sleep(0.05)  # stay under Telegram's ~30 msg/s limit
        context.user_data.pop("admin_state", None)
        await update.message.reply_text(f"✅ تم إرسال الإعلان إلى {sent} مستخدم.")
        return

    if state in ("block", "unblock"):
        target = message_text.strip()
        if target == "إلغاء":
            context.user_data.pop("admin_state", None)
            await update.message.reply_text("❌ تم إلغاء العملية.")
            return
        if not target.isdigit():
            await update.message.reply_text("❌ ابعت ID رقمي صحيح (أو اكتب إلغاء).")
            return

        if state == "block":
            from database.user_repository import block_user
            block_user(target)
            reply = "✅ تم حظر المستخدم."
        else:
            from database.user_repository import unblock_user
            unblock_user(target)
            reply = "✅ تم إلغاء الحظر."
        context.user_data.pop("admin_state", None)
        await update.message.reply_text(reply)
        return

    # ------------------------------------------------------------------
    # Normal users
    # ------------------------------------------------------------------
    if is_blocked(user_id):
        await update.message.reply_text("🚫 لقد تم حظرك")
        return

    url = extract_link(message_text)
    if not url:
        await update.message.reply_text("❌ أرسل رابط صحيح")
        return

    # Users who never pressed /start were not registered, so their downloads
    # were never counted and the block feature could not reach them.
    if not get_user(user_id):
        add_user(user_id, user.username or user.first_name or "Unknown")

    if user_id not in ADMIN_IDS:
        allowed, wait, _remaining = rate_limiter.is_allowed(user_id)
        if not allowed:
            await update.message.reply_text(
                f"⏳ بتبعت روابط كتير. استنى {wait} ثانية وجرب تاني."
            )
            return

    await handle_download(update, context)
