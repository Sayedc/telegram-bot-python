# handlers/message.py
import asyncio

from config import ADMIN_IDS
from core import rate_limiter
from database.user_repository import (
    add_user,
    block_user,
    get_all_users,
    get_user,
    unblock_user,
)
from handlers.download import handle_download
from handlers.menu import display_name, handle_menu_button
from keyboards.main_keyboard import match_menu_button
from security import is_blocked
from utils import texts as T
from utils.helpers import extract_link

CANCEL_WORD = "إلغاء"


async def _reply(update, text):
    await update.message.reply_text(text, parse_mode="HTML")


async def _handle_admin_state(update, context, state, text):
    """Admin conversation steps (broadcast / block / unblock)."""
    if text.strip() == CANCEL_WORD:
        context.user_data.pop("admin_state", None)
        await _reply(update, T.ACTION_CANCELLED)
        return

    if state == "broadcast":
        sent = 0
        for uid in get_all_users():
            try:
                await context.bot.send_message(int(uid), text)
                sent += 1
            except Exception:  # noqa: BLE001
                pass
            await asyncio.sleep(0.05)  # stay under Telegram's ~30 msg/s limit
        context.user_data.pop("admin_state", None)
        await _reply(update, f"<b>✅ تم إرسال الإعلان</b>\nعدد المستلمين: <b>{sent}</b>")
        return

    # block / unblock
    target = text.strip()
    if not target.isdigit():
        await _reply(update, "⚠️ أرسل <b>ID</b> رقمي صحيح، أو اكتب «إلغاء».")
        return

    if state == "block":
        block_user(target)
        done = "<b>✅ تم تقييد المستخدم.</b>"
    else:
        unblock_user(target)
        done = "<b>✅ تم رفع التقييد عن المستخدم.</b>"

    context.user_data.pop("admin_state", None)
    await _reply(update, done)


async def handle_message(update, context):
    user = update.effective_user
    if not user or not update.message or not update.message.text:
        return

    user_id = user.id
    text = update.message.text
    is_admin = user_id in ADMIN_IDS

    # Admin conversation states (only admins can ever have one).
    state = context.user_data.get("admin_state") if is_admin else None
    if state in ("broadcast", "block", "unblock"):
        await _handle_admin_state(update, context, state, text)
        return

    if not is_admin and is_blocked(user_id):
        await _reply(update, T.BLOCKED)
        return

    # Persistent keyboard buttons arrive as plain text messages.
    action = match_menu_button(text)
    if action:
        await handle_menu_button(update, context, action)
        return

    url = extract_link(text)
    if not url:
        await _reply(update, T.NO_LINK)
        return

    # Users who never pressed /start were not registered, so their downloads
    # were never counted and the block feature could not reach them.
    if not get_user(user_id):
        add_user(user_id, display_name(user))

    if not is_admin:
        allowed, wait, _remaining = rate_limiter.is_allowed(user_id)
        if not allowed:
            await _reply(update, T.rate_limited(wait))
            return

    await handle_download(update, context)
