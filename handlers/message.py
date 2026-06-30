import os
from datetime import datetime

from config import SIGNATURE
from downloader import Downloader
from metrics import Metrics
from security import is_safe_url, record_failed_attempt
from rate_limiter import RateLimiter

from utils.helpers import (
    extract_link,
    get_platform,
    get_video_info,
    get_random_sticker,
    get_random_processing_text,
    get_random_success_text,
    get_random_error_text
)

downloader = Downloader
metrics = Metrics()
rate_limiter = RateLimiter(max_requests=10, time_window=60)


async def handle_message(update, context):
    u = update.effective_user
    start_time = datetime.now()

    url = extract_link(update.message.text)
    quality = context.user_data.get('quality', '720')
    audio = context.user_data.get('audio', False)

    if not url:
        await update.message.reply_text("❌ أرسل رابط صحيح")
        return

    safe, msg = is_safe_url(url)
    if not safe:
        await update.message.reply_text(f"⚠️ {msg}")
        return

    platform = get_platform(url)

    video_info = await get_video_info(url)
    if video_info:
        await update.message.reply_text(
            f"📹 معلومات الفيديو\n"
            f"📝 {video_info['title'][:50]}\n"
            f"⏱️ {video_info['duration']}\n"
            f"📦 {video_info['size']}\n"
            f"📱 {platform}\n"
            f"🔄 جاري التحميل..."
        )

    sticker = get_random_sticker("processing")
    processing_text = get_random_processing_text(u.first_name)

    s = await update.message.reply_text(
        f"{sticker} {processing_text}\n📱 {platform}"
    )

    download_start = datetime.now()

    try:
        position = await downloader.add_to_queue(
            url, quality, audio, u.id
        )

        path, title = await downloader._download_media(
            url, quality, audio
        )

        size = os.path.getsize(path) / 1048576

        elapsed = (datetime.now() - download_start).total_seconds()
        metrics.record_download(elapsed, platform, u.id)

        if audio:
            with open(path, 'rb') as f:
                await update.message.reply_audio(
                    f,
                    title=title[:50],
                    caption=get_random_success_text()
                )
        else:
            with open(path, 'rb') as f:
                await update.message.reply_video(
                    f,
                    caption=f"🎬 {title[:60]}\n📦 {size:.1f} MB\n⚡ {quality}p\n📱 {platform}\n\n{SIGNATURE}",
                    supports_streaming=True
                )

        os.remove(path)
        await s.delete()

    except Exception as e:
        metrics.record_error(str(e)[:50], u.id)
        blocked, msg = record_failed_attempt(u.id, url)

        if blocked:
            await s.edit_text(f"🚫 {msg}")
        else:
            await s.edit_text("❌ حصل خطأ أثناء التحميل")
