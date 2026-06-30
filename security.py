from database.user_repository import (
    load_data,
    save_data,
    is_blocked as db_is_blocked
)

# ==========================
# إحصائيات الحماية
# ==========================

_failed_attempts = {}
_blocked_attempts = 0


# ==========================
# المستخدم محظور؟
# ==========================

def is_blocked(user_id):
    return db_is_blocked(user_id)


# ==========================
# التحقق من الرابط
# ==========================

def is_safe_url(url):
    if not url:
        return False

    url = url.lower()

    allowed = (
        "http://",
        "https://"
    )

    return url.startswith(allowed)


# ==========================
# تسجيل محاولة فاشلة
# ==========================

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


# ==========================
# تصفير عداد المحاولات
# ==========================

def reset_failed_attempts(user_id):
    uid = str(user_id)

    if uid in _failed_attempts:
        del _failed_attempts[uid]


# ==========================
# إحصائيات الأدمن
# ==========================

def get_failed_stats():
    data = load_data()

    blocked_users = sum(
        1
        for u in data["users"].values()
        if u.get("blocked", False)
    )

    return {
        "failed_attempts": sum(_failed_attempts.values()),
        "blocked_users": blocked_users + _blocked_attempts
    }
