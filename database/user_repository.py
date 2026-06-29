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
