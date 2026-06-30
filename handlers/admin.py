import os
import asyncio
import json
import shutil
from datetime import datetime

from config import SIGNATURE, DOWNLOADS_PATH
from downloader import downloader
from metrics import metrics
from database.user_repository import (
    get_users,
    block_user,
    unblock_user
)

from security import get_failed_stats


# لازم تكون الدوال دي موجودة في main أو utils (هنظبطها بعدين)
from main import (
    is_admin,
    get_uptime,
    get_top_users,
    DB_FILE
)


async def admin_stats(update, context):
    if not is_admin(update.effective_user.id):
        return

    with open(DB_FILE, 'r') as f:
        data = json.load(f)

    blocked_count = sum(1 for u in data["users"].values() if u.get("blocked", False))
    downloader_stats = downloader.get_stats()

    await update.message.reply_text(
        f"👑 إحصائيات البوت\n"
        f"👥 المستخدمين: {len(data['users'])}\n"
        f"🚫 محظورين: {blocked_count}\n"
        f"📥 إجمالي التحميلات: {data['total']}\n"
        f"📈 اليوم: {data['daily']}\n"
        f"⏱️ وقت التشغيل: {get_uptime()}\n\n"
        f"📊 تحميلات:\n"
        f"⏳ قائمة الانتظار: {downloader_stats['queue_size']}\n"
        f"⚡ نشط: {downloader_stats['active']}\n"
        f"✅ نجاح: {downloader_stats['success']}\n"
        f"❌ فشل: {downloader_stats['failed']}\n\n"
        f"{SIGNATURE}",
        parse_mode='Markdown'
    )


async def admin_top(update, context):
    if not is_admin(update.effective_user.id):
        return

    top_users = get_top_users(10)

    if not top_users:
        await update.message.reply_text("لا يوجد مستخدمين")
        return

    text = "🏆 ترتيب المستخدمين\n\n"

    for i, (uid, info) in enumerate(top_users, 1):
        status = "🚫" if info.get("blocked", False) else "✅"
        text += f"{i}- {uid} {status} - {info.get('downloads', 0)} تحميل\n"

    await update.message.reply_text(text)


async def broadcast_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return

    msg = ' '.join(context.args)

    if not msg:
        await update.message.reply_text("اكتب الرسالة")
        return

    users = get_users()
    sent = 0

    for uid in users:
        try:
            await context.bot.send_message(int(uid), msg)
            sent += 1
            await asyncio.sleep(0.05)
        except:
            pass

    await update.message.reply_text(f"تم الإرسال لـ {sent} مستخدم")


async def users_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return

    with open(DB_FILE, 'r') as f:
        data = json.load(f)

    text = "المستخدمين:\n"

    for uid, info in list(data["users"].items())[:30]:
        text += f"{uid} - {info.get('downloads', 0)}\n"

    await update.message.reply_text(text)


async def clear_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return

    count = 0

    for f in os.listdir(DOWNLOADS_PATH):
        try:
            os.remove(os.path.join(DOWNLOADS_PATH, f))
            count += 1
        except:
            pass

    await update.message.reply_text(f"تم حذف {count} ملف")


async def delete_all_users_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return

    admin_id = str(update.effective_user.id)

    with open(DB_FILE, 'w') as f:
        json.dump({
            "users": {
                admin_id: {
                    "name": "admin",
                    "first_seen": str(datetime.now()),
                    "last_seen": str(datetime.now()),
                    "downloads": 0,
                    "fav_platform": "None",
                    "platforms": {},
                    "blocked": False
                }
            },
            "total": 0,
            "daily": 0,
            "last_date": str(datetime.now().date())
        }, f, indent=2)

    await update.message.reply_text("تم حذف كل المستخدمين")


async def uptime_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return

    await update.message.reply_text(get_uptime())


async def backup_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return

    backup_file = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    shutil.copy(DB_FILE, backup_file)

    await update.message.reply_document(open(backup_file, 'rb'))

    os.remove(backup_file)


async def block_user_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return

    if not context.args:
        await update.message.reply_text("block <user_id>")
        return

    user_id = context.args[0]

    block_user(user_id)
    await update.message.reply_text("تم الحظر")


async def unblock_user_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return

    if not context.args:
        await update.message.reply_text("unblock <user_id>")
        return

    user_id = context.args[0]

    unblock_user(user_id)
    await update.message.reply_text("تم فك الحظر")


async def admin_metrics_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return

    summary = metrics.get_summary()
    downloader_stats = downloader.get_stats()
    failed_stats = get_failed_stats()

    await update.message.reply_text(
        f"📊 إحصائيات\n"
        f"⏱️ استجابة: {summary['avg_response']}\n"
        f"📥 تحميل: {summary['avg_download']}\n"
        f"📈 نجاح: {summary['success_rate']}\n"
        f"⚠️ أخطاء: {summary['common_error']}\n"
        f"⏳ Queue: {downloader_stats['queue_size']}\n"
        f"❌ Fail: {downloader_stats['failed']}\n"
        f"🚫 Blocked: {failed_stats['blocked_users']}\n"
  )
