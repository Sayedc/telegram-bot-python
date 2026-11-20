import asyncio
import os
from datetime import datetime

from config import DOWNLOADS_PATH
from core import metrics, get_uptime, is_admin
from database.user_repository import (
    DB_FILE,
    block_user,
    get_admin_stats,
    get_users,
    unblock_user,
)
from services.common import cleanup_stale
from utils import texts as T


async def _reply(update, text):
    await update.message.reply_text(text, parse_mode="HTML")


# ==========================
# STATS
# ==========================
async def admin_stats(update, context):
    if not is_admin(update.effective_user.id):
        return
    await _reply(update, T.admin_stats(get_admin_stats(), get_uptime()))


# ==========================
# TOP USERS
# ==========================
async def admin_top(update, context):
    if not is_admin(update.effective_user.id):
        return

    ranked = sorted(
        get_users().items(),
        key=lambda item: item[1].get("downloads", 0),
        reverse=True,
    )[:10]
    await _reply(update, T.admin_top(ranked))


# ==========================
# BROADCAST
# ==========================
async def broadcast_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return

    msg = " ".join(context.args)
    if not msg:
        await _reply(update, "<b>📢 إعلان للجميع</b>\nالاستخدام: <code>/broadcast النص</code>")
        return

    sent = 0
    for uid in get_users():
        try:
            await context.bot.send_message(int(uid), msg)
            sent += 1
        except Exception:  # noqa: BLE001
            pass
        await asyncio.sleep(0.05)

    await _reply(update, f"<b>✅ تم إرسال الإعلان</b>\nعدد المستلمين: <b>{sent}</b>")


# ==========================
# USERS LIST
# ==========================
async def users_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return

    users = list(get_users().items())
    lines = [
        f"{i}. <code>{T.esc(uid)}</code>  •  {info.get('downloads', 0)} تحميل"
        for i, (uid, info) in enumerate(users[:30], 1)
    ]
    body = "\n".join(lines) or "لا يوجد مستخدمون بعد."
    more = f"\n\n<i>عرض أول 30 من أصل {len(users)}</i>" if len(users) > 30 else ""
    await _reply(update, f"<b>👥 المستخدمون</b>\n{T.SEP}\n{body}{more}")


# ==========================
# CLEAR DOWNLOADS
# ==========================
async def clear_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return

    # Entries younger than 10 minutes may belong to a download in progress.
    count = cleanup_stale(DOWNLOADS_PATH, max_age=600)
    await _reply(update, f"<b>🧹 اكتمل التنظيف</b>\nتم حذف <b>{count}</b> عنصر (الأقدم من 10 دقائق).")


# ==========================
# BACKUP
# ==========================
async def backup_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return

    if not os.path.exists(DB_FILE):
        await _reply(update, "<b>ℹ️ لا توجد قاعدة بيانات بعد.</b>")
        return

    name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(DB_FILE, "rb") as src:
        await update.message.reply_document(document=src, filename=name, caption="📦 نسخة احتياطية")


# ==========================
# BLOCK / UNBLOCK
# ==========================
async def block_user_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return

    if not context.args:
        await _reply(update, "<b>🚫 تقييد مستخدم</b>\nالاستخدام: <code>/block ID</code>")
        return

    if not context.args[0].isdigit():
        await _reply(update, "⚠️ يجب أن يكون <b>ID</b> رقماً.")
        return

    block_user(context.args[0])
    await _reply(update, "<b>✅ تم تقييد المستخدم.</b>")


async def unblock_user_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return

    if not context.args:
        await _reply(update, "<b>🔓 رفع التقييد</b>\nالاستخدام: <code>/unblock ID</code>")
        return

    if not context.args[0].isdigit():
        await _reply(update, "⚠️ يجب أن يكون <b>ID</b> رقماً.")
        return

    unblock_user(context.args[0])
    await _reply(update, "<b>✅ تم رفع التقييد عن المستخدم.</b>")


# ==========================
# METRICS
# ==========================
async def admin_metrics_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return
    await _reply(update, T.admin_metrics(metrics.get_summary()))
