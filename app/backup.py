"""Standalone database backup module with no FastAPI dependencies."""

import shutil
from datetime import date
from pathlib import Path


BACKUP_DIR = Path.home() / ".hreader" / "backups"


def run_backup(db_path: Path) -> Path:
    """
    Copy the database to BACKUP_DIR with today's date in the filename.
    Creates BACKUP_DIR if it doesn't exist.
    Overwrites if a backup already exists for today.

    Args:
        db_path: Path to the source database file

    Returns:
        Path to the created backup file

    Raises:
        FileNotFoundError: If the database file doesn't exist
    """
    if not db_path.exists():
        raise FileNotFoundError(f"Database file not found: {db_path}")

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    backup_filename = f"hreader-{date.today().isoformat()}.db"
    backup_path = BACKUP_DIR / backup_filename

    shutil.copy2(db_path, backup_path)
    return backup_path


def prune_old_backups(backup_dir: Path, keep: int = 7) -> None:
    """
    Delete all but the `keep` most recent .db backup files in the directory.

    Args:
        backup_dir: Path to the backups directory
        keep: Number of recent backups to retain (default 7)
    """
    if not backup_dir.exists():
        return

    backup_files = sorted(backup_dir.glob("*.db"), key=lambda p: p.stat().st_mtime, reverse=True)

    # Delete files beyond the keep count
    for old_backup in backup_files[keep:]:
        old_backup.unlink()


def get_last_backup_date(backup_dir: Path) -> date | None:
    """
    Return the date of the most recent .db backup file, or None if no backups exist.

    Args:
        backup_dir: Path to the backups directory

    Returns:
        date object of the most recent backup, or None
    """
    if not backup_dir.exists():
        return None

    backup_files = list(backup_dir.glob("*.db"))
    if not backup_files:
        return None

    # Find the most recent file by mtime
    most_recent = max(backup_files, key=lambda p: p.stat().st_mtime)

    # Extract date from filename (hreader-YYYY-MM-DD.db)
    try:
        date_str = most_recent.stem.replace("hreader-", "")
        return date.fromisoformat(date_str)
    except (ValueError, AttributeError):
        return None
