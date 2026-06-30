# database/user_repository.py
import json
import os
from datetime import datetime

DB_FILE = "database.json"


# =========================
# INIT DATABASE
# =========================
def init_db():
    if not os.path.exists(DB_FILE):
        data = {
            "users": {},
            "total": 0,
            "daily": 0,
            "last_date": str(datetime.now().date())
        }

        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)


# =========================
# LOAD / SAVE
# =========================
def load_data():
    init_db()
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# =========================
# USERS BASIC OPS
# =========================
def get_users():
    return load_data().get("users", {})


def get_all_users():
    return get_users()


def get_user(user_id):
    return get_users().get(str(user_id))


def add_user(user_id, name="Unknown"):
    data = load_data()
    uid = str(user_id)

    if uid not in data["users"]:
        data["users"][uid] = {
            "name": name,
            "downloads": 0,
            "videos": 0,
            "audio": 0,
            "visits": 0,
            "blocked": False,
            "joined": str(datetime.now()),
            "last_seen": str(datetime.now())
        }
        data["total"] += 1

    save_data(data)


def update_last_seen(user_id):
    data = load_data()
    uid = str(user_id)

    if uid in data["users"]:
        data["users"][uid]["last_seen"] = str(datetime.now())
        data["users"][uid]["visits"] = data["users"][uid].get("visits", 0) + 1

    save_data(data)


# =========================
# DOWNLOAD STATS
# =========================
def increase_downloads(user_id, media_type="video"):
    data = load_data()
    uid = str(user_id)

    if uid in data["users"]:
        data["users"][uid]["downloads"] += 1
        
        if media_type == "video":
            data["users"][uid]["videos"] = data["users"][uid].get("videos", 0) + 1
        elif media_type == "audio":
            data["users"][uid]["audio"] = data["users"][uid].get("audio", 0) + 1

    save_data(data)


# =========================
# BLOCK SYSTEM
# =========================
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


def is_blocked(user_id):
    user = get_user(user_id)
    return user.get("blocked", False) if user else False


# =========================
# DELETE USER DATA (NEW)
# =========================
def delete_user_data(user_id):
    """حذف بيانات مستخدم معين"""
    data = load_data()
    uid = str(user_id)
    
    if uid in data["users"]:
        downloads = data["users"][uid].get("downloads", 0)
        del data["users"][uid]
        data["total"] = max(0, data["total"] - downloads)
        save_data(data)
        return True
    
    return False


# =========================
# USER STATS (NEW)
# =========================
def get_user_stats(user_id):
    """جلب إحصائيات مستخدم معين"""
    user = get_user(user_id)
    
    if not user:
        return None
    
    return {
        "downloads": user.get("downloads", 0),
        "videos": user.get("videos", 0),
        "audio": user.get("audio", 0),
        "visits": user.get("visits", 0),
        "blocked": user.get("blocked", False),
    }


# =========================
# STATS (FOR ADMIN)
# =========================
def get_admin_stats():
    data = load_data()
    users = data.get("users", {})

    return {
        "total_users": len(users),
        "blocked_users": sum(1 for u in users.values() if u.get("blocked")),
        "total_downloads": sum(u.get("downloads", 0) for u in users.values())
        }
