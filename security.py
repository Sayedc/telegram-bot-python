import re
from database.user_repository import get_data, save_data


# =========================
# URL safety
# =========================
def is_safe_url(url: str) -> bool:
    if not url:
        return False

    return url.startswith("http://") or url.startswith("https://")


# =========================
# تسجيل محاولة فاشلة
# =========================
def record_failed_attempt(user_id: int):
    data = get_data()

    if "failed" not in data:
        data["failed"] = {}

    uid = str(user_id)

    data["failed"][uid] = data["failed"].get(uid, 0) + 1

    save_data(data)


# =========================
# التحقق من الحظر
# =========================
def is_blocked(user_id: int) -> bool:
    data = get_data()

    user = data["users"].get(str(user_id))

    if not user:
        return False

    return user.get("blocked", False)


# =========================
# المستخدم محظور؟ (alias)
# =========================
def is_user_blocked(user_id: int) -> bool:
    return is_blocked(user_id)


# =========================
# إحصائيات الفشل
# =========================
def get_failed_stats():
    data = get_data()

    failed = data.get("failed", {})

    return {
        "total_failed": sum(failed.values()),
        "blocked_users": len([x for x in failed.values() if x > 5])
    }
