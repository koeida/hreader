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
            language TEXT NOT NULL DEFAULT 'hebrew',
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
            language TEXT NOT NULL DEFAULT 'hebrew',
            normalized_word TEXT NOT NULL,
            state TEXT NOT NULL CHECK(state IN ('known', 'unknown', 'never_seen')),
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            UNIQUE(user_id, language, normalized_word)
        );

        CREATE TABLE IF NOT EXISTS meanings (
            meaning_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            language TEXT NOT NULL DEFAULT 'hebrew',
            normalized_word TEXT NOT NULL,
            meaning_text TEXT NOT NULL,
            source_sentence TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS word_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            language TEXT NOT NULL DEFAULT 'hebrew',
            normalized_word TEXT NOT NULL,
            mnemonic TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            UNIQUE(user_id, language, normalized_word)
        );

        CREATE TABLE IF NOT EXISTS user_text_positions (
            user_id TEXT NOT NULL,
            text_id TEXT NOT NULL,
            sentence_index INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (user_id, text_id),
            FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY(text_id) REFERENCES texts(text_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS srs_cards (
            user_id TEXT NOT NULL,
            language TEXT NOT NULL DEFAULT 'hebrew',
            normalized_word TEXT NOT NULL,
            is_new INTEGER NOT NULL DEFAULT 1,
            is_introduced INTEGER NOT NULL DEFAULT 0,
            stage_index INTEGER NOT NULL DEFAULT 0,
            due_at TEXT NOT NULL,
            introduced_at TEXT,
            last_reviewed_at TEXT,
            deleted_at TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (user_id, language, normalized_word),
            FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS srs_daily_new_counts (
            user_id TEXT NOT NULL,
            language TEXT NOT NULL DEFAULT 'hebrew',
            window_start_at TEXT NOT NULL,
            new_count INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (user_id, language, window_start_at),
            FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_users_deleted_at ON users(deleted_at);
        CREATE INDEX IF NOT EXISTS idx_texts_user_id ON texts(user_id);
        CREATE INDEX IF NOT EXISTS idx_sentences_text_id ON text_sentences(text_id, sentence_index);
        CREATE INDEX IF NOT EXISTS idx_words_user_state ON user_words(user_id, language, state);
        CREATE INDEX IF NOT EXISTS idx_meanings_user_word ON meanings(user_id, normalized_word, created_at);
        CREATE INDEX IF NOT EXISTS idx_word_details_user_word ON word_details(user_id, normalized_word);
        CREATE INDEX IF NOT EXISTS idx_user_text_positions_user_text ON user_text_positions(user_id, text_id);
        CREATE INDEX IF NOT EXISTS idx_srs_cards_user_due ON srs_cards(user_id, language, due_at);
        CREATE INDEX IF NOT EXISTS idx_srs_cards_user_new ON srs_cards(user_id, language, is_new, is_introduced);

        CREATE TABLE IF NOT EXISTS sentences_read (
            user_id TEXT NOT NULL,
            text_id TEXT NOT NULL,
            sentence_index INTEGER NOT NULL,
            word_count INTEGER NOT NULL DEFAULT 0,
            read_at TEXT NOT NULL,
            PRIMARY KEY (user_id, text_id, sentence_index),
            FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY(text_id) REFERENCES texts(text_id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_sentences_read_user_date ON sentences_read(user_id, read_at);

        CREATE TABLE IF NOT EXISTS dictionary_cache (
            language TEXT NOT NULL DEFAULT 'hebrew',
            normalized_word TEXT NOT NULL,
            lemmas_json TEXT NOT NULL DEFAULT '[]',
            sefaria_json TEXT NOT NULL DEFAULT '[]',
            wiktionary_json TEXT NOT NULL DEFAULT '[]',
            created_at TEXT NOT NULL,
            PRIMARY KEY (language, normalized_word)
        );
        """
    )
    conn.commit()
    _migrate(conn)


def _migrate(conn: sqlite3.Connection) -> None:
    """Idempotent schema migrations. Safe to run on every startup."""
    cols = {row[1] for row in conn.execute("PRAGMA table_info(texts)")}
    if "language" not in cols:
        _run_language_migration(conn)

    sr_cols = {row[1] for row in conn.execute("PRAGMA table_info(sentences_read)")}
    if "nikkud_off" not in sr_cols:
        conn.execute("ALTER TABLE sentences_read ADD COLUMN nikkud_off INTEGER NOT NULL DEFAULT 0")
        conn.commit()

    srs_cols = {row[1] for row in conn.execute("PRAGMA table_info(srs_cards)")}
    if "deleted_at" not in srs_cols:
        conn.execute("ALTER TABLE srs_cards ADD COLUMN deleted_at TEXT")
        conn.commit()


def _run_language_migration(conn: sqlite3.Connection) -> None:
    # Simple ALTER TABLE for tables that just need a new column
    conn.execute("ALTER TABLE texts ADD COLUMN language TEXT NOT NULL DEFAULT 'hebrew'")
    conn.execute("ALTER TABLE meanings ADD COLUMN language TEXT NOT NULL DEFAULT 'hebrew'")
    conn.execute("ALTER TABLE word_details ADD COLUMN language TEXT NOT NULL DEFAULT 'hebrew'")

    # Recreate user_words (UNIQUE constraint change)
    conn.executescript("""
        CREATE TABLE user_words_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            language TEXT NOT NULL DEFAULT 'hebrew',
            normalized_word TEXT NOT NULL,
            state TEXT NOT NULL CHECK(state IN ('known', 'unknown', 'never_seen')),
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            UNIQUE(user_id, language, normalized_word)
        );
        INSERT INTO user_words_new SELECT id, user_id, 'hebrew', normalized_word, state, created_at, updated_at FROM user_words;
        DROP TABLE user_words;
        ALTER TABLE user_words_new RENAME TO user_words;
        CREATE INDEX IF NOT EXISTS idx_words_user_state ON user_words(user_id, language, state);
    """)

    # Recreate srs_cards (PK change)
    conn.executescript("""
        CREATE TABLE srs_cards_new (
            user_id TEXT NOT NULL,
            language TEXT NOT NULL DEFAULT 'hebrew',
            normalized_word TEXT NOT NULL,
            is_new INTEGER NOT NULL DEFAULT 1,
            is_introduced INTEGER NOT NULL DEFAULT 0,
            stage_index INTEGER NOT NULL DEFAULT 0,
            due_at TEXT NOT NULL,
            introduced_at TEXT,
            last_reviewed_at TEXT,
            deleted_at TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (user_id, language, normalized_word),
            FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
        );
        INSERT INTO srs_cards_new SELECT user_id, 'hebrew', normalized_word, is_new, is_introduced, stage_index, due_at, introduced_at, last_reviewed_at, NULL, created_at, updated_at FROM srs_cards;
        DROP TABLE srs_cards;
        ALTER TABLE srs_cards_new RENAME TO srs_cards;
        CREATE INDEX IF NOT EXISTS idx_srs_cards_user_due ON srs_cards(user_id, language, due_at);
        CREATE INDEX IF NOT EXISTS idx_srs_cards_user_new ON srs_cards(user_id, language, is_new, is_introduced);
    """)

    # Recreate srs_daily_new_counts (PK change)
    conn.executescript("""
        CREATE TABLE srs_daily_new_counts_new (
            user_id TEXT NOT NULL,
            language TEXT NOT NULL DEFAULT 'hebrew',
            window_start_at TEXT NOT NULL,
            new_count INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (user_id, language, window_start_at),
            FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
        );
        INSERT INTO srs_daily_new_counts_new SELECT user_id, 'hebrew', window_start_at, new_count FROM srs_daily_new_counts;
        DROP TABLE srs_daily_new_counts;
        ALTER TABLE srs_daily_new_counts_new RENAME TO srs_daily_new_counts;
    """)

    conn.commit()
