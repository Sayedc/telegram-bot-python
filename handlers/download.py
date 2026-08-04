# handlers/download.py - النسخة النهائية (مع إصلاح إرسال الخطأ)

import os
from datetime import datetime

from config import SIGNATURE
from core import metrics
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
            # محاولة عامة (YouTube fallback)
            result = await download_youtube(url, quality, audio)

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
                    audio=f,
                    title=title[:80],
                    caption=f"{get_random_success_text()}\n\n{SIGNATURE}",
                    read_timeout=300,
                    write_timeout=300,
                )
        else:
            with open(file_path, "rb") as f:
                await update.message.reply_video(
                    video=f,
                    caption=(
                        f"🎬 {title[:80]}\n"
                        f"📦 {file_size:.2f} MB\n"
                        f"🎥 الجودة: {quality}p\n"
                        f"📱 {platform}\n\n"
                        f"{SIGNATURE}"
                    ),
                    supports_streaming=True,
                    read_timeout=300,
                    write_timeout=300,
                    connect_timeout=60,
                    pool_timeout=60,
                )

        # تنظيف الملف بأمان
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass

        # تحديث الإحصائيات
        increase_downloads(user.id)

        # تسجيل المقاييس
        elapsed = (datetime.now() - start_time).total_seconds()
        metrics.record_download(elapsed, platform, user.id)

        # حذف رسالة التحميل
        await msg.delete()

    except Exception as e:
        error_text = get_random_error_text()
        # استخدام parse_mode=None لمنع تنسيق Markdown
        await msg.edit_text(
            f"❌ {error_text}\n\n{str(e)[:300]}",
            parse_mode=None
            )
