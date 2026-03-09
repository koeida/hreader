#!/usr/bin/env python3
"""
Manual backup script. Creates an on-demand backup of the database.
Usage: python scripts/manual_backup.py
"""

from pathlib import Path
import sys

# Add parent directory to path so we can import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.backup import run_backup, BACKUP_DIR

DEFAULT_DB_PATH = Path(__file__).parent.parent / "data" / "hreader.db"

if __name__ == "__main__":
    db_path = DEFAULT_DB_PATH
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        sys.exit(1)

    backup_path = run_backup(db_path)
    print(f"✓ Backup created: {backup_path}")
