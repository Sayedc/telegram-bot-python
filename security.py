import ipaddress
import socket
from urllib.parse import urlsplit

from database.user_repository import load_data, save_data, is_blocked as db_is_blocked

_failed_attempts = {}
_blocked_attempts = 0


def is_blocked(user_id):
    return db_is_blocked(user_id)


def is_safe_url(url):
    """
    Accept only public http(s) URLs.

    The bot downloads whatever URL a user sends, from the server itself, so
    URLs that point at the server's own network (localhost, 10.x, 192.168.x,
    169.254.169.254 cloud-metadata, ...) must be refused. This does a DNS
    lookup, so call it from a thread (asyncio.to_thread) inside async code.
    """
    if not url:
        return False, "Empty URL"

    try:
        parts = urlsplit(url.strip())
        port = parts.port
    except ValueError:
        return False, "Invalid URL"

    scheme = (parts.scheme or "").lower()
    host = parts.hostname

    if scheme not in ("http", "https") or not host:
        return False, "Invalid URL"

    if parts.username or parts.password:
        return False, "Credentials in URL are not allowed"

    try:
        infos = socket.getaddrinfo(
            host, port or (443 if scheme == "https" else 80),
            proto=socket.IPPROTO_TCP,
        )
    except (socket.gaierror, UnicodeError):
        return False, "Unknown host"

    for info in infos:
        try:
            ip = ipaddress.ip_address(info[4][0].split("%")[0])
        except ValueError:
            return False, "Invalid address"

        if ip.version == 6 and ip.ipv4_mapped:
            ip = ip.ipv4_mapped

        if (
            ip.is_private or ip.is_loopback or ip.is_link_local
            or ip.is_reserved or ip.is_multicast or ip.is_unspecified
        ):
            return False, "Private address not allowed"

    return True, "OK"


def record_failed_attempt(user_id):
    global _blocked_attempts

    uid = str(user_id)

    _failed_attempts[uid] = _failed_attempts.get(uid, 0) + 1

    if _failed_attempts[uid] >= 5:
        data = load_data()

        if uid in data["users"]:
            data["users"][uid]["blocked"] = True
            save_data(data)

        _blocked_attempts += 1


def get_failed_stats():
    data = load_data()

    blocked_users = sum(
        1 for u in data["users"].values()
        if u.get("blocked", False)
    )

    return {
        "failed_attempts": sum(_failed_attempts.values()),
        "blocked_users": blocked_users + _blocked_attempts
    }
