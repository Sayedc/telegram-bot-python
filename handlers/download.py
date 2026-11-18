import asyncio
import os
import shutil
from datetime import datetime

from config import MAX_CONCURRENT_DOWNLOADS
from core import metrics
from utils.helpers import extract_link, get_platform
from utils import texts as T
from utils.admin_notify import notify_admins
from database.user_repository import get_settings, increase_downloads
from security import is_safe_url
from services.common import remove_path
from services.tiktok import download_tiktok
from services.youtube import download_youtube
from services.facebook import download_facebook
from services.instagram import download_instagram
from services.generic import download_generic

MAX_UPLOAD_SIZE = 49 * 1024 * 1024

# Only N downloads/compressions run at once; everybody else waits in a queue
# instead of exhausting the server's CPU, RAM and disk.
DOWNLOAD_SEMAPHORE = asyncio.Semaphore(MAX_CONCURRENT_DOWNLOADS)


def get_file_size_mb(path):
    try:
        return os.path.getsize(path) / (1024 * 1024)
    except (OSError, TypeError):
        return 0.0


def find_ffmpeg():
    return shutil.which("ffmpeg")


async def run_ffmpeg(args):
    p = await asyncio.create_subprocess_exec(*args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    out, err = await p.communicate()
    return p.returncode, out.decode(errors="ignore"), err.decode(errors="ignore")


async def compress_video(src, dst, height=720, vb="1200k", ab="96k"):
    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        raise RuntimeError("FFmpeg is not installed on the server.")
    args = [ffmpeg, "-y", "-i", src, "-c:v", "libx264", "-preset", "veryfast",
            "-b:v", vb, "-maxrate", vb, "-bufsize", "2M",
            "-vf", f"scale='if(gt(ih,{height}),-2,iw)':'if(gt(ih,{height}),{height},ih)'",
            "-c:a", "aac", "-b:a", ab, "-ac", "2", "-movflags", "+faststart", dst]
    code, _, err = await run_ffmpeg(args)
    if code or not os.path.isfile(dst):
        raise RuntimeError(f"FFmpeg compression failed: {err[-1200:]}")
    return dst


async def compress_until_small_enough(path, status_message=None):
    limit = MAX_UPLOAD_SIZE / (1024 * 1024)
    size = get_file_size_mb(path)
    if size <= limit:
        return path
    base, _ = os.path.splitext(path)
    original = path
    generated = []
    levels = [(720, "1200k", "96k"), (480, "800k", "80k"), (360, "550k", "64k")]
    for i, (height, vb, ab) in enumerate(levels, 1):
        dst = f"{base}_compressed_{i}.mp4"
        generated.append(dst)
        if status_message:
            try: await status_message.edit_text(T.status_compress(i, 3, size), parse_mode="HTML")
            except Exception: pass
        try:
            await compress_video(original, dst, height, vb, ab)
            new_size = get_file_size_mb(dst)
            print(f"🗜️ Compression {i}: {size:.2f} MB -> {new_size:.2f} MB")
            if new_size <= limit:
                for old in generated:
                    if old != dst and os.path.isfile(old):
                        try: os.remove(old)
                        except OSError: pass
                return dst
            original, size = dst, new_size
        except Exception as exc:
            print(f"❌ Compression level {i} failed: {exc}")
            try:
                if os.path.isfile(dst): os.remove(dst)
            except OSError: pass
            break
    raise RuntimeError("الفيديو أكبر من الحد المسموح به حتى بعد الضغط.")


async def compress_audio_if_needed(path, status_message=None):
    limit = MAX_UPLOAD_SIZE / (1024 * 1024)
    size = get_file_size_mb(path)
    if size <= limit:
        return path
    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        raise RuntimeError("FFmpeg is not installed on the server.")
    base, _ = os.path.splitext(path)
    original = path
    for i, bitrate in enumerate(["128k", "96k", "64k", "48k"], 1):
        dst = f"{base}_compressed_{i}.mp3"
        if status_message:
            try: await status_message.edit_text(T.status_compress(i, 4, size, "الملف الصوتي"), parse_mode="HTML")
            except Exception: pass
        code, _, err = await run_ffmpeg([ffmpeg, "-y", "-i", original, "-vn", "-c:a", "libmp3lame", "-b:a", bitrate, dst])
        if code or not os.path.isfile(dst):
            print(f"❌ Audio compression failed: {err[-800:]}")
            try:
                if os.path.isfile(dst): os.remove(dst)
            except OSError: pass
            continue
        new_size = get_file_size_mb(dst)
        if new_size <= limit:
            if original != path:
                try: os.remove(original)
                except OSError: pass
            return dst
        if original != path:
            try: os.remove(original)
            except OSError: pass
        original, size = dst, new_size
    raise RuntimeError("الملف الصوتي أكبر من الحد المسموح به.")


async def handle_download(update, context):
    user = update.effective_user
    message = update.effective_message or update.message
    if not message or not getattr(message, "text", None):
        return
    url = extract_link(message.text)
    if not url:
        await message.reply_text(T.NO_LINK, parse_mode="HTML")
        return

    safe, reason = await asyncio.to_thread(is_safe_url, url)
    if not safe:
        print(f"🚫 Rejected URL from {user.id}: {reason}", flush=True)
        await message.reply_text(T.INVALID_LINK, parse_mode="HTML")
        return

    platform = get_platform(url)
    # Settings are stored per user in the database, so they survive restarts.
    settings = get_settings(user.id)
    quality = settings["quality"]
    audio = settings["mode"] == "audio"
    status = await message.reply_text(
        T.status_processing(platform, audio, quality), parse_mode="HTML"
    )
    started = datetime.now()
    result = None
    file_path = final_path = None

    async def show(text):
        try:
            await status.edit_text(text, parse_mode="HTML")
        except Exception:  # noqa: BLE001 - status edits are cosmetic
            pass

    try:
        if DOWNLOAD_SEMAPHORE.locked():
            await show(T.STATUS_QUEUED)

        async with DOWNLOAD_SEMAPHORE:
            await show(T.status_processing(platform, audio, quality))

            if platform == "TikTok":
                result = await download_tiktok(url, quality, audio)
            elif platform == "YouTube":
                result = await download_youtube(url, quality, audio)
            elif platform == "Facebook":
                result = await download_facebook(url, quality, audio)
            elif platform == "Instagram":
                result = await download_instagram(url, quality, audio)
            else:
                result = await download_generic(url, quality, audio, platform)

            if not result or not result.get("success"):
                error = (result or {}).get("error", "Unknown error")
                code = (result or {}).get("error_code")
                metrics.record_error(code or "UNKNOWN", user.id)
                await show(T.download_failed(error))
                await notify_admins(
                    context.bot, user.id, url, platform, code,
                    (result or {}).get("details") or error,
                )
                return

            file_path = result.get("file_path")
            title = result.get("title") or "Media"
            media_type = result.get("media_type") or ("audio" if audio else "video")
            if not file_path or not os.path.isfile(file_path):
                metrics.record_error("FILE_NOT_FOUND", user.id)
                await show(T.FILE_MISSING)
                return

            size = get_file_size_mb(file_path)
            limit = MAX_UPLOAD_SIZE / (1024 * 1024)
            print(f"📦 Downloaded file: {size:.2f} MB; type={media_type}", flush=True)

            # TikTok Photo Mode returns a ZIP/document. Do not send it through FFmpeg.
            if media_type == "document":
                if size > limit:
                    await show(T.TOO_BIG_PHOTOS)
                    return
                final_path = file_path
            elif size > limit:
                try:
                    if media_type == "audio" or audio:
                        final_path = await compress_audio_if_needed(file_path, status)
                    else:
                        final_path = await compress_until_small_enough(file_path, status)
                except Exception as exc:
                    print(f"❌ Compression error: {exc}", flush=True)
                    await show(T.TOO_BIG_AFTER_COMPRESS)
                    return
            else:
                final_path = file_path

        # The semaphore is released here: uploading does not need a slot.
        if not final_path or not os.path.isfile(final_path):
            await show(T.PREPARE_FAILED)
            return
        final_size = get_file_size_mb(final_path)
        if final_size > limit:
            await show(T.TOO_BIG_AFTER_COMPRESS)
            return

        await show(T.status_uploading(final_size))
        timeouts = dict(read_timeout=300, write_timeout=300, connect_timeout=60, pool_timeout=60)
        is_audio = media_type == "audio" or audio

        if media_type == "document":
            count = result.get("photo_count", "—")
            with open(final_path, "rb") as f:
                await message.reply_document(
                    document=f, filename=os.path.basename(final_path),
                    caption=T.caption_photos(count, final_size),
                    parse_mode="HTML", **timeouts)
        elif is_audio:
            with open(final_path, "rb") as f:
                await message.reply_audio(
                    audio=f, title=T.short(title, 80),
                    caption=T.caption_audio(title, platform, final_size),
                    parse_mode="HTML", **timeouts)
        else:
            duration = result.get("duration") or 0
            extra = {"duration": int(duration)} if duration else {}
            with open(final_path, "rb") as f:
                await message.reply_video(
                    video=f,
                    caption=T.caption_video(title, platform, quality, final_size),
                    parse_mode="HTML", supports_streaming=True, **extra, **timeouts)

        increase_downloads(user.id, "audio" if is_audio else "video")
        metrics.record_download((datetime.now() - started).total_seconds(), platform, user.id)
        try:
            await status.delete()
        except Exception:  # noqa: BLE001
            pass
        print(f"✅ Upload completed successfully for user {user.id}", flush=True)
    except Exception as exc:
        print(f"❌ HANDLE DOWNLOAD ERROR: {type(exc).__name__}: {exc}", flush=True)
        metrics.record_error("EXCEPTION", user.id)
        await show(T.SEND_FAILED)
        await notify_admins(context.bot, user.id, url, platform, "EXCEPTION",
                            f"{type(exc).__name__}: {exc}")
    finally:
        # The per-request work directory also holds compressed copies.
        remove_path((result or {}).get("workdir"))
        for path in {p for p in (final_path, file_path) if p}:
            remove_path(path)
