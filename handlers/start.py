from telegram import Update
from telegram.ext import ContextTypes

from database.user_repository import add_user, update_last_seen
from keyboards.main_keyboard import main_keyboard, admin_keyboard
from utils.messages import WELCOME_RESPONSES, get_response
from security import is_blocked
from config import ADMIN_IDS
from utils.signature import SIGNATURE


# ==========================
# ADMIN CHECK
# ==========================
def is_admin(user_id):
    return user_id in ADMIN_IDS


# ==========================
# START HANDLER
# ==========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user

    # 🚫 blocked users
    if is_blocked(u.id):
        await update.message.reply_text("🚫 لقد تم حظرك")
        return

    # 📌 save user
    add_user(u.id, u.username)
    update_last_seen(u.id)

    # ==========================
    # CLEAN MESSAGE (FIXED)
    # ==========================
    text = (
        "🖤 أهلاً  ،! 🖤\n\n"
        "✨ ✨ 𝓐𝓵𝓱𝓪𝔀𝔂 ✨ ✨\n\n"
        "🌍 البوت بينزل أي حاجة من أي موقع\n\n"
        "📌 المنصات المدعومة:\n"
        "• TikTok • YouTube • Instagram\n"
        "• Facebook • Twitter • SoundCloud\n"
        "• Spotify • Deezer • وأي موقع\n\n"
        "🔥 أرسل أي رابط وسأقوم بالتحميل\n\n"
        "📌 البوت شغال على كل المواقع\n\n"
        f"{get_response(WELCOME_RESPONSES, u.first_name)}"
    )

    # 🎯 keyboard
    kb = admin_keyboard() if is_admin(u.id) else main_keyboard()

    await update.message.reply_text(
        text,
        reply_markup=kb
    )
