import json
import os
from datetime import datetime

DB_FILE = "bot_database.json"

def init_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w') as f:
            json.dump({
                "users": {},
                "stats": {
                    "total_downloads": 0,
                    "total_users": 0,
                    "daily_downloads": {}
                }
            }, f)

def add_user(user_id, username):
    with open(DB_FILE, 'r+') as f:
        data = json.load(f)
        if str(user_id) not in data["users"]:
            data["users"][str(user_id)] = {
                "username": username,
                "first_seen": datetime.now().isoformat(),
                "downloads": 0,
                "blocked": False
            }
            data["stats"]["total_users"] = len(data["users"])
            f.seek(0)
            json.dump(data, f, indent=2)

def increment_downloads(user_id):
    with open(DB_FILE, 'r+') as f:
        data = json.load(f)
        if str(user_id) in data["users"]:
            data["users"][str(user_id)]["downloads"] += 1
            data["stats"]["total_downloads"] += 1
            
            today = datetime.now().strftime("%Y-%m-%d")
            if today not in data["stats"]["daily_downloads"]:
                data["stats"]["daily_downloads"][today] = 0
            data["stats"]["daily_downloads"][today] += 1
            
            f.seek(0)
            json.dump(data, f, indent=2)

def is_user_blocked(user_id):
    with open(DB_FILE, 'r') as f:
        data = json.load(f)
        return data["users"].get(str(user_id), {}).get("blocked", False)
