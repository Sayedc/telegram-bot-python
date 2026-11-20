import sqlite3

DB_NAME = "bot.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_seen TEXT,
        last_seen TEXT,
        downloads INTEGER DEFAULT 0,
        blocked INTEGER DEFAULT 0,
        points INTEGER DEFAULT 0,
        referrals INTEGER DEFAULT 0
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS stats (
        id INTEGER PRIMARY KEY,
        total_downloads INTEGER DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()
