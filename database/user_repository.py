import json
import os

DB_FILE = "database.json"


# =========================
# تحميل الداتا
# =========================
def get_data():
    if not os.path.exists(DB_FILE):
        data = {
            "users": {},
            "total": 0,
            "daily": 0,
            "failed": {}
        }
        with open(DB_FILE, "w") as f:
            json.dump(data, f, indent=4)

    with open(DB_FILE, "r") as f:
        return json.load(f)


# =========================
# حفظ الداتا
# =========================
def save_data(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)


# =========================
# إضافة مستخدم
# =========================
def add_user(user_id, name):
    data = get_data()

    uid = str(user_id)

    if uid not in data["users"]:
        data["users"][uid] = {
            "name": name,
            "downloads": 0,
            "blocked": False
        }

    save_data(data)


# =========================
# تحديث آخر ظهور
# =========================
def update_last_seen(user_id):
    data = get_data()

    uid = str(user_id)

    if uid in data["users"]:
        data["users"][uid]["last_seen"] = True

    save_data(data)


# =========================
# أعلى مستخدمين
# =========================
def get_top_users(limit=10):
    data = get_data()

    users = data.get("users", {})

    sorted_users = sorted(
        users.items(),
        key=lambda x: x[1].get("downloads", 0),
        reverse=True
    )

    return sorted_users[:limit]
