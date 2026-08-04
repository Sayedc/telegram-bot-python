# handlers/message.py
import os
import asyncio
import traceback
from datetime import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from config import SIGNATURE, ADMIN_IDS
from core import metrics
from utils.helpers import extract_link, get_platform
from utils.messages import get_random_success, get_error
from database.user_repository import increase_downloads
from handlers.download import handle_download


# ===== Helper Functions =====
def platform_icon(platform: str):
    if "youtube" in platform.lower():
        return "▶️ 𝗬𝗼𝘂𝗧𝘂𝗯𝗲"
    if "tiktok" in platform.lower():
        return "🎵 𝗧𝗶𝗸𝗧𝗼𝗸"
    if "facebook" in platform.lower():
        return "📘 𝗙𝗮𝗰𝗲𝗯𝗼𝗼𝗸"
    if "instagram" in platform.lower():
        return "📸 𝗜𝗻𝘀𝘁𝗮𝗴𝗿𝗮𝗺"
    return "▶️ 𝗠𝗲𝗱𝗶𝗮"


# ===== زر المطور =====
developer_button = InlineKeyboardMarkup([
    [InlineKeyboardButton("👨‍💻 تواصل مع المطور", url="https://t.me/ALHAWY1")]
])


# ===== رسالة الترحيب =====
async def start(update, context):
    await update.message.reply_text(
        "━━━━━━━━━━━━━━━━━━\n\n"
        "🤖 𝗔𝗹𝗵𝗮𝘄𝘆 𝗗𝗼𝘄𝗻𝗹𝗼𝗮𝗱𝗲𝗿\n\n"
        "⚡ Fast • Clean • Unlimited\n\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "📎 أرسل أي رابط...\n\n"
        "━━━━━━━━━━━━━━━━━━"
    )


async def send_admin_error(context, user_id, url, platform, error_msg, error_code=None, tb=None):
    """إرسال تقرير خطأ مفصل للأدمن"""
    
    error_emojis = {
        "TIMEOUT": "⏰",
        "COOKIES_REQUIRED": "🍪",
        "COOKIES_ERROR": "🍪",
        "PRIVATE_VIDEO": "🔒",
        "VIDEO_UNAVAILABLE": "🚫",
        "AGE_RESTRICTED": "🔞",
        "FORMAT_NOT_AVAILABLE": "📹",
        "RATE_LIMIT": "⏳",
        "IP_BLOCKED": "🌐",
        "FFMPEG_MISSING": "🎬",
        "INVALID_URL": "❌",
        "FILE_NOT_FOUND": "📁",
        "DOWNLOAD_ERROR": "⚠️",
        "UNKNOWN_ERROR": "💔",
        "EXCEPTION": "💥",
    }
    
    emoji = error_emojis.get(error_code, "❌")
    
    advice_map = {
        "TIMEOUT": "⏰ التحميل استغرق وقتاً طويلاً. جرب رابط آخر أو جودة أقل.",
        "COOKIES_REQUIRED": "🍪 يوتيوب طلب تسجيل دخول. حمّل ملف cookies.txt وارفعه على GitHub.",
        "COOKIES_ERROR": "🍪 ملف الكوكيز تالف أو منتهي الصلاحية. جيب كوكيز جديدة.",
        "PRIVATE_VIDEO": "🔒 الفيديو خاص. استخدم رابط فيديو عام.",
        "VIDEO_UNAVAILABLE": "🚫 الفيديو غير متاح (اتحذف أو اتغيرت صلاحياته).",
        "AGE_RESTRICTED": "🔞 الفيديو مقيد بعمر. استخدم حساب مسجل الدخول.",
        "FORMAT_NOT_AVAILABLE": "📹 الجودة المطلوبة غير متاحة. جرب جودة أقل.",
        "RATE_LIMIT": "⏳ تم تجاوز حد التحميل. انتظر شوية وحاول تاني.",
        "IP_BLOCKED": "🌐 الـ IP بتاع السيرفر محظور من المنصة. جرب بعد فترة.",
        "FFMPEG_MISSING": "🎬 FFmpeg مش موجود. تأكد من تثبيته على السيرفر.",
        "INVALID_URL": "❌ الرابط غير صحيح أو غير مدعوم.",
        "FILE_NOT_FOUND": "📁 الملف لم يتم تحميله بنجاح.",
    }
    
    advice = advice_map.get(error_code, "🔄 جرب رابط آخر أو حاول مرة أخرى.")
    
    error_report = f"""
{emoji} *تقرير خطأ في التحميل* {emoji}
━━━━━━━━━━━━━━━━━━━
👤 *المستخدم:* `{user_id}`
📱 *المنصة:* {platform}
🔗 *الرابط:* `{url[:100]}...`

❌ *الخطأ:* {error_msg}
📋 *كود الخطأ:* `{error_code or "UNKNOWN"}`

⏱️ *التوقيت:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
━━━━━━━━━━━━━━━━━━━
💡 *نصيحة:* {advice}
━━━━━━━━━━━━━━━━━━━
✨ {SIGNATURE} ✨
"""

    if tb:
        error_report += f"\n📄 *التفاصيل:*\n```\n{tb[:500]}\n```"

    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                admin_id,
                error_report,
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"Failed to send error to admin {admin_id}: {e}")


async def handle_message(update, context):
    user = update.effective_user
    user_id = user.id

    url = extract_link(update.message.text)

    # ==========================
    # ADMIN STATES
    # ==========================

    state = context.user_data.get("admin_state")

    if state == "broadcast":

        if update.message.text.lower() == "إلغاء":
            context.user_data.pop("admin_state", None)
            await update.message.reply_text("❌ تم إلغاء العملية.")
            return

        from database.user_repository import get_all_users

        users = get_all_users()

        sent = 0

        for uid in users:

            try:
                await context.bot.send_message(
                    int(uid),
                    update.message.text
                )
                sent += 1

            except:
                pass

        context.user_data.pop("admin_state", None)

        await update.message.reply_text(
            f"✅ تم إرسال الإعلان إلى {sent} مستخدم."
        )

        return


    if state == "block":

        from database.user_repository import block_user

        block_user(update.message.text)

        context.user_data.pop("admin_state", None)

        await update.message.reply_text(
            "✅ تم حظر المستخدم."
        )

        return


    if state == "unblock":

        from database.user_repository import unblock_user

        unblock_user(update.message.text)

        context.user_data.pop("admin_state", None)

        await update.message.reply_text(
            "✅ تم إلغاء الحظر."
        )

        return

    # ===== استخدام handle_download =====
    if not url:
        await update.message.reply_text("❌ أرسل رابط صحيح")
        return

    # تفويض التحميل إلى handle_download
    await handle_download(update, context)
