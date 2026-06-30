import json
import os
from datetime import datetime

DB_FILE = "database.json"


def load_data():
    if not os.path.exists(DB_FILE):
        return {
            "users": {},
            "total": 0,
            "daily": 0
        }

    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def get_data():
    return load_data()


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


def is_blocked(user_id):
    data = load_data()

    uid = str(user_id)

    if uid not in data["users"]:
        return False

    return data["users"][uid].get("blocked", False)


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


def increase_downloads(user_id):
    data = load_data()

    uid = str(user_id)

    if uid in data["users"]:
        data["users"][uid]["downloads"] += 1

    save_data(data)


def get_user(user_id):
    data = load_data()
    return data["users"].get(str(user_id))
