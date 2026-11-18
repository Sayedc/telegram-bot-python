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
from services.common import (
    base_options,
    failure_result,
    find_output_file,
    new_workdir,
    prepare_cookies,
    remove_path,
)


PHOTO_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".webp", ".gif", ".mp4", ".webm"
}


def _clean_tiktok_url(url: str) -> str:
    """Normalize TikTok URLs and remove tracking parameters."""
    url = re.sub(r"\s+", "", (url or "").strip())
    parts = urlsplit(url)

    hostname = (parts.hostname or "").lower()
    if (
        parts.scheme not in ("http", "https")
        or not (hostname == "tiktok.com" or hostname.endswith(".tiktok.com"))
    ):
        raise ValueError("رابط TikTok غير صحيح.")

    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


async def _download_photo_post(url: str) -> dict:
    """Download TikTok Photo Mode and package its media into a ZIP."""
    gallery_dl = shutil.which("gallery-dl")

    if not gallery_dl:
        return {
            "success": False,
            "error": "gallery-dl غير مثبت على السيرفر.",
            "error_code": "PHOTO_DEPENDENCY_MISSING",
        }

    os.makedirs(DOWNLOADS_PATH, exist_ok=True)
    work_dir = tempfile.mkdtemp(
        prefix="tiktok_photo_", dir=DOWNLOADS_PATH
    )
    zip_path = os.path.join(
        DOWNLOADS_PATH,
        f"{os.path.basename(work_dir)}.zip",
    )

    try:
        print(f"[TIKTOK DEBUG] Photo Mode URL: {url}")
        print(f"[TIKTOK DEBUG] gallery-dl executable: {gallery_dl}")

        proc = await asyncio.create_subprocess_exec(
            gallery_dl,
            "--no-mtime",
            "-D", work_dir,
            url,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=180
            )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.communicate()
            return {
                "success": False,
                "error": "انتهت مهلة تنزيل صور TikTok. جرّب مرة أخرى.",
                "error_code": "TIMEOUT",
            }

        files = sorted(
            p for p in Path(work_dir).rglob("*")
            if p.is_file() and p.suffix.lower() in PHOTO_EXTENSIONS
        )

        if proc.returncode != 0 or not files:
            details = (
                stderr or stdout or b""
            ).decode("utf-8", errors="replace").strip()

            print(
                f"[TIKTOK DEBUG] gallery-dl exit={proc.returncode}; "
                f"files={len(files)}; details={details[-1000:]}"
            )

            return {
                "success": False,
                "error": (
                    "تعذر تنزيل صور منشور TikTok."
                    + (f" التفاصيل: {details[-350:]}" if details else "")
                ),
                "error_code": "PHOTO_DOWNLOAD_FAILED",
            }

        # Avoid duplicate ZIP names if different folders contain same basenames.
        with zipfile.ZipFile(
            zip_path, "w", compression=zipfile.ZIP_DEFLATED
        ) as archive:
            for index, file_path in enumerate(files, start=1):
                archive_name = f"{index:03d}_{file_path.name}"
                archive.write(file_path, arcname=archive_name)

        print(f"[TIKTOK DEBUG] Photo download succeeded: {len(files)} files")

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
        print(f"[TIKTOK DEBUG] Photo download exception: {exc}")

        try:
            if os.path.exists(zip_path):
                os.remove(zip_path)
        except OSError:
            pass

        return {
            "success": False,
            "error": f"فشل تنزيل منشور الصور: {str(exc)[:180]}",
            "error_code": "PHOTO_DOWNLOAD_FAILED",
        }

    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


async def download_tiktok(
    url: str, quality: str = "720", audio: bool = False
):
    """Download TikTok videos/audio with yt-dlp and Photo Mode with gallery-dl."""
    try:
        url = _clean_tiktok_url(url)
        path = urlsplit(url).path.lower()
        is_photo_post = "/photo/" in path

        print(f"[TIKTOK DEBUG] URL path: {path}")
        print(f"[TIKTOK DEBUG] Photo mode detected: {is_photo_post}")

        if is_photo_post:
            if audio:
                return {
                    "success": False,
                    "error": "رابط الصور لا يحتوي على مسار صوتي مستقل.",
                    "error_code": "INVALID_MEDIA_TYPE",
                }

            print("[TIKTOK DEBUG] Routing Photo Mode to gallery-dl")
            return await _download_photo_post(url)

        print("[TIKTOK DEBUG] Routing video/audio to yt-dlp")

        workdir = new_workdir(prefix="tiktok_")

        try:
            opts = base_options(workdir)
            opts["outtmpl"] = os.path.join(workdir, "tiktok_%(id)s.%(ext)s")

            cookie_file = prepare_cookies("tiktok", workdir)
            if cookie_file:
                opts["cookiefile"] = cookie_file

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
                try:
                    max_height = max(144, min(int(quality), 4320))
                except (TypeError, ValueError):
                    max_height = 720

                # res:<N> uses the shorter side, so vertical TikToks get the
                # requested quality instead of one step lower.
                opts["format"] = "best/bv*+ba"
                opts["format_sort"] = [f"res:{max_height}", "ext:mp4"]

            def _extract():
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(url, download=True)

                    if not info:
                        raise RuntimeError(
                            "TikTok لم يُرجع معلومات قابلة للتنزيل."
                        )

                    if info.get("entries"):
                        entries = [e for e in info["entries"] if e]
                        if not entries:
                            raise RuntimeError("TikTok returned no entries.")
                        info = entries[0]

                    prepared = None
                    for item in info.get("requested_downloads") or []:
                        candidate = item.get("filepath") or item.get("_filename")
                        if candidate and os.path.isfile(candidate):
                            prepared = candidate
                            break

                    if audio and prepared and not prepared.lower().endswith(".mp3"):
                        prepared = None  # pre-conversion stream; look for the mp3

                    if not prepared:
                        prepared = find_output_file(
                            workdir, ".mp3" if audio else None
                        )

                    if not prepared or not os.path.isfile(prepared):
                        raise FileNotFoundError(
                            "التحميل انتهى لكن الملف الناتج غير موجود."
                        )

                    return info, prepared

            info, file_path = await asyncio.to_thread(_extract)

        except Exception:
            remove_path(workdir)
            raise

        return {
            "success": True,
            "file_path": file_path,
            "workdir": workdir,
            "title": info.get("title") or "TikTok Video",
            "duration": info.get("duration") or 0,
            "platform": "TikTok",
            "media_type": "audio" if audio else "video",
            "is_photo_post": False,
        }

    except Exception as exc:
        print(f"[TIKTOK ERROR] {type(exc).__name__}: {str(exc)[:500]}")
        return failure_result("TikTok", exc)
