import json
import os
from datetime import datetime

DB_FILE = "database.json"


# ==========================
# Database
# ==========================

def load_data():
    if not os.path.exists(DB_FILE):
        return {
            "users": {},
            "total": 0,
            "daily": 0,
            "last_date": str(datetime.now().date())
        }

    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def get_data():
    return load_data()


# ==========================
# Users
# ==========================

def get_users():
    return load_data()["users"]


def get_user(user_id):
    return load_data()["users"].get(str(user_id))


def add_user(user_id, name="Unknown"):
    data = load_data()

    uid = str(user_id)

    # إعادة تعيين عداد اليوم إذا بدأ يوم جديد
    today = str(datetime.now().date())
    if data.get("last_date") != today:
        data["daily"] = 0
        data["last_date"] = today

    if uid not in data["users"]:
        data["users"][uid] = {
            "name": name,
            "downloads": 0,
            "blocked": False,
            "joined": str(datetime.now()),
            "last_seen": str(datetime.now()),
            "first_seen": str(datetime.now()),
            "fav_platform": "None",
            "platforms": {}
        }

        data["total"] += 1

    save_data(data)


def update_last_seen(user_id):
    data = load_data()

    uid = str(user_id)

    if uid in data["users"]:
        data["users"][uid]["last_seen"] = str(datetime.now())

    save_data(data)


# ==========================
# Downloads
# ==========================

def increase_downloads(user_id, platform=None):
    data = load_data()

    uid = str(user_id)

    if uid in data["users"]:

        user = data["users"][uid]

        user["downloads"] = user.get("downloads", 0) + 1

        if platform:
            plats = user.setdefault("platforms", {})
            plats[platform] = plats.get(platform, 0) + 1

            user["fav_platform"] = max(
                plats,
                key=plats.get
            )

        data["daily"] = data.get("daily", 0) + 1

    save_data(data)


# ==========================
# Block System
# ==========================

def is_blocked(user_id):
    user = get_user(user_id)

    if not user:
        return False

    return user.get("blocked", False)


def block_user(user_id):
    data = load_data()

    uid = str(user_id)

    if uid in data["users"]:
        data["users"][uid]["blocked"] = True

    save_data(data)


def unblock_user(user_id):
    data = load_data()

    uid = str(user_id)

    if uid in data["users"]:
        data["users"][uid]["blocked"] = False

    save_data(data)


# ==========================
# Statistics
# ==========================

def get_total_users():
    return len(load_data()["users"])


def get_total_downloads():
    data = load_data()

    return sum(
        user.get("downloads", 0)
        for user in data["users"].values()
    )


def get_top_users(limit=10):
    data = load_data()

    return sorted(
        data["users"].items(),
        key=lambda x: x[1].get("downloads", 0),
        reverse=True
    )[:limit]
