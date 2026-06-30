import os
import asyncio
import json
import shutil
from datetime import datetime

from config import SIGNATURE, DOWNLOADS_PATH

from database.user_repository import (
    get_users,
    block_user,
    unblock_user
)

from core import downloader, metrics

from main import is_admin, get_uptime


# ==========================
# STATS
# ==========================
async def admin_stats(update, context):
    if not is_admin(update.effective_user.id):
        return

    users = get_users()
    blocked = sum(1 for u in users.values() if u.get("blocked"))

    stats = downloader.get_stats()

    text = f"""
👑 ADMIN DASHBOARD

👥 Users: {len(users)}
🚫 Blocked: {blocked}

📥 Downloads:
• Queue: {stats['queue_size']}
• Active: {stats['active']}
• Success: {stats['success']}
• Failed: {stats['failed']}

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
        except:
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

    count = 0

    for f in os.listdir(DOWNLOADS_PATH):
        try:
            os.remove(os.path.join(DOWNLOADS_PATH, f))
            count += 1
        except:
            pass

    await update.message.reply_text(f"Deleted {count} files")


# ==========================
# BACKUP (FIXED - THIS WAS YOUR ERROR)
# ==========================
async def backup_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return

    backup_file = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    with open("database.json", "rb") as src:
        with open(backup_file, "wb") as dst:
            dst.write(src.read())

    await update.message.reply_document(
        document=open(backup_file, "rb")
    )

    os.remove(backup_file)


# ==========================
# BLOCK / UNBLOCK
# ==========================
async def block_user_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return

    if not context.args:
        await update.message.reply_text("Usage: /block user_id")
        return

    block_user(context.args[0])
    await update.message.reply_text("User blocked")


async def unblock_user_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return

    if not context.args:
        await update.message.reply_text("Usage: /unblock user_id")
        return

    unblock_user(context.args[0])
    await update.message.reply_text("User unblocked")


# ==========================
# METRICS
# ==========================
async def admin_metrics_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return

    stats = downloader.get_stats()

    await update.message.reply_text(
        f"""
📊 SYSTEM METRICS

Queue: {stats['queue_size']}
Active: {stats['active']}
Success: {stats['success']}
Failed: {stats['failed']}

━━━━━━━━━━━━
{SIGNATURE}
"""
    )
