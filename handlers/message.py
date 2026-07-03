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


def progress_bar(step: int):
    bars = [
        "⬛⬜⬜⬜⬜⬜",
        "⬛⬛⬜⬜⬜⬜",
        "⬛⬛⬛⬜⬜⬜",
        "⬛⬛⬛⬛⬜⬜",
        "⬛⬛⬛⬛⬛⬜",
        "⬛⬛⬛⬛⬛⬛",
    ]
    return bars[min(step, len(bars) - 1)]


# ===== شاشة التحميل المتحركة =====
LOADING_STEPS = [
    ("🔍 جاري التحضير", 0),
    ("🌐 جاري الاتصال", 1),
    ("📥 جاري التحميل", 2),
    ("⚙️ جاري المعالجة", 3),
    ("✨ إنهاء العملية", 4),
]


async def animate_loading(message, platform):
    i = 0
    while True:
        step = LOADING_STEPS[i % len(LOADING_STEPS)]

        text = (
            "━━━━━━━━━━━━━━━━━━\n\n"
            f"{platform_icon(platform)}\n\n"
            f"{step[0]}\n\n"
            f"{progress_bar(step[1])}\n\n"
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

    # ===== كارت البداية =====
    msg = await update.message.reply_text(
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"{platform_icon(platform)}\n\n"
        "🔍 جاري التحضير...\n\n"
        "⬛⬜⬜⬜⬜⬜\n\n"
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
                "━━━━━━━━━━━━━━━━━━\n\n"
                "⚠️ حدث خطأ أثناء التحميل\n"
                "حاول مرة أخرى\n\n"
                f"{SIGNATURE}"
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
                "━━━━━━━━━━━━━━━━━━\n\n"
                "⚠️ حدث خطأ أثناء التحميل\n"
                "حاول مرة أخرى\n\n"
                f"{SIGNATURE}"
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

        # ===== رسالة إنهاء العملية =====
        size_mb = round(file_size, 2)
        await msg.edit_text(
            "━━━━━━━━━━━━━━━━━━\n\n"
            "✨ إنهاء العملية\n\n"
            f"📦 {size_mb} MB\n"
            f"🎞️ {quality}P\n\n"
            f"{SIGNATURE}"
        )

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
            "━━━━━━━━━━━━━━━━━━\n\n"
            "⚠️ حدث خطأ أثناء التحميل\n"
            "حاول مرة أخرى\n\n"
            f"{SIGNATURE}"
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
            "━━━━━━━━━━━━━━━━━━\n\n"
            "⚠️ حدث خطأ أثناء التحميل\n"
            "حاول مرة أخرى\n\n"
            f"{SIGNATURE}"
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
