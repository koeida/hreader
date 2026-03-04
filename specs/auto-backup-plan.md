# Auto-Backup Implementation Plan

---

## Stage 1: Backend — `app/backup.py`

Create a standalone backup module with no dependencies on FastAPI.

**Steps:**
1. Create `app/backup.py` with:
   - `BACKUP_DIR = Path.home() / ".hreader" / "backups"`
   - `run_backup(db_path: Path) -> Path` — copies DB to `BACKUP_DIR/hreader-YYYY-MM-DD.db`, creates dir if needed, returns the backup path
   - `prune_old_backups(backup_dir: Path, keep: int = 7)` — deletes all but the `keep` most recent `.db` files
   - `get_last_backup_date(backup_dir: Path) -> date | None` — returns the date of the most recent backup file, or None

**Validation gates:**
- [ ] `run_backup()` produces a file at the expected path with the correct date in the filename
- [ ] Running `run_backup()` twice on the same day overwrites rather than duplicating
- [ ] `prune_old_backups()` with 8 files present leaves exactly 7
- [ ] `get_last_backup_date()` returns `None` when no backups exist
- [ ] Unit tests covering all three functions pass

---

## Stage 2: Backend — Wire into `app/main.py`

**Steps:**
1. In `lifespan`, initialize `app.state.backup_last_date = None` and `app.state.backup_failed = False`
2. Add a middleware that on every request:
   - Checks if `date.today() > app.state.backup_last_date`
   - If so, attempts `run_backup()` + `prune_old_backups()` once
   - Sets `app.state.backup_last_date = date.today()` and `backup_failed = False` on success, `backup_failed = True` on exception
3. Add `GET /v1/backup/status` endpoint returning:
   ```json
   { "last_backup_date": "2025-03-02", "status": "ok" | "overdue" | "failed" }
   ```
   - `ok` — `backup_last_date == today` and not failed
   - `failed` — `backup_last_date == today` but `backup_failed`
   - `overdue` — `backup_last_date` is None or before today

**Validation gates:**
- [ ] `GET /v1/backup/status` returns `overdue` on a fresh app start before any backup has run
- [ ] After the first non-backup-status request, a backup file exists and status returns `ok`
- [ ] A second request on the same day does not trigger a second backup (file mtime unchanged)
- [ ] Status returns `failed` when `run_backup` is patched to throw
- [ ] Existing tests still pass

---

## Stage 3: Frontend — Status Indicator

**Steps:**
1. `index.html`: add `<span id="backup-status"></span>` in the header, next to the subtitle
2. `app.js`:
   - Fetch `/v1/backup/status` on page load
   - Render into `#backup-status`:
     - `ok` → `✓ backed up DATE` (muted)
     - `overdue` → `⚠ no backup yet`
     - `failed` → `⚠ backup failed`
3. `styles.css`: small font, muted color for ok, amber for warning

**Validation gates:**
- [ ] Status indicator is visible in the header on page load
- [ ] Shows correct text for each of the three states (verify by temporarily forcing each from the backend)
- [ ] `ok` state is visually unobtrusive — doesn't compete with the title
- [ ] `overdue` and `failed` states are visually distinct (amber/warning color)
- [ ] Indicator does not appear or shows a neutral state if the API call fails

---

## Stage 4: End-to-End Smoke Test

**Steps:**
1. Start a clean app instance
2. Confirm status shows `overdue` in the UI on first load
3. Make any API call (e.g. `GET /health`) — confirm backup file created in `~/.hreader/backups/`
4. Reload page — confirm status shows `✓ backed up` with today's date
5. Restart app, reload — confirm status still shows `ok` (backup persists across restarts)
6. Seed 8 days' worth of dummy backup files, restart, make a request — confirm oldest is pruned, 7 remain

**Validation gates:**
- [ ] All of the above manual checks pass
- [ ] Full test suite (`make test`) passes
