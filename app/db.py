from __future__ import annotations

import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path("data/hreader.db")


def get_connection(db_path: str | Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # FastAPI may execute sync dependencies and handlers on different worker threads.
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            display_name TEXT NOT NULL,
            deleted_at TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS texts (
            text_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS text_sentences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text_id TEXT NOT NULL,
            sentence_index INTEGER NOT NULL,
            sentence_text TEXT NOT NULL,
            FOREIGN KEY(text_id) REFERENCES texts(text_id) ON DELETE CASCADE,
            UNIQUE(text_id, sentence_index)
        );

        CREATE TABLE IF NOT EXISTS user_words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            normalized_word TEXT NOT NULL,
            state TEXT NOT NULL CHECK(state IN ('known', 'unknown', 'never_seen')),
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            UNIQUE(user_id, normalized_word)
        );

        CREATE TABLE IF NOT EXISTS meanings (
            meaning_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            normalized_word TEXT NOT NULL,
            meaning_text TEXT NOT NULL,
            source_sentence TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_users_deleted_at ON users(deleted_at);
        CREATE INDEX IF NOT EXISTS idx_texts_user_id ON texts(user_id);
        CREATE INDEX IF NOT EXISTS idx_sentences_text_id ON text_sentences(text_id, sentence_index);
        CREATE INDEX IF NOT EXISTS idx_words_user_state ON user_words(user_id, state, normalized_word);
        CREATE INDEX IF NOT EXISTS idx_meanings_user_word ON meanings(user_id, normalized_word, created_at);
        """
    )
    conn.commit()
