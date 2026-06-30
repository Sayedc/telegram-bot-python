import json

DB_FILE = "bot_database.json"


def is_blocked(user_id: int) -> bool:
    try:
        with open(DB_FILE, "r") as f:
            data = json.load(f)

        user = data["users"].get(str(user_id))
        if not user:
            return False

        return user.get("blocked", False)

    except:
        return False
