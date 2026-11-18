import os
import asyncio
import json
import shutil
from datetime import datetime

from config import SIGNATURE, DOWNLOADS_PATH

from database.user_repository import (
    get_users,
    block_user,
    unblock_user,
    DB_FILE,
)
from services.common import cleanup_stale

from core import metrics, rate_limiter, get_uptime
from core import is_admin


# ==========================
# STATS
# ==========================
async def admin_stats(update, context):
    if not is_admin(update.effective_user.id):
        return

    users = get_users()
    blocked = sum(1 for u in users.values() if u.get("blocked"))

    text = f"""
👑 ADMIN DASHBOARD

👥 Users: {len(users)}
🚫 Blocked: {blocked}

⏱ Uptime: {get_uptime()}

━━━━━━━━━━━━
{SIGNATURE}
"""

    await update.message.reply_text(text)


# ==========================
# TOP USERS
# ==========================
async def admin_top(update, context):
    if not is_admin(update.effective_user.id):
        return

    users = get_users()

    sorted_users = sorted(
        users.items(),
        key=lambda x: x[1].get("downloads", 0),
        reverse=True
    )[:10]

    text = "🏆 TOP USERS\n\n"

    for i, (uid, info) in enumerate(sorted_users, 1):
        status = "🚫" if info.get("blocked") else "✅"
        text += f"{i}. {uid} {status} | {info.get('downloads', 0)}\n"

    await update.message.reply_text(text)


# ==========================
# BROADCAST
# ==========================
async def broadcast_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return

    msg = " ".join(context.args)

    if not msg:
        await update.message.reply_text("Usage: /broadcast message")
        return

    users = get_users()
    sent = 0

    for uid in users:
        try:
            await context.bot.send_message(int(uid), msg)
            sent += 1
            await asyncio.sleep(0.05)
        except Exception:
            pass

    await update.message.reply_text(f"Sent to {sent} users")


# ==========================
# USERS LIST
# ==========================
async def users_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return

    users = get_users()

    text = "👥 USERS\n\n"

    for i, (uid, info) in enumerate(list(users.items())[:30], 1):
        text += f"{i}. {uid} | {info.get('downloads', 0)} downloads\n"

    await update.message.reply_text(text)


# ==========================
# CLEAR DOWNLOADS
# ==========================
async def clear_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return

    # Entries younger than 10 minutes may belong to a download in progress.
    count = cleanup_stale(DOWNLOADS_PATH, max_age=600)

    await update.message.reply_text(f"Deleted {count} items (older than 10 min)")


# ==========================
# BACKUP
# ==========================
async def backup_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return

    if not os.path.exists(DB_FILE):
        await update.message.reply_text("No database file yet.")
        return

    backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    with open(DB_FILE, "rb") as src:
        await update.message.reply_document(document=src, filename=backup_name)


# ==========================
# BLOCK / UNBLOCK
# ==========================
async def block_user_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return

    if not context.args:
        await update.message.reply_text("Usage: /block user_id")
        return

    if not context.args[0].isdigit():
        await update.message.reply_text("user_id must be a number")
        return

    block_user(context.args[0])
    await update.message.reply_text("User blocked")


async def unblock_user_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return

    if not context.args:
        await update.message.reply_text("Usage: /unblock user_id")
        return

    if not context.args[0].isdigit():
        await update.message.reply_text("user_id must be a number")
        return

    unblock_user(context.args[0])
    await update.message.reply_text("User unblocked")


# ==========================
# METRICS
# ==========================
async def admin_metrics_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return

    summary = metrics.get_summary()

    await update.message.reply_text(
        f"""
📊 SYSTEM METRICS

Uptime: {get_uptime()}
Downloads: {summary['total_downloads']}
Success rate: {summary['success_rate']}%
Avg download: {summary['avg_download']}s
Top platform: {summary['top_platform']}
Most common error: {summary['common_error']}

━━━━━━━━━━━━
{SIGNATURE}
"""
    )
