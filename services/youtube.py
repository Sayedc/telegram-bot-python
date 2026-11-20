# services/youtube.py
"""
YouTube downloader (yt-dlp).

All the heavy lifting lives in services/common.py. What is specific to
YouTube:

* A JavaScript runtime (Deno/Node/Bun) is REQUIRED by YouTube. common.py
  enables every runtime it finds on PATH - Node alone is not picked up by
  yt-dlp unless it is enabled explicitly.
* Cookies: set the YOUTUBE_COOKIES env var (content of a Netscape cookies.txt)
  or put cookies_youtube.txt next to the bot.
* The player client list is NOT forced any more (yt-dlp updates its defaults
  with every release). To override it for debugging set
  YT_PLAYER_CLIENTS="web_safari,tv" (comma separated).
* A custom User-Agent header is NOT forced either: mobile clients expect
  their own UA and a mismatch is a classic cause of HTTP 403.
"""

import os

from services.common import download_with_ytdlp


def _extra_options():
    clients = [
        c.strip()
        for c in os.getenv("YT_PLAYER_CLIENTS", "").split(",")
        if c.strip()
    ]
    if not clients:
        return {}
    return {"extractor_args": {"youtube": {"player_client": clients}}}


async def download_youtube(url: str, quality: str = "720", audio: bool = False):
    return await download_with_ytdlp(
        "YouTube", url, quality, audio, extra_opts=_extra_options()
    )
