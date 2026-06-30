import re
from database.user_repository import get_data, save_data

# =========================
# URL safety check
# =========================
def is_safe_url(url: str) -> bool:
    if not url:
        return False

    # منع الروابط الغريبة أو المكررة
    patterns = [
        r"^https?://",
    ]

    return any(re.match(p, url) for p in patterns)


# =========================
# تسجيل محاولة فاشلة
# =========================
def record_failed_attempt(user_id: int):
    data = get_data()

    if "failed" not in data:
        data["failed"] = {}

    uid = str(user_id)

    if uid not in data["failed"]:
        data["failed"][uid] = 0

    data["failed"][uid] += 1

    save_data(data)


# =========================
# (اختياري لو عندك استخدام لها)
# =========================
def is_user_blocked(user_id: int) -> bool:
    data = get_data()
    user = data["users"].get(str(user_id))

    if not user:
        return False

    return user.get("blocked", False)


# =========================
# stats helper
# =========================
def get_failed_stats():
    data = get_data()
    failed = data.get("failed", {})

    return {
        "total_failed": sum(failed.values()),
        "blocked_users": len([x for x in failed.values() if x > 5])
    }
