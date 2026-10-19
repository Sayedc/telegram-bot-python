# services/tiktok.py
        import asyncio
import os
import re
import shutil
import tempfile
import zipfile
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import yt_dlp
from config import DOWNLOADS_PATH


def _clean_tiktok_url(url: str) -> str:
    """Normalize accidental whitespace and remove tracking query parameters."""
    url = (url or "").strip()
    # TikTok URLs copied from logs/messages can contain accidental spaces inside IDs.
    url = re.sub(r"\s+", "", url)
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https") or not parts.netloc.lower().endswith("tiktok.com"):
        raise ValueError("رابط TikTok غير صحيح.")
    # Keep the post path; tracking query parameters are not required for extraction.
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


async def _download_photo_post(url: str) -> dict:
    """Download TikTok Photo Mode with gallery-dl and package images into a ZIP."""
    gallery_dl = shutil.which("gallery-dl")
    if not gallery_dl:
        return {
            "success": False,
            "error": "منشور الصور يحتاج تثبيت gallery-dl. أضف gallery-dl إلى requirements.txt ثم أعد النشر.",
            "error_code": "PHOTO_DEPENDENCY_MISSING",
        }

    os.makedirs(DOWNLOADS_PATH, exist_ok=True)
    work_dir = tempfile.mkdtemp(prefix="tiktok_photo_", dir=DOWNLOADS_PATH)
    zip_path = os.path.join(
        DOWNLOADS_PATH,
        f"tiktok_photo_{os.path.basename(work_dir).replace('tiktok_photo_', '')}.zip",
    )

    try:
        # Run outside the event loop; cap runtime to avoid hanging a bot worker.
        proc = await asyncio.create_subprocess_exec(
            gallery_dl,
            "--no-mtime",
            "-D", work_dir,
            url,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=180)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.communicate()
            return {
                "success": False,
                "error": "انتهت مهلة تنزيل صور TikTok. جرّب مرة أخرى.",
                "error_code": "TIMEOUT",
            }

        files = [
            p for p in Path(work_dir).rglob("*")
            if p.is_file() and p.suffix.lower() in {
                ".jpg", ".jpeg", ".png", ".webp", ".gif", ".mp4", ".webm"
            }
        ]

        if proc.returncode != 0 or not files:
            details = (stderr or stdout or b"").decode("utf-8", errors="replace").strip()
            return {
                "success": False,
                "error": ("تعذر تنزيل صور منشور TikTok."
                          + (f" التفاصيل: {details[-350:]}" if details else "")),
                "error_code": "PHOTO_DOWNLOAD_FAILED",
            }

        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for file_path in files:
                archive.write(file_path, arcname=file_path.name)

        return {
            "success": True,
            "file_path": zip_path,
            "title": "TikTok Photo Post",
            "duration": 0,
            "platform": "TikTok",
            "media_type": "document",
            "is_photo_post": True,
            "photo_count": len(files),
        }
    except Exception as exc:
        try:
            if os.path.exists(zip_path):
                os.remove(zip_path)
        except OSError:
            pass
        return {
            "success": False,
            "error": f"TikTok photo download failed: {str(exc)[:180]}",
            "error_code": "PHOTO_DOWNLOAD_FAILED",
        }
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


async def download_tiktok(url: str, quality: str = "720", audio: bool = False):
    """
    Download a TikTok video/audio with yt-dlp, or Photo Mode with gallery-dl.
    For Photo Mode, returns a ZIP path and media_type='document'.
    """
    try:
        url = _clean_tiktok_url(url)
        if "/photo/" in urlsplit(url).path.lower():
            if audio:
                return {
                    "success": False,
                    "error": "رابط الصور لا يحتوي على مسار صوتي مستقل.",
                    "error_code": "INVALID_MEDIA_TYPE",
                }
            return await _download_photo_post(url)

        os.makedirs(DOWNLOADS_PATH, exist_ok=True)
        opts = {
            "outtmpl": os.path.join(DOWNLOADS_PATH, "tiktok_%(id)s.%(ext)s"),
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "restrictfilenames": True,
            "overwrites": True,
        }

        cookie_candidates = (
            os.path.join(os.getcwd(), "cookies.txt"),
            "/app/cookies.txt",
        )
        for cookie_path in cookie_candidates:
            if os.path.isfile(cookie_path):
                opts["cookiefile"] = cookie_path
                break

        if audio:
            opts.update({
                "format": "bestaudio/best",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
            })
        else:
            # Avoid the old extractor_args option that can trigger setdefault errors
            # with some yt-dlp versions. Respect the requested quality when possible.
            try:
                max_height = max(144, min(int(quality), 4320))
            except (TypeError, ValueError):
                max_height = 720
            opts["format"] = (
                f"best[height<={max_height}]/best"
            )

        def _extract():
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if not info:
                    raise RuntimeError("TikTok لم يُرجع معلومات قابلة للتنزيل.")
                prepared = ydl.prepare_filename(info)
                if audio:
                    prepared = str(Path(prepared).with_suffix(".mp3"))
                # Some postprocessors/mergers change the final extension.
                if not os.path.isfile(prepared):
                    candidates = sorted(
                        Path(DOWNLOADS_PATH).glob(f"tiktok_{info.get('id', '')}.*"),
                        key=lambda p: p.stat().st_mtime,
                        reverse=True,
                    )
                    if audio:
                        candidates = [p for p in candidates if p.suffix.lower() == ".mp3"]
                    if candidates:
                        prepared = str(candidates[0])
                if not os.path.isfile(prepared):
                    raise FileNotFoundError("التحميل انتهى لكن الملف الناتج غير موجود.")
                return info, prepared

        info, file_path = await asyncio.to_thread(_extract)
        return {
            "success": True,
            "file_path": file_path,
            "title": info.get("title") or "TikTok Video",
            "duration": info.get("duration") or 0,
            "platform": "TikTok",
            "media_type": "audio" if audio else "video",
            "is_photo_post": False,
        }

    except Exception as exc:
        message = str(exc)
        return {
            "success": False,
            "error": f"TikTok download failed: {message[:180]}",
            "error_code": "DOWNLOAD_ERROR",
        }
