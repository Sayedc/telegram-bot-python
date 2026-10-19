import asyncio
import os
import shutil
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

MAX_UPLOAD_SIZE = 49 * 1024 * 1024


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
            try: await status_message.edit_text(f"⏳ الفيديو حجمه كبير... جاري الضغط ({i}/3)\n📦 {size:.2f} MB")
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
            try: await status_message.edit_text(f"⏳ الملف الصوتي كبير... جاري الضغط ({i}/4)")
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
        await message.reply_text("❌ أرسل رابط صحيح")
        return

    platform = get_platform(url)
    quality = context.user_data.get("quality", "720")
    audio = context.user_data.get("audio", False)
    status = await message.reply_text(f"{get_random_processing_text()}\n📱 {platform}")
    started = datetime.now()
    file_path = final_path = None

    try:
        if platform == "TikTok":
            result = await download_tiktok(url, quality, audio)
        elif platform == "YouTube":
            result = await download_youtube(url, quality, audio)
        elif platform == "Facebook":
            result = await download_facebook(url, quality, audio)
        elif platform == "Instagram":
            result = await download_instagram(url, quality, audio)
        else:
            result = await download_youtube(url, quality, audio)

        if not result or not result.get("success"):
            await status.edit_text(f"❌ {(result or {}).get('error', 'Unknown error')}")
            return

        file_path = result.get("file_path")
        title = result.get("title") or "Media"
        media_type = result.get("media_type") or ("audio" if audio else "video")
        if not file_path or not os.path.isfile(file_path):
            await status.edit_text("❌ الملف لم يتم العثور عليه بعد التحميل.")
            return

        size = get_file_size_mb(file_path)
        limit = MAX_UPLOAD_SIZE / (1024 * 1024)
        print(f"📦 Downloaded file: {size:.2f} MB; type={media_type}")

        # TikTok Photo Mode returns a ZIP/document. Do not send it through FFmpeg.
        if media_type == "document":
            if size > limit:
                await status.edit_text("❌ ملف صور المنشور أكبر من حد الإرسال (49 MB).")
                return
            final_path = file_path
        elif size > limit:
            try:
                if media_type == "audio" or audio:
                    final_path = await compress_audio_if_needed(file_path, status)
                else:
                    final_path = await compress_until_small_enough(file_path, status)
            except Exception as exc:
                print(f"❌ Compression error: {exc}")
                await status.edit_text("❌ الملف كبير جدًا حتى بعد محاولة ضغطه. جرّب جودة أقل مثل 480p أو 360p.")
                return
        else:
            final_path = file_path

        if not final_path or not os.path.isfile(final_path):
            await status.edit_text("❌ تعذر تجهيز الملف للإرسال.")
            return
        final_size = get_file_size_mb(final_path)
        if final_size > limit:
            await status.edit_text("❌ حجم الملف ما زال أكبر من الحد المسموح به.")
            return

        await status.edit_text(f"📤 جاري إرسال الملف...\n📦 الحجم: {final_size:.2f} MB")
        success_caption = f"{get_random_success_text()}\n📦 {final_size:.2f} MB\n{SIGNATURE}"
        timeouts = dict(read_timeout=300, write_timeout=300, connect_timeout=60, pool_timeout=60)

        if media_type == "document":
            count = result.get("photo_count", "عدة")
            with open(final_path, "rb") as f:
                await message.reply_document(document=f, filename=os.path.basename(final_path),
                    caption=f"🖼️ صور منشور TikTok ({count} صورة)\n{success_caption}", **timeouts)
        elif media_type == "audio" or audio:
            with open(final_path, "rb") as f:
                await message.reply_audio(audio=f, title=title[:80], caption=success_caption, **timeouts)
        else:
            with open(final_path, "rb") as f:
                await message.reply_video(video=f,
                    caption=f"🎬 {title[:80]}\n📦 {final_size:.2f} MB\n🎥 الجودة: {quality}p\n📱 {platform}\n\n{SIGNATURE}",
                    supports_streaming=True, **timeouts)

        increase_downloads(user.id)
        metrics.record_download((datetime.now() - started).total_seconds(), platform, user.id)
        try: await status.delete()
        except Exception: pass
        print(f"✅ Upload completed successfully for user {user.id}")
    except Exception as exc:
        print(f"❌ HANDLE DOWNLOAD ERROR: {exc}")
        try: await status.edit_text(f"❌ {get_random_error_text()}\n\n{str(exc)[:300]}", parse_mode=None)
        except Exception: pass
    finally:
        for path in {p for p in (final_path, file_path) if p}:
            try:
                if os.path.isfile(path): os.remove(path)
            except OSError: pass
