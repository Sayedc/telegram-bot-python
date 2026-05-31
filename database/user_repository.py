from datetime import datetime
from database.db import get_connection

def add_user(user_id, username):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    INSERT OR IGNORE INTO users
    (user_id, username, first_seen, last_seen)
    VALUES (?, ?, ?, ?)
    """, (
        user_id,
        username,
        datetime.now().isoformat(),
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()

def update_last_seen(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    UPDATE users
    SET last_seen = ?
    WHERE user_id = ?
    """, (
        datetime.now().isoformat(),
        user_id
    ))

    conn.commit()
    conn.close()
