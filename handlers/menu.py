# handlers/menu.py
"""
شاشات القائمة. نفس الشاشة بتتعرض بطريقتين:
  * كرسالة جديدة (الكيبورد الثابت أو الأوامر)  -> reply_text
  * بتعديل رسالة موجودة (أزرار Inline)           -> edit_message_text
عشان كده كل شاشة بترجّع (نص، كيبورد).
"""

from telegram import InlineKeyboardMarkup

from config import ADMIN_IDS
from database.user_repository import get_settings, get_user, get_user_stats, set_setting
from keyboards.main_keyboard import (
    admin_panel as admin_panel_keyboard,
    close_row,
    quality_keyboard,
    settings_keyboard,
)
from security import is_blocked
from utils import texts as T


def is_admin(user_id):
    return user_id in ADMIN_IDS


def display_name(user):
    return user.username or user.first_name or "Unknown"


def quality_screen(user_id):
    s = get_settings(user_id)
    return T.quality_menu(s["quality"], s["mode"]), quality_keyboard(s["quality"])


def settings_screen(user_id, bot_username=None):
    return T.settings_menu(get_settings(user_id)), settings_keyboard(bot_username)


def stats_screen(user_id):
    user = get_user(user_id) or {}
    return (
        T.stats(get_user_stats(user_id), user.get("joined", "")),
        InlineKeyboardMarkup([close_row()]),
    )


def help_screen():
    return T.help_text(), InlineKeyboardMarkup([close_row()])


def admin_screen():
    return T.admin_panel(), admin_panel_keyboard()


async def _reply(update, text, markup=None):
    await update.effective_message.reply_text(
        text, parse_mode="HTML", reply_markup=markup
    )


async def handle_menu_button(update, context, key):
    """Handle a press on the persistent keyboard (or the matching command)."""
    user = update.effective_user
    uid = user.id

    if key in ("video", "audio"):
        set_setting(uid, "mode", key, display_name(user))
        await _reply(update, T.mode_saved(key, get_settings(uid)["quality"]))

    elif key == "quality":
        text, markup = quality_screen(uid)
        await _reply(update, text, markup)

    elif key == "settings":
        text, markup = settings_screen(uid, context.bot.username)
        await _reply(update, text, markup)

    elif key == "stats":
        text, markup = stats_screen(uid)
        await _reply(update, text, markup)

    elif key == "help":
        text, markup = help_screen()
        await _reply(update, text, markup)

    elif key == "admin":
        if not is_admin(uid):
            await _reply(update, T.NOT_AUTHORIZED)
            return
        text, markup = admin_screen()
        await _reply(update, text, markup)


def _command(key):
    async def handler(update, context):
        if not is_admin(update.effective_user.id) and is_blocked(update.effective_user.id):
            await _reply(update, T.BLOCKED)
            return
        await handle_menu_button(update, context, key)

    handler.__name__ = f"{key}_command"
    return handler


help_cmd = _command("help")
quality_cmd = _command("quality")
settings_cmd = _command("settings")
mystats_cmd = _command("stats")
