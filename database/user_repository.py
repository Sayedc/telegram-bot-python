import json
import os
from datetime import datetime

DB_FILE = "bot_database.json"


def init_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w") as f:
            json.dump({
                "users": {},
                "total": 0,
                "daily": 0,
                "last_date": str(datetime.now().date())
            }, f, indent=2)


async def save_user(user_id, username):
    with open(DB_FILE, "r+") as f:
        data = json.load(f)

        if str(user_id) not in data["users"]:
            data["users"][str(user_id)] = {
                "name": username,
                "first_seen": str(datetime.now()),
                "last_seen": str(datetime.now()),
                "downloads": 0,
                "fav_platform": "None",
                "platforms": {},
                "blocked": False
            }

        else:
            data["users"][str(user_id)]["last_seen"] = str(datetime.now())

        f.seek(0)
        json.dump(data, f, indent=2)
        f.truncate()


def get_data():
    with open(DB_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)
def update_stats(user_id, platform):
    data = get_data()

    today = str(datetime.now().date())

    if data["last_date"] != today:
        data["daily"] = 0
        data["last_date"] = today

    if str(user_id) in data["users"]:
        user = data["users"][str(user_id)]

        user["downloads"] += 1
        user["last_seen"] = str(datetime.now())

        if platform in user["platforms"]:
            user["platforms"][platform] += 1
        else:
            user["platforms"][platform] = 1

        user["fav_platform"] = max(
            user["platforms"],
            key=user["platforms"].get
        )

        data["total"] += 1
        data["daily"] += 1

        save_data(data)


def delete_user_data(user_id):
    data = get_data()

    if str(user_id) in data["users"]:
        downloads = data["users"][str(user_id)].get("downloads", 0)

        del data["users"][str(user_id)]

        data["total"] = max(0, data["total"] - downloads)

        save_data(data)

        return True

    return False


def get_users():
    data = get_data()

    return [
        uid
        for uid, u in data["users"].items()
        if not u.get("blocked", False)
    ]


def get_all_users():
    return list(get_data()["users"].keys())


def is_blocked(user_id):
    data = get_data()

    return data["users"].get(
        str(user_id),
        {}
    ).get("blocked", False)


def block_user(user_id):
    data = get_data()

    if str(user_id) in data["users"]:
        data["users"][str(user_id)]["blocked"] = True
        save_data(data)
        return True

    return False


def unblock_user(user_id):
    data = get_data()

    if str(user_id) in data["users"]:
        data["users"][str(user_id)]["blocked"] = False
        save_data(data)
        return True

    return False
