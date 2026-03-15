"""SQLite connection, schema, and CRUD for download history."""

import sqlite3
from pathlib import Path
from typing import List, Optional

from .models import DownloadRecord

# Default DB path
RDM_DIR = Path.home() / ".rdm"
DB_PATH = RDM_DIR / "rdm.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS downloads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL,
    filename TEXT NOT NULL,
    size INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'unknown',
    category TEXT NOT NULL DEFAULT 'General',
    date TEXT NOT NULL,
    path TEXT NOT NULL DEFAULT '',
    gid TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_downloads_status ON downloads(status);
CREATE INDEX IF NOT EXISTS idx_downloads_category ON downloads(category);
CREATE INDEX IF NOT EXISTS idx_downloads_date ON downloads(date);
"""


def get_connection(path: Optional[Path] = None) -> sqlite3.Connection:
    """Return a connection to the DB; create dir and schema if needed."""
    p = path or DB_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p))
    conn.executescript(SCHEMA)
    return conn


def insert(
    conn: sqlite3.Connection,
    url: str,
    filename: str,
    size: int = 0,
    status: str = "active",
    category: str = "General",
    path: str = "",
    gid: str = "",
) -> int:
    """Insert a download record. Returns row id."""
    from datetime import datetime

    date = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    cur = conn.execute(
        "INSERT INTO downloads (url, filename, size, status, category, date, path, gid) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (url, filename, size, status, category, date, path, gid),
    )
    conn.commit()
    return cur.lastrowid


def update_status(conn: sqlite3.Connection, gid: str, status: str) -> None:
    conn.execute("UPDATE downloads SET status = ? WHERE gid = ?", (status, gid))
    conn.commit()


def update_status_by_id(conn: sqlite3.Connection, row_id: int, status: str) -> None:
    conn.execute("UPDATE downloads SET status = ? WHERE id = ?", (status, row_id))
    conn.commit()


def delete(conn: sqlite3.Connection, row_id: int) -> None:
    conn.execute("DELETE FROM downloads WHERE id = ?", (row_id,))
    conn.commit()


def get_by_gid(conn: sqlite3.Connection, gid: str) -> Optional[DownloadRecord]:
    cur = conn.execute("SELECT id, url, filename, size, status, category, date, path, gid FROM downloads WHERE gid = ?", (gid,))
    row = cur.fetchone()
    return DownloadRecord.from_row(row) if row else None


def get_all(
    conn: sqlite3.Connection,
    category: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 500,
) -> List[DownloadRecord]:
    """Return download records, optionally filtered."""
    query = "SELECT id, url, filename, size, status, category, date, path, gid FROM downloads WHERE 1=1"
    params: list = []
    if category:
        query += " AND category = ?"
        params.append(category)
    if status:
        query += " AND status = ?"
        params.append(status)
    if search:
        query += " AND (filename LIKE ? OR url LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
    query += " ORDER BY date DESC LIMIT ?"
    params.append(limit)
    cur = conn.execute(query, params)
    return [DownloadRecord.from_row(row) for row in cur.fetchall()]


def clear_history(conn: sqlite3.Connection) -> int:
    """Delete all records. Returns count deleted."""
    cur = conn.execute("DELETE FROM downloads")
    conn.commit()
    return cur.rowcount
