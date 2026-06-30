# handlers/message.py
import os
from datetime import datetime

from config import SIGNATURE
from core import downloader, metrics, rate_limiter
from utils.helpers import extract_link, get_platform
from utils.messages import get_random_processing_text, get_random_success_text, get_random_error_text
from database.user_repository import increase_downloads


async def handle_message(update, context):
    user = update.effective_user

    url = extract_link(update.message.text)

    if not url:
        await update.message.reply_text("❌ أرسل رابط صحيح")
        return

    platform = get_platform(url)
    quality = context.user_data.get("quality", "720")
    audio = context.user_data.get("audio", False)

    msg = await update.message.reply_text(
        f"{get_random_processing_text()}\n📱 {platform}"
    )

    start_time = datetime.now()

    try:
        result = await downloader.download(url, quality, audio)

        if not result or not result.get("success"):
            error_msg = result.get("error", "Unknown error")
            await msg.edit_text(f"❌ {error_msg}")
            return

        file_path = result.get("file_path")
        title = result.get("title", "Media")

        if not os.path.exists(file_path):
            await msg.edit_text("❌ الملف غير موجود بعد التحميل")
            return

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

        os.remove(file_path)
        increase_downloads(user.id)

        elapsed = (datetime.now() - start_time).total_seconds()
        metrics.record_download(elapsed, platform, user.id)

        await msg.delete()

    except Exception as e:
        await msg.edit_text(f"❌ حدث خطأ أثناء التحميل\n```\n{str(e)[:100]}\n```")
