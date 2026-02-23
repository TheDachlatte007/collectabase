import os
import sqlite3
from contextlib import contextmanager

_db_url = os.getenv("DATABASE_URL", "sqlite:////app/app/data/games.db")
if _db_url.startswith("sqlite:////"):
    DATABASE_PATH = _db_url.replace("sqlite:////", "/")
else:
    DATABASE_PATH = _db_url.replace("sqlite:///", "")


@contextmanager
def get_db():
    """Context manager for sqlite connections."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def dict_from_row(row):
    return dict(row) if row else None


def set_app_meta(key: str, value: str):
    with get_db() as db:
        db.execute(
            """
            INSERT INTO app_meta (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(key) DO UPDATE SET
              value = excluded.value,
              updated_at = CURRENT_TIMESTAMP
            """,
            (key, str(value)),
        )
        db.commit()


def get_app_meta_many(keys):
    if not keys:
        return {}
    placeholders = ",".join("?" for _ in keys)
    with get_db() as db:
        rows = db.execute(
            f"SELECT key, value, updated_at FROM app_meta WHERE key IN ({placeholders})",
            tuple(keys),
        ).fetchall()
    return {row["key"]: {"value": row["value"], "updated_at": row["updated_at"]} for row in rows}


def init_db():
    """Initialize schema and default platform seed."""
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

    with get_db() as db:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS platforms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                manufacturer TEXT,
                type TEXT
            )
            """
        )

        db.execute(
            """
            CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                platform_id INTEGER,
                barcode TEXT,
                igdb_id INTEGER,
                release_date TEXT,
                publisher TEXT,
                developer TEXT,
                genre TEXT,
                description TEXT,
                cover_url TEXT,
                region TEXT,
                condition TEXT,
                completeness TEXT,
                location TEXT,
                purchase_date TEXT,
                purchase_price REAL,
                current_value REAL,
                notes TEXT,
                is_wishlist INTEGER DEFAULT 0,
                wishlist_max_price REAL,
                item_type TEXT DEFAULT 'game',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (platform_id) REFERENCES platforms(id)
            )
            """
        )

        db.execute(
            """
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id INTEGER NOT NULL,
                source TEXT DEFAULT 'pricecharting',
                loose_price REAL,
                complete_price REAL,
                new_price REAL,
                eur_rate REAL,
                pricecharting_id TEXT,
                fetched_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE
            )
            """
        )

        db.execute(
            """
            CREATE TABLE IF NOT EXISTS price_catalog (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                pricecharting_id TEXT,
                title            TEXT NOT NULL,
                platform         TEXT NOT NULL,
                loose_usd        REAL,
                cib_usd          REAL,
                new_usd          REAL,
                loose_eur        REAL,
                cib_eur          REAL,
                new_eur          REAL,
                page_url         TEXT,
                scraped_at       TEXT DEFAULT CURRENT_TIMESTAMP,
                changed_at       TEXT
            )
            """
        )
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS app_meta (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        db.execute(
            "CREATE INDEX IF NOT EXISTS idx_price_catalog_title ON price_catalog(title COLLATE NOCASE)"
        )
        db.execute(
            "CREATE INDEX IF NOT EXISTS idx_price_catalog_platform ON price_catalog(platform)"
        )
        db.execute(
            "CREATE INDEX IF NOT EXISTS idx_price_catalog_platform_title ON price_catalog(platform, title COLLATE NOCASE)"
        )
        db.execute(
            "CREATE INDEX IF NOT EXISTS idx_price_catalog_platform_pcid ON price_catalog(platform, pricecharting_id)"
        )

        try:
            db.execute("ALTER TABLE games ADD COLUMN item_type TEXT DEFAULT 'game'")
        except sqlite3.OperationalError:
            pass
        try:
            db.execute("ALTER TABLE price_catalog ADD COLUMN changed_at TEXT")
        except sqlite3.OperationalError:
            pass
        db.execute(
            "UPDATE price_catalog SET changed_at = scraped_at WHERE changed_at IS NULL"
        )

        default_platforms = [
            ("PlayStation 5", "Sony", "Console"),
            ("PlayStation 4", "Sony", "Console"),
            ("PlayStation 3", "Sony", "Console"),
            ("PlayStation 2", "Sony", "Console"),
            ("PlayStation", "Sony", "Console"),
            ("PSP", "Sony", "Handheld"),
            ("PS Vita", "Sony", "Handheld"),
            ("Xbox Series X/S", "Microsoft", "Console"),
            ("Xbox One", "Microsoft", "Console"),
            ("Xbox 360", "Microsoft", "Console"),
            ("Xbox", "Microsoft", "Console"),
            ("Nintendo Switch", "Nintendo", "Console"),
            ("Nintendo Switch 2", "Nintendo", "Console"),
            ("Wii U", "Nintendo", "Console"),
            ("Wii", "Nintendo", "Console"),
            ("GameCube", "Nintendo", "Console"),
            ("Nintendo 64", "Nintendo", "Console"),
            ("SNES", "Nintendo", "Console"),
            ("NES", "Nintendo", "Console"),
            ("Game Boy Advance", "Nintendo", "Handheld"),
            ("Game Boy Color", "Nintendo", "Handheld"),
            ("Game Boy", "Nintendo", "Handheld"),
            ("Nintendo 3DS", "Nintendo", "Handheld"),
            ("Nintendo DS", "Nintendo", "Handheld"),
            ("PC", "Various", "PC"),
            ("Sega Dreamcast", "Sega", "Console"),
            ("Sega Saturn", "Sega", "Console"),
            ("Sega Genesis/Mega Drive", "Sega", "Console"),
            ("Sega Master System", "Sega", "Console"),
            ("Sega Game Gear", "Sega", "Handheld"),
        ]
        for name, manufacturer, type_ in default_platforms:
            db.execute(
                "INSERT OR IGNORE INTO platforms (name, manufacturer, type) VALUES (?, ?, ?)",
                (name, manufacturer, type_),
            )

        db.execute(
            """
            UPDATE games SET item_type = 'console'
            WHERE item_type = 'game'
            AND platform_id IN (
                SELECT id FROM platforms WHERE type IN ('Console', 'Handheld')
            )
            AND (
                LOWER(title) LIKE '%console%'
                OR LOWER(title) LIKE '%system%'
                OR LOWER(title) LIKE '% wii %'
                OR LOWER(title) LIKE '%nintendo wii%'
                OR LOWER(title) LIKE '%playstation%'
                OR LOWER(title) LIKE '%xbox%'
                OR LOWER(title) LIKE '%game boy%'
                OR LOWER(title) LIKE '%gameboy%'
                OR LOWER(title) LIKE '%nintendo 64%'
                OR LOWER(title) LIKE '%dreamcast%'
            )
            """
        )
        db.commit()
