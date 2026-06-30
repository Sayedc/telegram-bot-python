from database.user_repository import load_data, save_data, is_blocked as db_is_blocked

_failed_attempts = {}
_blocked_attempts = 0


def is_blocked(user_id):
    return db_is_blocked(user_id)


def is_safe_url(url):
    if not url:
        return False, "Empty URL"

    url = url.lower()

    if url.startswith(("http://", "https://")):
        return True, "OK"

    return False, "Invalid URL"


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
