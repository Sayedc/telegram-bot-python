import asyncio

from config import SIGNATURE, DOWNLOADS_PATH
from core import downloader, metrics
from metrics import metrics

from database.user_repository import (
    get_users,
    block_user,
    unblock_user,
)

# لازم تكون موجودة في main (هنستوردها وقت التشغيل)
try:
    from main import is_admin, get_uptime, START_TIME
except:
    is_admin = lambda x: False
    get_uptime = lambda: "Unknown"


# ==========================
# Helpers
# ==========================
def safe_get_stats():
    try:
        return downloader.get_stats()
    except:
        return {
            "queue_size": 0,
            "active": 0,
            "success": 0,
            "failed": 0,
        }


# ==========================
# STATS
# ==========================
async def admin_stats(update, context):
    if not is_admin(update.effective_user.id):
        return

    users = get_users()
    blocked = sum(1 for u in users.values() if u.get("blocked"))

    stats = safe_get_stats()

    text = f"""
✨✨ 𝓐𝓵𝓱𝓪𝔀𝔂 ADMIN PANEL ✨✨

👑 BOT STATUS: ACTIVE
⏱️ Uptime: {get_uptime()}

👥 Users: {len(users)}
🚫 Blocked: {blocked}

📥 Downloads:
• Queue: {stats['queue_size']}
• Active: {stats['active']}
• Success: {stats['success']}
• Failed: {stats['failed']}

━━━━━━━━━━━━━━
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

    if not sorted_users:
        await update.message.reply_text("🚫 No users yet")
        return

    text = "🏆 TOP USERS\n\n"

    for i, (uid, info) in enumerate(sorted_users, 1):
        status = "🚫" if info.get("blocked") else "✅"
        text += f"{i}. {uid} {status} | {info.get('downloads', 0)} downloads\n"

    text += f"\n{SIGNATURE}"

    await update.message.reply_text(text)


# ==========================
# BROADCAST
# ==========================
async def broadcast_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return

    msg = " ".join(context.args)

    if not msg:
        await update.message.reply_text("⚠️ Send message text")
        return

    users = get_users()

    sent = 0

    for uid in users:
        try:
            await context.bot.send_message(chat_id=int(uid), text=msg)
            sent += 1
            await asyncio.sleep(0.05)
        except:
            pass

    await update.message.reply_text(f"✅ Sent to {sent} users")


# ==========================
# USERS LIST
# ==========================
async def users_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return

    users = get_users()

    text = "👥 USERS LIST\n\n"

    for i, (uid, info) in enumerate(list(users.items())[:30], 1):
        text += f"{i}. {uid} | {info.get('downloads', 0)} downloads\n"

    text += f"\n{SIGNATURE}"

    await update.message.reply_text(text)


# ==========================
# CLEAR FILES
# ==========================
async def clear_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return

    import os

    count = 0

    for f in os.listdir(DOWNLOADS_PATH):
        try:
            os.remove(os.path.join(DOWNLOADS_PATH, f))
            count += 1
        except:
            pass

    await update.message.reply_text(f"🧹 Deleted {count} files")


# ==========================
# BLOCK / UNBLOCK
# ==========================
async def block_user_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return

    if not context.args:
        await update.message.reply_text("Usage: block <user_id>")
        return

    block_user(context.args[0])
    await update.message.reply_text("🚫 User blocked")


async def unblock_user_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return

    if not context.args:
        await update.message.reply_text("Usage: unblock <user_id>")
        return

    unblock_user(context.args[0])
    await update.message.reply_text("✅ User unblocked")


# ==========================
# METRICS
# ==========================
async def admin_metrics_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return

    summary = metrics.get_summary()
    stats = safe_get_stats()

    text = f"""
📊 SYSTEM METRICS

⚡ Response: {summary['avg_response']}s
📥 Download: {summary['avg_download']}s
📈 Success Rate: {summary['success_rate']}%

🔥 Active Users: {summary['active_users']}
⚠️ Common Error: {summary['common_error']}

📦 Queue: {stats['queue_size']}
❌ Failed: {stats['failed']}

━━━━━━━━━━━━━━
{SIGNATURE}
"""

    await update.message.reply_text(text)
