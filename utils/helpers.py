import yt_dlp


# =========================
# Video info function
# =========================
async def get_video_info(url: str):
    opts = {
        "quiet": True,
        "no_warnings": True
    }

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)

            duration = info.get("duration", 0)

            if duration:
                minutes = duration // 60
                seconds = duration % 60
                duration_str = f"{minutes}:{seconds:02d}"
            else:
                duration_str = "غير معروف"

            filesize = info.get("filesize_approx", 0)

            if filesize:
                size_mb = filesize / 1048576
                size_str = f"{size_mb:.1f} MB"
            else:
                size_str = "غير معروف"

            return {
                "title": info.get("title", "غير معروف"),
                "duration": duration_str,
                "size": size_str,
            }

    except Exception:
        return None
