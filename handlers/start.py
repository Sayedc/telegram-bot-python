from telegram import Update
from telegram.ext import ContextTypes

from config import ADMIN_IDS
from database.user_repository import add_user, update_last_seen
from keyboards.main_keyboard import main_reply_keyboard
from security import is_blocked
from utils import texts as T


# ==========================
# START HANDLER
# ==========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    is_admin = u.id in ADMIN_IDS

    if not is_admin and is_blocked(u.id):
        await update.message.reply_text(T.BLOCKED, parse_mode="HTML")
        return

    add_user(u.id, u.username or u.first_name or "Unknown")
    update_last_seen(u.id)

    # القائمة الثابتة بتظهر جنب خانة الكتابة وتفضل موجودة طول الوقت.
    await update.message.reply_text(
        T.welcome(u.first_name or u.username or ""),
        parse_mode="HTML",
        reply_markup=main_reply_keyboard(is_admin),
    )
