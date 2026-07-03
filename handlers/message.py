# handlers/message.py
import os
import asyncio
import traceback
from datetime import datetime

from config import SIGNATURE, ADMIN_IDS
from core import downloader, metrics
from utils.helpers import extract_link, get_platform
from utils.messages import get_random_success, get_error
from database.user_repository import increase_downloads
from utils.loading import LoadingMessage
from utils.signature import SIGNATURE


# ===== شاشة التحميل المتحركة =====
LOADING_STEPS = [
    ("🔍 جاري التحضير", "▰▱▱▱▱"),
    ("🌐 جاري الاتصال", "▰▰▱▱▱"),
    ("📥 جاري التحميل", "▰▰▰▱▱"),
    ("⚙️ جاري المعالجة", "▰▰▰▰▱"),
    ("✨ إنهاء العملية", "▰▰▰▰▰"),
]


def format_platform(name):
    icons = {
        "youtube": "▶️ 𝗬𝗼𝘂𝗧𝘂𝗯𝗲",
        "tiktok": "🎵 𝗧𝗶𝗸𝗧𝗼𝗸",
        "facebook": "📘 𝗙𝗮𝗰𝗲𝗯𝗼𝗼𝗸",
        "instagram": "📸 𝗜𝗻𝘀𝘁𝗮𝗴𝗿𝗮𝗺",
    }
    return icons.get(name.lower(), f"▶️ 𝗔𝗹𝗹")


async def animate_loading(message, platform):
    i = 0
    while True:
        step = LOADING_STEPS[i % len(LOADING_STEPS)]

        text = (
            f"{step[0]}\n\n"
            f"{format_platform(platform)}\n\n"
            f"{step[1]}\n\n"
            f"{SIGNATURE}"
        )

        try:
            await message.edit_text(text)
        except:
            pass

        i += 1
        await asyncio.sleep(1.5)


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

    if not url:
        await update.message.reply_text("❌ أرسل رابط صحيح")
        return

    platform = get_platform(url)
    quality = context.user_data.get("quality", "720")
    audio = context.user_data.get("audio", False)

    # ===== رد سريع أولي =====
    await update.message.reply_text("⚡ جاري تحليل الرابط...")

    # ===== شاشة التحميل المتحركة =====
    msg = await update.message.reply_text(
        "🔍 جاري التحضير...\n\n"
        f"{format_platform(platform)}\n\n"
        "▰▱▱▱▱\n"
        f"{SIGNATURE}"
    )

    task = asyncio.create_task(animate_loading(msg, platform))

    start_time = datetime.now()

    try:
        try:
            result = await downloader.download(url, quality, audio)
        finally:
            task.cancel()

        print("=" * 60)
        print("DOWNLOAD RESULT:")
        print(result)
        print("=" * 60)

        if not result or not result.get("success"):
            error_msg = result.get("error", "Unknown error")
            error_code = result.get("error_code", "UNKNOWN_ERROR")

            await msg.edit_text(
                f"{get_error(error_code)}\n\n{SIGNATURE}"
            )

            await send_admin_error(
                context,
                user_id,
                url,
                platform,
                error_msg,
                error_code
            )
            return

        file_path = result.get("file_path")
        title = result.get("title", "Media")

        print("FILE PATH:", file_path)

        if file_path:
            print("FILE EXISTS:", os.path.exists(file_path))

            if os.path.exists(file_path):
                print("FILE SIZE:", os.path.getsize(file_path))

        if not file_path or not os.path.exists(file_path):
            await msg.edit_text(
                f"{get_error('FILE_NOT_FOUND')}\n\n{SIGNATURE}"
            )
            
            await send_admin_error(
                context,
                user_id,
                url,
                platform,
                "File not found after download",
                "FILE_NOT_FOUND"
            )
            return

        file_size = os.path.getsize(file_path) / 1048576

        try:
            if audio:
                with open(file_path, "rb") as f:
                    await update.message.reply_audio(
                        audio=f,
                        title=title[:50],
                        caption=f"{get_random_success()}\n\n{SIGNATURE}",
                    )
            else:
                with open(file_path, "rb") as f:
                    await update.message.reply_video(
                        video=f,
                        caption=f"🎬 {title[:60]}\n📦 {file_size:.1f} MB\n⚡ {quality}p\n📱 {platform}\n\n{SIGNATURE}",
                        supports_streaming=True,
                    )

            try:
                await msg.delete()
            except:
                pass

            print("✅ FILE SENT SUCCESS")

        except Exception as send_error:
            print("SEND ERROR:")
            print(repr(send_error))
            raise

        os.remove(file_path)
        increase_downloads(user.id)

        elapsed = (datetime.now() - start_time).total_seconds()
        metrics.record_download(elapsed, platform, user.id)

    except asyncio.TimeoutError:
        await msg.edit_text(
            f"❌ استغرق التحميل وقتاً طويلاً، جرب تاني\n\n{SIGNATURE}"
        )
        await send_admin_error(
            context,
            user_id,
            url,
            platform,
            "Timed out",
            "TIMEOUT",
            traceback.format_exc()
        )

    except Exception as e:
        print("=" * 60)
        print("FATAL ERROR")
        print(repr(e))
        traceback.print_exc()
        print("=" * 60)

        await msg.edit_text(
            f"❌ حدث خطأ أثناء التحميل\n\n{str(e)[:150]}\n\n{SIGNATURE}"
        )

        await send_admin_error(
            context,
            user_id,
            url,
            platform,
            str(e),
            "EXCEPTION",
            traceback.format_exc()
        )
