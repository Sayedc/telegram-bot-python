# handlers/callback.py
import io
import os
import sys
from datetime import datetime

from telegram.error import BadRequest
from telegram.ext import ContextTypes

from config import ADMIN_IDS, DOWNLOADS_PATH
from core import metrics, get_uptime
from database.user_repository import (
    DB_FILE,
    delete_user_data,
    get_admin_stats,
    get_all_users,
    get_settings,
    load_data,
    save_data,
    set_setting,
)
from handlers.menu import (
    admin_screen,
    display_name,
    quality_screen,
    settings_screen,
)
from keyboards.main_keyboard import (
    admin_back_keyboard,
    admin_confirm_delete_keyboard,
    back_to_settings_keyboard,
    confirm_keyboard,
    confirm_reposts_keyboard,
)
from security import is_blocked
from services.common import cleanup_stale
from utils import texts as T

VALID_QUALITIES = {"144", "240", "360", "480", "720", "1080"}


def is_admin(user_id: int):
    return user_id in ADMIN_IDS


def _restart_process():
    """Restart the bot in place (works on any host, unlike exit code 0 which
    Railway/Docker restart policies treat as a normal shutdown)."""
    try:
        sys.stdout.flush()
        sys.stderr.flush()
        os.execv(sys.executable, [sys.executable] + sys.argv)
    except Exception:  # noqa: BLE001
        os._exit(1)


async def _edit(query, text, markup=None):
    """edit_message_text that ignores 'message is not modified' (double taps)."""
    try:
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=markup)
    except BadRequest as exc:
        if "not modified" not in str(exc).lower():
            raise


async def callback_handler(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    user = query.from_user
    user_id = user.id
    admin = is_admin(user_id)

    if not admin and is_blocked(user_id):
        await _edit(query, T.BLOCKED)
        return

    # =========================
    # القوائم العامة
    # =========================
    if data == "menu_close":
        try:
            await query.message.delete()
        except Exception:  # noqa: BLE001
            pass

    elif data == "menu_settings":
        text, markup = settings_screen(user_id, context.bot.username)
        await _edit(query, text, markup)

    elif data == "menu_quality":
        text, markup = quality_screen(user_id)
        await _edit(query, text, markup)

    elif data.startswith("q_"):
        quality = data[2:]
        if quality not in VALID_QUALITIES:
            return
        name = display_name(user)
        set_setting(user_id, "quality", quality, name)
        set_setting(user_id, "mode", "video", name)
        await _edit(query, T.quality_saved(quality), back_to_settings_keyboard())

    elif data == "mode_toggle":
        current = get_settings(user_id)["mode"]
        new_mode = "audio" if current == "video" else "video"
        set_setting(user_id, "mode", new_mode, display_name(user))
        text, markup = settings_screen(user_id, context.bot.username)
        await _edit(query, text, markup)

    elif data == "menu_privacy":
        await _edit(query, T.privacy(), back_to_settings_keyboard())

    elif data == "menu_delete":
        await _edit(query, T.delete_data_confirm(), confirm_keyboard())

    elif data == "confirm_yes":
        deleted = delete_user_data(user_id)
        await _edit(query, T.DATA_DELETED if deleted else T.DATA_NOT_FOUND)

    elif data == "confirm_no":
        await _edit(query, T.ACTION_CANCELLED)

    # =========================
    # حذف ريبوستات TikTok
    # =========================
    elif data == "delete_reposts":
        await _edit(query, T.REPOST_INTRO, confirm_reposts_keyboard())

    elif data == "confirm_delete_reposts":
        from services.tiktok_repost import repost_manager

        # A double tap used to start two browsers and leak the first one.
        if context.user_data.get("repost_busy"):
            await query.message.reply_text(T.REPOST_BUSY)
            return

        context.user_data["repost_busy"] = True

        try:
            await _edit(query, T.REPOST_PREPARING)

            qr_path = await repost_manager.start_login(user_id)

            if not qr_path or not os.path.exists(qr_path):
                await _edit(query, T.REPOST_QR_FAILED)
                return

            with open(qr_path, "rb") as f:
                await query.message.reply_photo(
                    photo=f, caption=T.REPOST_QR_CAPTION, parse_mode="HTML"
                )

            await query.message.reply_text(T.REPOST_WAITING, parse_mode="HTML")

            logged_in = await repost_manager.wait_login(user_id, timeout=180)

            if not logged_in:
                await query.message.reply_text(T.REPOST_TIMEOUT, parse_mode="HTML")
                return

            await query.message.reply_text(T.REPOST_LOGGED_IN, parse_mode="HTML")

            result = await repost_manager.delete_reposts(user_id)

            if result.get("success"):
                await query.message.reply_text(
                    T.repost_done(result.get("deleted", 0)), parse_mode="HTML"
                )
            else:
                await query.message.reply_text(
                    T.repost_failed(result.get("error", "خطأ غير معروف")),
                    parse_mode="HTML",
                )

        finally:
            # Always close the browser + virtual display, even after an error.
            context.user_data.pop("repost_busy", None)
            await repost_manager.cleanup(user_id)

    # =========================
    # لوحة الأدمن
    # =========================
    elif data.startswith("admin_"):
        if not admin:
            return
        await _admin_action(query, context, data, user_id)

    else:
        await query.message.reply_text(T.UNKNOWN_BUTTON)


async def _admin_action(query, context, data, user_id):
    back = admin_back_keyboard()

    if data == "admin_panel":
        text, markup = admin_screen()
        await _edit(query, text, markup)

    elif data == "admin_stats":
        await _edit(query, T.admin_stats(get_admin_stats(), get_uptime()), back)

    elif data == "admin_top":
        users = sorted(
            get_all_users().items(),
            key=lambda item: item[1].get("downloads", 0),
            reverse=True,
        )[:10]
        await _edit(query, T.admin_top(users), back)

    elif data == "admin_broadcast":
        context.user_data["admin_state"] = "broadcast"
        await _edit(query, T.ADMIN_BROADCAST_PROMPT)

    elif data == "admin_block":
        context.user_data["admin_state"] = "block"
        await _edit(query, T.ADMIN_BLOCK_PROMPT)

    elif data == "admin_unblock":
        context.user_data["admin_state"] = "unblock"
        await _edit(query, T.ADMIN_UNBLOCK_PROMPT)

    elif data == "admin_users":
        users = get_all_users()
        lines = [
            f"{uid} | {info.get('name')} | {info.get('downloads', 0)}"
            for uid, info in users.items()
        ]
        payload = io.BytesIO(("\n".join(lines) or "no users").encode("utf-8"))
        await query.message.reply_document(
            document=payload,
            filename="users.txt",
            caption="👥 قائمة المستخدمين",
        )

    elif data == "admin_clear":
        # Entries younger than 10 minutes may belong to a download in progress.
        count = cleanup_stale(DOWNLOADS_PATH, max_age=600)
        await _edit(
            query,
            f"<b>🧹 اكتمل التنظيف</b>\nتم حذف <b>{count}</b> عنصر (الأقدم من 10 دقائق).",
            back,
        )

    elif data == "admin_delete_all":
        await _edit(query, T.ADMIN_DELETE_ALL_CONFIRM, admin_confirm_delete_keyboard())

    elif data == "admin_delete_all_yes":
        data_db = load_data()
        admin_record = data_db["users"].get(str(user_id))

        # Keep the admin's own record only if it exists.
        data_db["users"] = {str(user_id): admin_record} if admin_record else {}
        data_db["total"] = len(data_db["users"])
        save_data(data_db)

        await _edit(query, "<b>✅ تم حذف جميع المستخدمين.</b>", back)

    elif data == "admin_uptime":
        await _edit(
            query,
            f"<b>⏱️ مدة التشغيل</b>\n{T.SEP}\n<b>{T.esc(get_uptime())}</b>",
            back,
        )

    elif data == "admin_backup":
        if not os.path.exists(DB_FILE):
            await _edit(query, "<b>ℹ️ لا توجد قاعدة بيانات بعد.</b>", back)
            return

        name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(DB_FILE, "rb") as src:
            await query.message.reply_document(
                document=src, filename=name, caption="📦 نسخة احتياطية"
            )
        await _edit(query, "<b>✅ تم إرسال النسخة الاحتياطية.</b>", back)

    elif data == "admin_metrics":
        await _edit(query, T.admin_metrics(metrics.get_summary()), back)

    elif data == "admin_logs":
        log_file = os.path.join("logs", "errors.log")

        if not os.path.exists(log_file):
            await _edit(query, "<b>ℹ️ لا يوجد سجل أخطاء.</b>", back)
            return

        with open(log_file, "r", encoding="utf8", errors="replace") as f:
            tail = "".join(f.readlines()[-10:])[-3300:] or "السجل فارغ."

        await _edit(
            query,
            f"<b>📋 آخر الأخطاء</b>\n{T.SEP}\n<pre>{T.esc(tail)}</pre>",
            back,
        )

    elif data == "admin_restart":
        await _edit(query, "<b>🔄 جارٍ إعادة تشغيل البوت…</b>\nسيستغرق ذلك بضع ثوانٍ.")
        _restart_process()
