from telegram import Update
from telegram.ext import ContextTypes

from config import BOT_TOKEN, ADMIN_IDS
from database.user_repository import add_user, update_last_seen
from utils.keyboards import admin_keyboard, main_keyboard
from utils.messages import WELCOME_RESPONSES, get_response
from security import is_blocked
from config import ADMIN_IDS


def is_admin(user_id):
    return user_id in ADMIN_IDS


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user

    if is_blocked(u.id):
        await update.message.reply_text(
            "🚫 *لقد تم حظرك*",
            parse_mode="Markdown"
        )
        return

    add_user(u.id, u.username)
    update_last_seen(u.id)

    text = f"""
🖤 *أهلاً {u.first_name}!*

✨ {SIGNATURE} ✨

🌍 *البوت بينزل أي حاجة من أي موقع*

📌 *المنصات المدعومة:*
• TikTok
• YouTube
• Instagram
• Facebook
• Twitter
• SoundCloud
• Spotify
• Deezer

🔥 *أرسل أي رابط وسأقوم بتحميله*

{get_response(WELCOME_RESPONSES, u.first_name)}
"""

    kb = admin_keyboard() if is_admin(u.id) else main_keyboard()

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=kb
    )
