# handlers/download.py

import os
import asyncio
import shutil
from datetime import datetime

from config import SIGNATURE
from core import metrics

from utils.helpers import extract_link, get_platform
from utils.messages import (
    get_random_processing_text,
    get_random_success_text,
    get_random_error_text,
)

from database.user_repository import increase_downloads

from services.tiktok import download_tiktok
from services.youtube import download_youtube
from services.facebook import download_facebook
from services.instagram import download_instagram


# =========================================================
# Telegram safe upload limit
# =========================================================

# Telegram Bot API limit is around 50 MB.
# We intentionally stay below it to leave some safety margin.
MAX_UPLOAD_SIZE = 49 * 1024 * 1024


# =========================================================
# Helpers
# =========================================================

def get_file_size_mb(file_path: str) -> float:
    """Return file size in MB."""
    try:
        return os.path.getsize(file_path) / (1024 * 1024)
    except Exception:
        return 0.0


def find_ffmpeg():
    """Find FFmpeg executable."""
    return shutil.which("ffmpeg")


async def run_ffmpeg(args):
    """
    Run FFmpeg asynchronously so the bot event loop
    doesn't get blocked.
    """

    process = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await process.communicate()

    return (
        process.returncode,
        stdout.decode(errors="ignore"),
        stderr.decode(errors="ignore"),
    )


async def compress_video(
    input_path: str,
    output_path: str,
    max_height: int = 720,
    video_bitrate: str = "1200k",
    audio_bitrate: str = "96k",
):
    """
    Compress video using FFmpeg.

    H.264 + AAC + MP4
    """

    ffmpeg = find_ffmpeg()

    if not ffmpeg:
        raise RuntimeError("FFmpeg is not installed on the server.")

    command = [
        ffmpeg,

        "-y",

        "-i",
        input_path,

        # Video
        "-c:v",
        "libx264",

        "-preset",
        "veryfast",

        "-b:v",
        video_bitrate,

        "-maxrate",
        video_bitrate,

        "-bufsize",
        "2M",

        # Keep aspect ratio and don't upscale
        "-vf",
        (
            f"scale='if(gt(ih,{max_height}),-2,iw)':"
            f"'if(gt(ih,{max_height}),{max_height},ih)'"
        ),

        # Audio
        "-c:a",
        "aac",

        "-b:a",
        audio_bitrate,

        "-ac",
        "2",

        # MP4 streaming optimization
        "-movflags",
        "+faststart",

        output_path,
    ]

    code, stdout, stderr = await run_ffmpeg(command)

    if code != 0:
        raise RuntimeError(
            f"FFmpeg compression failed:\n{stderr[-1500:]}"
        )

    if not os.path.exists(output_path):
        raise RuntimeError("FFmpeg did not create the output file.")

    return output_path


async def compress_until_small_enough(
    input_path: str,
    status_message=None,
):
    """
    Compress a video progressively until it fits Telegram's
    safe upload size.

    Returns:
        final_file_path
    """

    current_size = get_file_size_mb(input_path)

    if current_size <= MAX_UPLOAD_SIZE / (1024 * 1024):
        return input_path

    base, _ = os.path.splitext(input_path)

    # Compression levels:
    # 1 -> 720p
    # 2 -> 480p
    # 3 -> 360p
    compression_levels = [
        {
            "height": 720,
            "video_bitrate": "1200k",
            "audio_bitrate": "96k",
        },
        {
            "height": 480,
            "video_bitrate": "800k",
            "audio_bitrate": "80k",
        },
        {
            "height": 360,
            "video_bitrate": "550k",
            "audio_bitrate": "64k",
        },
    ]

    original_path = input_path
    generated_files = []

    for index, level in enumerate(compression_levels, start=1):

        output_path = f"{base}_compressed_{index}.mp4"

        generated_files.append(output_path)

        try:

            if status_message:
                try:
                    await status_message.edit_text(
                        "⏳ الفيديو حجمه كبير على تليجرام...\n"
                        f"🗜️ جاري ضغط الفيديو ({index}/3)\n"
                        f"📦 الحجم الحالي: {current_size:.2f} MB"
                    )
                except Exception:
                    pass

            await compress_video(
                original_path,
                output_path,
                max_height=level["height"],
                video_bitrate=level["video_bitrate"],
                audio_bitrate=level["audio_bitrate"],
            )

            new_size = get_file_size_mb(output_path)

            print(
                f"🗜️ Compression {index}: "
                f"{current_size:.2f} MB -> {new_size:.2f} MB"
            )

            if new_size <= MAX_UPLOAD_SIZE / (1024 * 1024):

                # Delete intermediate files except the final one
                for file_path in generated_files:
                    if file_path != output_path:
                        try:
                            if os.path.exists(file_path):
                                os.remove(file_path)
                        except Exception:
                            pass

                return output_path

            # Continue compressing the latest generated file
            original_path = output_path
            current_size = new_size

        except Exception as e:

            print(
                f"❌ Compression level {index} failed: {e}"
            )

            try:
                if os.path.exists(output_path):
                    os.remove(output_path)
            except Exception:
                pass

            break

    # Nothing succeeded
    raise RuntimeError(
        "الفيديو أكبر من الحد المسموح به حتى بعد الضغط."
    )


async def compress_audio_if_needed(
    input_path: str,
    status_message=None,
):
    """
    Compress MP3/audio if it exceeds Telegram safe limit.
    """

    current_size = get_file_size_mb(input_path)

    if current_size <= MAX_UPLOAD_SIZE / (1024 * 1024):
        return input_path

    ffmpeg = find_ffmpeg()

    if not ffmpeg:
        raise RuntimeError("FFmpeg is not installed on the server.")

    base, _ = os.path.splitext(input_path)

    bitrate_levels = [
        "128k",
        "96k",
        "64k",
        "48k",
    ]

    original_path = input_path

    for index, bitrate in enumerate(bitrate_levels, start=1):

        output_path = f"{base}_compressed_{index}.mp3"

        if status_message:
            try:
                await status_message.edit_text(
                    "⏳ الملف الصوتي كبير...\n"
                    f"🗜️ جاري ضغط الصوت ({index}/4)"
                )
            except Exception:
                pass

        command = [
            ffmpeg,
            "-y",

            "-i",
            original_path,

            "-vn",

            "-c:a",
            "libmp3lame",

            "-b:a",
            bitrate,

            output_path,
        ]

        code, stdout, stderr = await run_ffmpeg(command)

        if code != 0:
            print(
                f"❌ Audio compression failed: "
                f"{stderr[-1000:]}"
            )

            try:
                if os.path.exists(output_path):
                    os.remove(output_path)
            except Exception:
                pass

            continue

        if not os.path.exists(output_path):
            continue

        new_size = get_file_size_mb(output_path)

        print(
            f"🎵 Audio compression {index}: "
            f"{current_size:.2f} MB -> {new_size:.2f} MB"
        )

        if new_size <= MAX_UPLOAD_SIZE / (1024 * 1024):

            if original_path != input_path:
                try:
                    if os.path.exists(original_path):
                        os.remove(original_path)
                except Exception:
                    pass

            return output_path

        # Continue from compressed version
        if original_path != input_path:
            try:
                if os.path.exists(original_path):
                    os.remove(original_path)
            except Exception:
                pass

        original_path = output_path
        current_size = new_size

    raise RuntimeError(
        "الملف الصوتي أكبر من الحد المسموح به."
    )


# =========================================================
# Main Download Handler
# =========================================================

async def handle_download(update, context):

    user = update.effective_user

    url = extract_link(update.message.text)

    if not url:
        await update.message.reply_text(
            "❌ أرسل رابط صحيح"
        )
        return

    platform = get_platform(url)

    quality = context.user_data.get(
        "quality",
        "720"
    )

    audio = context.user_data.get(
        "audio",
        False
    )

    # -----------------------------------------------------
    # Processing message
    # -----------------------------------------------------

    msg = await update.message.reply_text(
        f"{get_random_processing_text()}\n"
        f"📱 {platform}"
    )

    start_time = datetime.now()

    file_path = None
    final_file_path = None

    try:

        # -------------------------------------------------
        # Download
        # -------------------------------------------------

        result = None

        if platform == "TikTok":

            result = await download_tiktok(
                url,
                quality,
                audio
            )

        elif platform == "YouTube":

            result = await download_youtube(
                url,
                quality,
                audio
            )

        elif platform == "Facebook":

            result = await download_facebook(
                url,
                quality,
                audio
            )

        elif platform == "Instagram":

            result = await download_instagram(
                url,
                quality,
                audio
            )

        else:

            result = await download_youtube(
                url,
                quality,
                audio
            )

        # -------------------------------------------------
        # Download failed
        # -------------------------------------------------

        if not result or not result.get("success"):

            error_msg = (
                result.get("error", "Unknown error")
                if result
                else "Unknown error"
            )

            await msg.edit_text(
                f"❌ {error_msg}"
            )

            return

        # -------------------------------------------------
        # File information
        # -------------------------------------------------

        file_path = result.get("file_path")

        title = result.get(
            "title",
            "Media"
        )

        if not file_path or not os.path.exists(file_path):

            await msg.edit_text(
                "❌ الملف لم يتم العثور عليه بعد التحميل."
            )

            return

        original_size = get_file_size_mb(
            file_path
        )

        print(
            f"📦 Downloaded file: "
            f"{original_size:.2f} MB"
        )

        # -------------------------------------------------
        # Size protection
        # -------------------------------------------------

        if original_size > (
            MAX_UPLOAD_SIZE / (1024 * 1024)
        ):

            try:

                if audio:

                    final_file_path = (
                        await compress_audio_if_needed(
                            file_path,
                            msg
                        )
                    )

                else:

                    final_file_path = (
                        await compress_until_small_enough(
                            file_path,
                            msg
                        )
                    )

            except Exception as compression_error:

                print(
                    f"❌ Compression error: "
                    f"{compression_error}"
                )

                await msg.edit_text(
                    "❌ الفيديو كبير جدًا لإرساله عبر تليجرام "
                    "حتى بعد محاولة ضغطه.\n\n"
                    "💡 جرّب اختيار جودة أقل مثل 480p أو 360p."
                )

                return

        else:

            final_file_path = file_path

        # -------------------------------------------------
        # Final size check
        # -------------------------------------------------

        if not final_file_path or not os.path.exists(
            final_file_path
        ):

            await msg.edit_text(
                "❌ تعذر تجهيز الملف للإرسال."
            )

            return

        final_size = get_file_size_mb(
            final_file_path
        )

        print(
            f"📤 Final upload size: "
            f"{final_size:.2f} MB"
        )

        if final_size > (
            MAX_UPLOAD_SIZE / (1024 * 1024)
        ):

            await msg.edit_text(
                "❌ حجم الملف ما زال أكبر من الحد المسموح به."
            )

            return

        # -------------------------------------------------
        # Upload
        # -------------------------------------------------

        await msg.edit_text(
            "📤 جاري إرسال الملف...\n"
            f"📦 الحجم: {final_size:.2f} MB"
        )

        if audio:

            with open(
                final_file_path,
                "rb"
            ) as audio_file:

                await update.message.reply_audio(
                    audio=audio_file,

                    title=title[:80],

                    caption=(
                        f"{get_random_success_text()}\n\n"
                        f"📦 {final_size:.2f} MB\n"
                        f"{SIGNATURE}"
                    ),

                    read_timeout=300,
                    write_timeout=300,
                    connect_timeout=60,
                    pool_timeout=60,
                )

        else:

            with open(
                final_file_path,
                "rb"
            ) as video_file:

                await update.message.reply_video(
                    video=video_file,

                    caption=(
                        f"🎬 {title[:80]}\n"
                        f"📦 {final_size:.2f} MB\n"
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

        # -------------------------------------------------
        # Success
        # -------------------------------------------------

        increase_downloads(
            user.id
        )

        elapsed = (
            datetime.now() - start_time
        ).total_seconds()

        metrics.record_download(
            elapsed,
            platform,
            user.id
        )

        try:
            await msg.delete()
        except Exception:
            pass

        print(
            f"✅ Upload completed successfully "
            f"for user {user.id}"
        )

    # -----------------------------------------------------
    # General error
    # -----------------------------------------------------

    except Exception as e:

        print(
            f"❌ HANDLE DOWNLOAD ERROR: {e}"
        )

        try:

            await msg.edit_text(
                f"❌ {get_random_error_text()}\n\n"
                f"{str(e)[:300]}",
                parse_mode=None
            )

        except Exception:
            pass

    # -----------------------------------------------------
    # Cleanup
    # -----------------------------------------------------

    finally:

        # Delete final file
        if (
            final_file_path
            and os.path.exists(final_file_path)
        ):

            try:
                os.remove(final_file_path)
            except Exception:
                pass

        # Delete original file if different
        if (
            file_path
            and file_path != final_file_path
            and os.path.exists(file_path)
        ):

            try:
                os.remove(file_path)
            except Exception:
                pass
