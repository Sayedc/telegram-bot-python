import json
import os

DB_FILE = "database.json"


def load_data():
    if not os.path.exists(DB_FILE):
        return {"users": {}, "total": 0, "daily": 0}
    with open(DB_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)


def add_user(user_id, name="Unknown"):
    data = load_data()
    uid = str(user_id)

    if uid not in data["users"]:
        data["users"][uid] = {"name": name, "downloads": 0, "blocked": False}

    save_data(data)


def update_last_seen(user_id):
    data = load_data()
    uid = str(user_id)
    if uid in data["users"]:
        data["users"][uid]["last_seen"] = True
    save_data(data)


def get_data():
    return load_data()
