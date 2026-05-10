"""SQLite connection + schema for the cache layer.

Two tables:
    disclosures   — actual rows, keyed by globally-unique rcept_no.
    fetched_days  — coverage marker per (corp_code, day). A day appears here
                    iff it has been fetched from DART, even if zero rows exist.
                    This is what enables incremental caching (Decisions.md §7).
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from config import CACHE_DB

SCHEMA = """
CREATE TABLE IF NOT EXISTS disclosures (
    rcept_no   TEXT PRIMARY KEY,
    corp_code  TEXT NOT NULL,
    corp_name  TEXT NOT NULL,
    stock_code TEXT,
    corp_cls   TEXT,
    report_nm  TEXT NOT NULL,
    flr_nm     TEXT,
    rcept_dt   TEXT NOT NULL,
    rm         TEXT,
    cached_at  INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_disclosures_corp_date
    ON disclosures(corp_code, rcept_dt);

CREATE TABLE IF NOT EXISTS fetched_days (
    corp_code TEXT NOT NULL,
    rcept_dt  TEXT NOT NULL,
    cached_at INTEGER NOT NULL,
    PRIMARY KEY (corp_code, rcept_dt)
);
"""


def connect(db_path: Path | None = None) -> sqlite3.Connection:
    """Open a connection, ensure the parent dir exists, and apply schema."""
    path = db_path or CACHE_DB
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn
