import sqlite3

DB_FILE = "youtube.db"


def get_db():
    return sqlite3.connect(DB_FILE)


def init_db():
    db = get_db()
    cur = db.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS channels (
        channel_id TEXT PRIMARY KEY,
        url TEXT,
        country TEXT,
        joined TEXT,
        subscribers TEXT,
        video_count TEXT,
        views TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS videos (
        video_id TEXT PRIMARY KEY,
        channel_id TEXT,
        url TEXT,
        title TEXT,
        published TEXT,
        views TEXT,
        likes TEXT,
        comments TEXT,
        description TEXT,
        type TEXT,
        FOREIGN KEY(channel_id) REFERENCES channels(channel_id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS shorts (
        short_id TEXT PRIMARY KEY,
        channel_id TEXT,
        url TEXT,
        title TEXT,
        published TEXT,
        views TEXT,
        likes TEXT,
        comments TEXT,
        description TEXT,
        type TEXT,
        FOREIGN KEY(channel_id) REFERENCES channels(channel_id)
    )
    """)

    db.commit()
    db.close()


def save_channel(channel_id, url, country, joined, subscribers, video_count, views):
    db = get_db()
    cur = db.cursor()

    cur.execute("""
        INSERT OR REPLACE INTO channels (
            channel_id, url, country, joined, subscribers, video_count, views
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (channel_id, url, country, joined, subscribers, video_count, views))

    db.commit()
    db.close()


def save_video(video_id, channel_id, url, title, published, views, likes, comments, description, type_):
    db = get_db()
    cur = db.cursor()

    cur.execute("""
        INSERT OR REPLACE INTO videos (
            video_id, channel_id, url, title, published, views, likes, comments, description, type
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (video_id, channel_id, url, title, published, views, likes, comments, description, type_))

    db.commit()
    db.close()


def save_short(short_id, channel_id, url, title, published, views, likes, comments, description, type_):
    db = get_db()
    cur = db.cursor()

    cur.execute("""
        INSERT OR REPLACE INTO shorts (
            short_id, channel_id, url, title, published, views, likes, comments, description, type
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (short_id, channel_id, url, title, published, views, likes, comments, description, type_))

    db.commit()
    db.close()
