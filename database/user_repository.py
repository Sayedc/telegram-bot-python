import json
import os
from datetime import datetime

DB_FILE = "database.json"


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


def load_data():
    init_db()
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def get_users():
    return load_data()["users"]


def get_user(user_id):
    return load_data()["users"].get(str(user_id))


def add_user(user_id, name="Unknown"):
    data = load_data()
    uid = str(user_id)

    if uid not in data["users"]:
        data["users"][uid] = {
            "name": name,
            "downloads": 0,
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

    save_data(data)


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


def increase_downloads(user_id):
    data = load_data()
    uid = str(user_id)

    if uid in data["users"]:
        data["users"][uid]["downloads"] += 1

    save_data(data)
