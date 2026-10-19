# handlers/message.py
import os
import re
import asyncio
import traceback
from datetime import datetime
from urllib.parse import urlsplit

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from config import SIGNATURE, ADMIN_IDS
from core import metrics
from utils.helpers import extract_link, get_platform
from utils.messages import get_random_success, get_error
from database.user_repository import increase_downloads
from handlers.download import handle_download


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


developer_button = InlineKeyboardMarkup([
    [InlineKeyboardButton("👨‍💻 تواصل مع المطور", url="https://t.me/ALHAWY1")]
])


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
        "PHOTO_DEPENDENCY_MISSING": "📦",
        "PHOTO_DOWNLOAD_FAILED": "🖼️",
    }
    emoji = error_emojis.get(error_code, "❌")
    advice_map = {
        "TIMEOUT": "⏰ التحميل استغرق وقتاً طويلاً. جرب رابط آخر أو جودة أقل.",
        "COOKIES_REQUIRED": "🍪 المنصة طلبت تسجيل دخول. تحقق من ملف الكوكيز.",
        "COOKIES_ERROR": "🍪 ملف الكوكيز تالف أو منتهي الصلاحية. استخدم ملفًا صالحًا.",
        "PRIVATE_VIDEO": "🔒 المنشور خاص. استخدم رابط منشور عام.",
        "VIDEO_UNAVAILABLE": "🚫 المنشور غير متاح أو تم حذفه.",
        "AGE_RESTRICTED": "🔞 المنشور مقيد بالعمر.",
        "FORMAT_NOT_AVAILABLE": "📹 الجودة المطلوبة غير متاحة. جرب جودة أقل.",
        "RATE_LIMIT": "⏳ تم تجاوز حد التحميل. انتظر قليلًا وحاول مجددًا.",
        "IP_BLOCKED": "🌐 قد يكون عنوان IP الخاص بالسيرفر محظورًا مؤقتًا.",
        "FFMPEG_MISSING": "🎬 تأكد من تثبيت FFmpeg على السيرفر.",
        "INVALID_URL": "❌ الرابط غير صحيح أو غير مدعوم.",
        "FILE_NOT_FOUND": "📁 الملف الناتج غير موجود.",
        "PHOTO_DEPENDENCY_MISSING": "📦 أضف gallery-dl إلى requirements.txt ثم أعد النشر.",
        "PHOTO_DOWNLOAD_FAILED": "🖼️ تعذر استخراج صور المنشور. حدّث gallery-dl وجرب مجددًا.",
    }
    advice = advice_map.get(error_code, "🔄 جرب رابطًا آخر أو حاول مرة أخرى.")
    error_report = (
        f"{emoji} *تقرير خطأ في التحميل* {emoji}\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        f"👤 *المستخدم:* `{user_id}`\n"
        f"📱 *المنصة:* {platform}\n"
        f"🔗 *الرابط:* `{url[:100]}`\n\n"
        f"❌ *الخطأ:* {error_msg}\n"
        f"📋 *كود الخطأ:* `{error_code or 'UNKNOWN'}`\n"
        f"⏱️ *التوقيت:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        f"💡 *نصيحة:* {advice}\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        f"✨ {SIGNATURE} ✨"
    )
    if tb:
        # Avoid breaking Markdown code fences with untrusted exception text.
        safe_tb = str(tb).replace("`", "'")[:500]
        error_report += f"\n📄 *التفاصيل:*\n```\n{safe_tb}\n```"

    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(admin_id, error_report, parse_mode="Markdown")
        except Exception as exc:
            print(f"Failed to send error to admin {admin_id}: {exc}")


async def handle_message(update, context):
    user = update.effective_user
    if not user or not update.message or not update.message.text:
        return

    user_id = user.id
    message_text = update.message.text
    url = extract_link(message_text)

    # If a copied TikTok URL was split by whitespace, normalize only the extracted URL.
    if url:
        try:
            host = urlsplit(url.strip()).netloc.lower()
        except Exception:
            host = ""
        if host.endswith("tiktok.com"):
            url = re.sub(r"\s+", "", url.strip())

    state = context.user_data.get("admin_state")

    if state == "broadcast":
        if message_text.strip().lower() == "إلغاء":
            context.user_data.pop("admin_state", None)
            await update.message.reply_text("❌ تم إلغاء العملية.")
            return

        from database.user_repository import get_all_users
        users = get_all_users()
        sent = 0
        for uid in users:
            try:
                await context.bot.send_message(int(uid), message_text)
                sent += 1
            except Exception:
                pass
        context.user_data.pop("admin_state", None)
        await update.message.reply_text(f"✅ تم إرسال الإعلان إلى {sent} مستخدم.")
        return

    if state == "block":
        from database.user_repository import block_user
        block_user(message_text.strip())
        context.user_data.pop("admin_state", None)
        await update.message.reply_text("✅ تم حظر المستخدم.")
        return

    if state == "unblock":
        from database.user_repository import unblock_user
        unblock_user(message_text.strip())
        context.user_data.pop("admin_state", None)
        await update.message.reply_text("✅ تم إلغاء الحظر.")
        return

    if not url:
        await update.message.reply_text("❌ أرسل رابط صحيح")
        return

    await handle_download(update, context)
