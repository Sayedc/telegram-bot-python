# handlers/download.py
import os
from datetime import datetime

from config import SIGNATURE
from core import downloader, metrics, rate_limiter
from utils.helpers import extract_link, get_platform
from utils.messages import get_random_processing_text, get_random_success_text, get_random_error_text
from database.user_repository import increase_downloads
from services.tiktok import download_tiktok
from services.youtube import download_youtube
from services.facebook import download_facebook
from services.instagram import download_instagram


async def handle_download(update, context):
    """
    معالج التحميل الأساسي
    """
    user = update.effective_user

    # استخراج الرابط
    url = extract_link(update.message.text)

    if not url:
        await update.message.reply_text("❌ أرسل رابط صحيح")
        return

    # تحديد المنصة
    platform = get_platform(url)

    # إعدادات التحميل
    quality = context.user_data.get("quality", "720")
    audio = context.user_data.get("audio", False)

    # رسالة التحميل
    msg = await update.message.reply_text(
        f"{get_random_processing_text()}\n📱 {platform}"
    )

    start_time = datetime.now()

    try:
        # اختيار الخدمة المناسبة
        result = None

        if platform == "TikTok":
            result = await download_tiktok(url, quality, audio)
        elif platform == "YouTube":
            result = await download_youtube(url, quality, audio)
        elif platform == "Facebook":
            result = await download_facebook(url, quality, audio)
        elif platform == "Instagram":
            result = await download_instagram(url, quality, audio)
        else:
            # محاولة عامة
            from services.yt_service import get_audio_only
            result = await get_audio_only(url) if audio else await download_youtube(url, quality, audio)

        # التحقق من النتيجة
        if not result or not result.get("success"):
            error_msg = result.get("error", "Unknown error")
            await msg.edit_text(f"❌ {error_msg}")
            return

        # إرسال الملف
        file_path = result.get("file_path")
        title = result.get("title", "Media")
        file_size = os.path.getsize(file_path) / 1048576

        if audio:
            with open(file_path, "rb") as f:
                await update.message.reply_audio(
                    f,
                    title=title[:50],
                    caption=f"{get_random_success_text()}\n\n{SIGNATURE}",
                )
        else:
            with open(file_path, "rb") as f:
                await update.message.reply_video(
                    f,
                    caption=f"🎬 {title[:60]}\n📦 {file_size:.1f} MB\n⚡ {quality}p\n📱 {platform}\n\n{SIGNATURE}",
                    supports_streaming=True,
                )

        # تنظيف الملف
        os.remove(file_path)

        # تحديث الإحصائيات
        increase_downloads(user.id)

        # تسجيل المقاييس
        elapsed = (datetime.now() - start_time).total_seconds()
        metrics.record_download(elapsed, platform, user.id)

        # حذف رسالة التحميل
        await msg.delete()

    except Exception as e:
        error_text = get_random_error_text()
        await msg.edit_text(f"❌ {error_text}\n```\n{str(e)[:100]}\n```")
