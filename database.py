import sqlite3

DB_NAME = "duofinder.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            game TEXT,
            rank TEXT,
            role TEXT,
            time TEXT,
            rating REAL DEFAULT 5.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user1_id INTEGER,
            user2_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_user_id INTEGER,
            to_user_id INTEGER,
            stars INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

    migrate_db()


def migrate_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute(
            "ALTER TABLE users ADD COLUMN last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        )
        conn.commit()
        print("✅ Добавлено поле last_seen")
    except sqlite3.OperationalError:
        pass

    conn.close()


def init_analytics():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            event_type TEXT,
            event_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def init_games():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            emoji TEXT DEFAULT '🎮',
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("SELECT COUNT(*) FROM games")
    if cursor.fetchone()[0] == 0:
        default_games = [
            ("Dota 2", "🟥"),
            ("CS2", "🔫"),
            ("Valorant", "🎯"),
            ("League of Legends", "⚔️"),
            ("Mobile Legends", "📱"),
            ("PUBG", "🪖"),
            ("Fortnite", "🏗"),
            ("Apex Legends", "🚀"),
            ("Overwatch 2", "🛡"),
            ("Minecraft", "⛏"),
        ]
        for name, emoji in default_games:
            cursor.execute("""
                INSERT OR IGNORE INTO games (name, emoji)
                VALUES (?, ?)
            """, (name, emoji))

    conn.commit()
    conn.close()


def init_messages():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_user_id INTEGER NOT NULL,
            to_user_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            is_read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


# ===== ПОЛЬЗОВАТЕЛИ =====

def add_user(user_id, username):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO users (user_id, username, last_seen)
        VALUES (?, ?, CURRENT_TIMESTAMP)
    """, (user_id, username))
    conn.commit()
    conn.close()


def update_profile(user_id, game, rank, role, time):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users
        SET game = ?, rank = ?, role = ?, time = ?
        WHERE user_id = ?
    """, (game, rank, role, time, user_id))
    conn.commit()
    conn.close()


def get_profile(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user


def find_partner(user_id, game, rank):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT user_id, username, game, rank, role, time, rating
        FROM users
        WHERE game = ? AND rank = ? AND user_id != ?
        ORDER BY rating DESC
        LIMIT 5
    """, (game, rank, user_id))
    users = cursor.fetchall()
    conn.close()
    return users


def find_partner_filtered(
    user_id: int,
    game: str,
    rank: str = None,
    role: str = None,
    time: str = None,
    min_rating: float = None,
    exclude_toxic: bool = False,
    limit: int = 5
):
    """
    Ищет напарников с учётом фильтров.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    query = """
        SELECT user_id, username, game, rank, role, time, rating
        FROM users
        WHERE user_id != ?
          AND game = ?
          AND game IS NOT NULL
    """
    params = [user_id, game]

    if rank:
        query += " AND rank = ?"
        params.append(rank)

    if role:
        query += " AND role = ?"
        params.append(role)

    if time:
        query += " AND time = ?"
        params.append(time)

    if min_rating is not None:
        query += " AND rating >= ?"
        params.append(min_rating)

    if exclude_toxic:
        query += " AND rating >= 5.0"

    query += " ORDER BY rating DESC LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)
    users = cursor.fetchall()
    conn.close()
    return users


def add_rating(from_user_id, to_user_id, stars):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO ratings (from_user_id, to_user_id, stars)
        VALUES (?, ?, ?)
    """, (from_user_id, to_user_id, stars))

    cursor.execute("""
        SELECT AVG(stars) FROM ratings WHERE to_user_id = ?
    """, (to_user_id,))
    avg = cursor.fetchone()[0]

    if avg:
        cursor.execute("""
            UPDATE users SET rating = ? WHERE user_id = ?
        """, (round(avg, 2), to_user_id))

    conn.commit()
    conn.close()


# ===== АНАЛИТИКА =====

def log_event(user_id: int, event_type: str, event_data: str = ""):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO events (user_id, event_type, event_data)
        VALUES (?, ?, ?)
    """, (user_id, event_type, event_data))
    conn.commit()
    conn.close()


def update_last_seen(user_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users SET last_seen = CURRENT_TIMESTAMP
        WHERE user_id = ?
    """, (user_id,))
    conn.commit()
    conn.close()


def get_stats() -> dict:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    stats = {}

    cursor.execute("SELECT COUNT(*) FROM users")
    stats["total_users"] = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM users
        WHERE last_seen >= datetime('now', '-1 day')
    """)
    stats["active_24h"] = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM users
        WHERE last_seen >= datetime('now', '-7 days')
    """)
    stats["active_7d"] = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM users
        WHERE game IS NOT NULL AND rank IS NOT NULL
    """)
    stats["filled_profiles"] = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM events WHERE event_type = 'find'
    """)
    stats["total_finds"] = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM events
        WHERE event_type = 'find'
        AND created_at >= datetime('now', '-1 day')
    """)
    stats["finds_24h"] = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM events WHERE event_type = 'message_sent'
    """)
    stats["total_messages"] = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM events
        WHERE event_type = 'message_sent'
        AND created_at >= datetime('now', '-1 day')
    """)
    stats["messages_24h"] = cursor.fetchone()[0]

    cursor.execute("""
        SELECT game, COUNT(*) as cnt FROM users
        WHERE game IS NOT NULL
        GROUP BY game
        ORDER BY cnt DESC
        LIMIT 5
    """)
    stats["top_games"] = cursor.fetchall()

    cursor.execute("""
        SELECT rank, COUNT(*) as cnt FROM users
        WHERE rank IS NOT NULL
        GROUP BY rank
        ORDER BY cnt DESC
        LIMIT 5
    """)
    stats["top_ranks"] = cursor.fetchall()

    cursor.execute("""
        SELECT user_id, username, created_at FROM users
        ORDER BY created_at DESC
        LIMIT 10
    """)
    stats["recent_users"] = cursor.fetchall()

    conn.close()
    return stats


def get_user_stats(user_id: int) -> dict:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    stats = {}

    cursor.execute("""
        SELECT COUNT(*) FROM events
        WHERE user_id = ? AND event_type = 'find'
    """, (user_id,))
    stats["finds"] = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM events
        WHERE user_id = ? AND event_type = 'profile_update'
    """, (user_id,))
    stats["profile_updates"] = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM events
        WHERE user_id = ? AND event_type = 'message_sent'
    """, (user_id,))
    stats["messages_sent"] = cursor.fetchone()[0]

    cursor.execute("""
        SELECT created_at FROM users WHERE user_id = ?
    """, (user_id,))
    row = cursor.fetchone()
    stats["registered_at"] = row[0] if row else None

    conn.close()
    return stats


# ===== УПРАВЛЕНИЕ РЕЙТИНГОМ =====

def set_user_rating(user_id: int, rating: float) -> bool:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if not cursor.fetchone():
        conn.close()
        return False

    rating = max(0.0, min(10.0, rating))

    cursor.execute("""
        UPDATE users SET rating = ? WHERE user_id = ?
    """, (rating, user_id))

    conn.commit()
    conn.close()
    return True


def get_user_rating(user_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT rating FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


def reset_user_rating(user_id: int) -> bool:
    return set_user_rating(user_id, 5.0)


def get_all_users(limit: int = 50, offset: int = 0) -> list:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT user_id, username, game, rank, rating
        FROM users
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
    """, (limit, offset))
    users = cursor.fetchall()
    conn.close()
    return users


def get_users_count() -> int:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    conn.close()
    return count


def find_user_by_username(username: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT user_id, username, game, rank, rating
        FROM users
        WHERE username LIKE ?
    """, (f"%{username}%",))
    users = cursor.fetchall()
    conn.close()
    return users


# ===== ИГРЫ =====

def get_active_games():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name, emoji FROM games
        WHERE is_active = 1
        ORDER BY name
    """)
    games = cursor.fetchall()
    conn.close()
    return games


def get_all_games():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name, emoji, is_active FROM games
        ORDER BY name
    """)
    games = cursor.fetchall()
    conn.close()
    return games


def add_game(name: str, emoji: str = "🎮") -> bool:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO games (name, emoji)
            VALUES (?, ?)
        """, (name, emoji))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False


def delete_game(name: str) -> bool:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM games WHERE name = ?", (name,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def toggle_game(name: str) -> bool:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE games
        SET is_active = CASE WHEN is_active = 1 THEN 0 ELSE 1 END
        WHERE name = ?
    """, (name,))
    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return updated


# ===== СООБЩЕНИЯ =====

def save_message(from_user_id: int, to_user_id: int, text: str) -> int:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO messages (from_user_id, to_user_id, text)
        VALUES (?, ?, ?)
    """, (from_user_id, to_user_id, text))
    message_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return message_id


def get_inbox(user_id: int, limit: int = 10):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT m.id, m.from_user_id, u.username, m.text, m.created_at, m.is_read
        FROM messages m
        LEFT JOIN users u ON m.from_user_id = u.user_id
        WHERE m.to_user_id = ?
        ORDER BY m.created_at DESC
        LIMIT ?
    """, (user_id, limit))
    messages = cursor.fetchall()
    conn.close()
    return messages


def get_conversation(user1_id: int, user2_id: int, limit: int = 20):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT from_user_id, text, created_at
        FROM messages
        WHERE (from_user_id = ? AND to_user_id = ?)
           OR (from_user_id = ? AND to_user_id = ?)
        ORDER BY created_at ASC
        LIMIT ?
    """, (user1_id, user2_id, user2_id, user1_id, limit))
    messages = cursor.fetchall()
    conn.close()
    return messages


def mark_as_read(user_id: int, from_user_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE messages
        SET is_read = 1
        WHERE to_user_id = ? AND from_user_id = ?
    """, (user_id, from_user_id))
    conn.commit()
    conn.close()


def count_unread(user_id: int) -> int:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM messages
        WHERE to_user_id = ? AND is_read = 0
    """, (user_id,))
    count = cursor.fetchone()[0]
    conn.close()
    return count


def get_last_sender(user_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT from_user_id FROM messages
        WHERE to_user_id = ?
        ORDER BY created_at DESC
        LIMIT 1
    """, (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None