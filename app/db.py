"""SQLite helpers for products and price history."""

import sqlite3
from datetime import datetime, timezone
from app.config import DB_PATH

def _utc_now() -> str:
    """Return current UTC timestamp as ISO string."""
    return datetime.now(timezone.utc).isoformat()

def get_connection() -> sqlite3.Connection:
    """Get a SQLite connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db() -> None:
    """Initialize the database with required tables."""
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL UNIQUE,
                title TEXT,
                last_price REAL,
                availability TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                price REAL,
                availability TEXT,
                scraped_at TEXT NOT NULL,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
            );
            """
        )

def get_product_by_url(url: str):
    """Return one product as a dict, or None."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM products WHERE url = ?",
            (url,),
        ).fetchone()
        return dict(row) if row else None

def get_product_by_id(product_id: int):
    """Return one product by id, or None."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM products WHERE id = ?",
            (product_id,),
        ).fetchone()
        return dict(row) if row else None


def list_products():
    """Return all products, newest updated first."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM products ORDER BY updated_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]

def upsert_product(url: str, title, price, availability):
    """Insert or update a product."""

    now = _utc_now()
    existing = get_product_by_url(url)

    with get_connection() as conn:
        if existing is None:
            cur = conn.execute(
                """
                INSERT INTO products (url, title, last_price, availability, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (url, title, price, availability, now, now)
            )
            product_id = cur.lastrowid
        else:
            conn.execute(
                """
                UPDATE products
                SET title = ?, last_price = ?, availability = ?, updated_at = ?
                WHERE url = ?
                """,
                (title, price, availability, now, url),
            )
            product_id = existing["id"]
        row = conn.execute(
            "SELECT * FROM products WHERE id = ?",
            (product_id,),
        ).fetchone()
        return dict(row)

def add_history(product_id: int, price, availability):
    """Append one price-history row for a product."""
    now = _utc_now()
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO price_history (product_id, price, availability, scraped_at)
            VALUES (?, ?, ?, ?)
            """,
            (product_id, price, availability, now),
        )
        row = conn.execute(
            "SELECT * FROM price_history WHERE id = ?",
            (cur.lastrowid,),
        ).fetchone()
        return dict(row)
    
def get_history(product_id: int | None = None):
    """Return history rows (newest first). Optionally filter by product_id.
    JOIN brings in title/url from products for nicer display later.
    """
    with get_connection() as conn:
        if product_id is None:
            rows = conn.execute(
                """
                SELECT
                    h.id,
                    h.product_id,
                    p.url,
                    p.title,
                    h.price,
                    h.availability,
                    h.scraped_at
                FROM price_history h
                JOIN products p ON p.id = h.product_id
                ORDER BY h.scraped_at DESC
                """
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT
                    h.id,
                    h.product_id,
                    p.url,
                    p.title,
                    h.price,
                    h.availability,
                    h.scraped_at
                FROM price_history h
                JOIN products p ON p.id = h.product_id
                WHERE h.product_id = ?
                ORDER BY h.scraped_at DESC
                """,
                (product_id,),
            ).fetchall()
        return [dict(r) for r in rows]