from database.user_repository import load_data, save_data


def is_blocked(user_id):
    data = load_data()
    user = data["users"].get(str(user_id))
    return user and user.get("blocked", False)


def is_safe_url(url):
    return url.startswith("http")


def record_failed_attempt(user_id):
    pass
