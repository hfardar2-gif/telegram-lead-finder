from __future__ import annotations
import sqlite3
from pathlib import Path

SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS groups(id INTEGER PRIMARY KEY, telegram_group_id INTEGER NOT NULL UNIQUE, title TEXT NOT NULL, username TEXT, link TEXT, description TEXT, member_count INTEGER, keyword TEXT, group_type TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, last_scanned_at TEXT, scan_status TEXT NOT NULL DEFAULT 'NOT_SCANNED');
CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, telegram_user_id INTEGER NOT NULL UNIQUE, username TEXT, first_name TEXT, last_name TEXT, display_name TEXT NOT NULL, is_bot INTEGER NOT NULL DEFAULT 0, is_deleted INTEGER NOT NULL DEFAULT 0, first_seen TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, last_seen TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS user_group_activity(id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, group_id INTEGER NOT NULL REFERENCES groups(id) ON DELETE CASCADE, message_count INTEGER NOT NULL DEFAULT 0, first_seen TEXT NOT NULL, last_seen TEXT NOT NULL, activity_score REAL NOT NULL DEFAULT 0, activity_level TEXT NOT NULL DEFAULT 'Low', UNIQUE(user_id, group_id));
CREATE TABLE IF NOT EXISTS search_keywords(id INTEGER PRIMARY KEY, keyword TEXT NOT NULL UNIQUE, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, last_searched_at TEXT, result_count INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS scan_jobs(job_id INTEGER PRIMARY KEY, group_id INTEGER REFERENCES groups(id) ON DELETE SET NULL, started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, finished_at TEXT, messages_scanned INTEGER NOT NULL DEFAULT 0, users_found INTEGER NOT NULL DEFAULT 0, new_users INTEGER NOT NULL DEFAULT 0, status TEXT NOT NULL, error TEXT, resume_after TEXT);
CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT NOT NULL, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE INDEX IF NOT EXISTS idx_activity_group ON user_group_activity(group_id); CREATE INDEX IF NOT EXISTS idx_activity_score ON user_group_activity(activity_score); CREATE INDEX IF NOT EXISTS idx_users_last_seen ON users(last_seen);
"""

class Database:
    def __init__(self, path: Path | str): self.path = Path(path)
    def connect(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(self.path, timeout=30); con.row_factory = sqlite3.Row; con.execute("PRAGMA foreign_keys=ON"); con.execute("PRAGMA journal_mode=WAL"); return con
    def initialize(self):
        with self.connect() as con: con.executescript(SCHEMA)

