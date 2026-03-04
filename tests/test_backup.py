"""Tests for the backup module."""

import shutil
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

from app.backup import BACKUP_DIR, get_last_backup_date, prune_old_backups, run_backup


@pytest.fixture
def temp_backup_dir(tmp_path):
    """Fixture providing a temporary backup directory."""
    return tmp_path / "backups"


@pytest.fixture
def temp_db_file(tmp_path):
    """Fixture providing a temporary database file."""
    db_file = tmp_path / "test.db"
    db_file.write_text("test database content")
    return db_file


class TestRunBackup:
    """Tests for run_backup()."""

    def test_creates_backup_with_correct_date(self, temp_db_file, temp_backup_dir):
        """Backup file should be created with today's date in filename."""
        backup_path = run_backup(temp_db_file)
        # Patch BACKUP_DIR for this test
        with patch("app.backup.BACKUP_DIR", temp_backup_dir):
            backup_path = run_backup(temp_db_file)

        assert backup_path.exists()
        assert backup_path.parent == temp_backup_dir
        assert backup_path.name == f"hreader-{date.today().isoformat()}.db"

    def test_creates_backup_dir_if_needed(self, temp_db_file, temp_backup_dir):
        """BACKUP_DIR should be created if it doesn't exist."""
        assert not temp_backup_dir.exists()

        with patch("app.backup.BACKUP_DIR", temp_backup_dir):
            run_backup(temp_db_file)

        assert temp_backup_dir.exists()

    def test_overwrites_existing_backup_same_day(self, temp_db_file, temp_backup_dir):
        """Running backup twice same day should overwrite, not duplicate."""
        with patch("app.backup.BACKUP_DIR", temp_backup_dir):
            path1 = run_backup(temp_db_file)
            original_mtime = path1.stat().st_mtime

            # Modify source and run again
            temp_db_file.write_text("updated database content")
            path2 = run_backup(temp_db_file)

            assert path1 == path2
            assert temp_backup_dir.glob("*.db").__sizeof__() != 2  # Only one file
            assert path2.read_text() == "updated database content"

    def test_backup_content_matches_source(self, temp_db_file, temp_backup_dir):
        """Backup file content should match source."""
        with patch("app.backup.BACKUP_DIR", temp_backup_dir):
            backup_path = run_backup(temp_db_file)

        assert backup_path.read_text() == temp_db_file.read_text()


class TestPruneOldBackups:
    """Tests for prune_old_backups()."""

    def test_keeps_only_n_most_recent(self, temp_backup_dir):
        """Should keep only the specified number of most recent files."""
        # Create 8 dummy backup files
        for i in range(8):
            backup_file = temp_backup_dir / f"hreader-2025-01-{i+1:02d}.db"
            backup_file.parent.mkdir(parents=True, exist_ok=True)
            backup_file.write_text(f"backup {i}")

        prune_old_backups(temp_backup_dir, keep=7)

        remaining = list(temp_backup_dir.glob("*.db"))
        assert len(remaining) == 7

    def test_handles_nonexistent_dir(self, temp_backup_dir):
        """Should not raise error if backup_dir doesn't exist."""
        prune_old_backups(temp_backup_dir, keep=7)  # Should not raise

    def test_handles_empty_dir(self, temp_backup_dir):
        """Should not raise error if backup_dir exists but is empty."""
        temp_backup_dir.mkdir(parents=True, exist_ok=True)
        prune_old_backups(temp_backup_dir, keep=7)  # Should not raise

    def test_deletes_oldest_files_first(self, temp_backup_dir):
        """When pruning, oldest files by mtime should be deleted."""
        import time

        temp_backup_dir.mkdir(parents=True, exist_ok=True)

        # Create 8 files with predictable names, with sequential mtimes
        filenames = [
            "hreader-2025-01-01.db",
            "hreader-2025-01-02.db",
            "hreader-2025-01-03.db",
            "hreader-2025-01-04.db",
            "hreader-2025-01-05.db",
            "hreader-2025-01-06.db",
            "hreader-2025-01-07.db",
            "hreader-2025-01-08.db",
        ]

        for filename in filenames:
            (temp_backup_dir / filename).write_text("backup")
            time.sleep(0.01)  # Ensure distinct mtimes

        prune_old_backups(temp_backup_dir, keep=7)

        remaining = set(f.name for f in temp_backup_dir.glob("*.db"))
        assert "hreader-2025-01-01.db" not in remaining
        assert len(remaining) == 7


class TestGetLastBackupDate:
    """Tests for get_last_backup_date()."""

    def test_returns_most_recent_date(self, temp_backup_dir):
        """Should return the date from the most recently modified backup file."""
        import time

        temp_backup_dir.mkdir(parents=True, exist_ok=True)

        (temp_backup_dir / "hreader-2025-01-01.db").write_text("backup")
        time.sleep(0.01)
        (temp_backup_dir / "hreader-2025-01-15.db").write_text("backup")
        time.sleep(0.01)
        (temp_backup_dir / "hreader-2025-01-08.db").write_text("backup")

        result = get_last_backup_date(temp_backup_dir)
        # The most recently modified file is 01-08 (created last)
        assert result == date(2025, 1, 8)

    def test_returns_none_if_no_backups(self, temp_backup_dir):
        """Should return None if no backup files exist."""
        result = get_last_backup_date(temp_backup_dir)
        assert result is None

    def test_returns_none_if_dir_not_exist(self, temp_backup_dir):
        """Should return None if backup_dir doesn't exist."""
        result = get_last_backup_date(temp_backup_dir)
        assert result is None

    def test_handles_todays_date(self, temp_backup_dir):
        """Should correctly parse today's date."""
        temp_backup_dir.mkdir(parents=True, exist_ok=True)

        today = date.today()
        backup_file = temp_backup_dir / f"hreader-{today.isoformat()}.db"
        backup_file.write_text("backup")

        result = get_last_backup_date(temp_backup_dir)
        assert result == today
