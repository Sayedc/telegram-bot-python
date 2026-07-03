# handlers/message.py
import os
import asyncio
import traceback
from datetime import datetime

from config import SIGNATURE, ADMIN_IDS
from core import downloader, metrics
from utils.helpers import extract_link, get_platform
from utils.messages import get_random_processing_text, get_random_success_text, get_random_error_text
from database.user_repository import increase_downloads


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

    msg = await update.message.reply_text(
        f"🔄 جاري التحميل...\n📱 {platform}\n⏳ يرجى الانتظار..."
    )

    start_time = datetime.now()

    try:
        result = await downloader.download(url, quality, audio)

        print("=" * 60)
        print("DOWNLOAD RESULT:")
        print(result)
        print("=" * 60)

        if not result:
            await msg.edit_text("❌ Downloader returned None")
            return

        if not result.get("success"):
            await msg.edit_text(
                f"❌ {result.get('error', 'Unknown error')}\n"
                f"Code: {result.get('error_code', 'UNKNOWN')}"
            )

            await send_admin_error(
                context,
                user_id,
                url,
                platform,
                result.get("error"),
                result.get("error_code"),
            )
            return

        file_path = result["file_path"]
        title = result.get("title", "Media")

        print("FILE PATH:", file_path)
        print("FILE EXISTS:", os.path.exists(file_path))

        if not os.path.isfile(file_path):
            await msg.edit_text("❌ الملف غير موجود بعد التحميل")
            return

        file_size = os.path.getsize(file_path) / 1048576
        print("FILE SIZE:", file_size, "MB")

        try:
            if audio:
                with open(file_path, "rb") as f:
                    await update.message.reply_audio(
                        audio=f,
                        title=title,
                        caption=f"{get_random_success_text()}\n\n{SIGNATURE}",
                    )
            else:
                with open(file_path, "rb") as f:
                    await update.message.reply_video(
                        video=f,
                        caption=f"🎬 {title[:60]}\n📦 {file_size:.1f} MB\n⚡ {quality}p\n📱 {platform}\n\n{SIGNATURE}",
                        supports_streaming=True,
                    )

            print("✅ FILE SENT SUCCESSFULLY")

        except Exception as send_error:
            print("SEND ERROR:", repr(send_error))
            raise

        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass

        increase_downloads(user.id)

        elapsed = (datetime.now() - start_time).total_seconds()
        metrics.record_download(elapsed, platform, user.id)

        await msg.delete()

    except asyncio.TimeoutError:
        await msg.edit_text("❌ استغرق التحميل وقتاً طويلاً")

        await send_admin_error(
            context,
            user_id,
            url,
            platform,
            "Timed out",
            "TIMEOUT",
            traceback.format_exc(),
        )

    except Exception as e:
        print("FATAL ERROR:", repr(e))
        traceback.print_exc()

        await msg.edit_text(f"❌ حدث خطأ أثناء التحميل\n\n{str(e)[:200]}")

        await send_admin_error(
            context,
            user_id,
            url,
            platform,
            str(e),
            "EXCEPTION",
            traceback.format_exc(),
            )
