# Developer Guide: Quick Reference for LLM Context

**Purpose:** Get up to speed on hreader structure, code organization, and key systems without reading the entire codebase.

---

## Project Overview

**Hebrew Reading Helper (hreader)** is a desktop learning app for Hebrew reading. Users read passages, encounter unknown words, mark word states (known/unknown), and use spaced repetition (SRS) to study.

- **Backend:** FastAPI + SQLite (no ORM), ~1000 LOC in main.py
- **Frontend:** Vanilla JS (no framework), ~1600 LOC in app.js
- **Stack:** Python 3.12, SQLite3, vanilla JS, Playwright for tests

---

## Quick File Reference

### Backend (Python)

| File | Purpose | Key Exports |
|------|---------|-------------|
| `app/main.py` | All route handlers, helpers, SRS logic | ~1000 LOC: get/post/patch/delete routes, `srs_window_bounds()`, `to_iso_utc()`, row mappers |
| `app/db.py` | Database initialization, connection | `init_db()`, `get_connection()`, schema DDL |
| `app/models.py` | Pydantic request/response schemas | ~40 models: `UserResponse`, `TextResponse`, `SrsSessionResponse`, etc. |
| `app/tokenizer.py` | Hebrew text tokenization | `tokenize_eligible()`, `normalize_token()`, `NIKKUD_RE` regex |
| `app/meanings.py` | AI meaning generation via subprocess | `MeaningGenerator`, `codex exec` wrapper |
| `app/backup.py` | Daily backup automation | `run_backup()`, `prune_old_backups()`, `get_last_backup_date()` |

### Frontend (JavaScript)

| File | Purpose | Key Objects |
|------|---------|-------------|
| `app/static/app.js` | All UI logic, state management, API client | `ApiClient` class, `state` object, render functions, event handlers (~1600 LOC) |
| `app/static/index.html` | SPA shell: 4-panel layout | User selector, text list, reader, words panel, meanings panel |
| `app/static/styles.css` | All styling | Theme colors, responsive layout, component styles |

### Tests

| File | Coverage |
|------|----------|
| `tests/test_api.py` | API endpoint testing, user/text/word/SRS flows |
| `tests/test_frontend.py` | Served asset checks, UI interaction hooks |
| `tests/test_ui_browser.py` | Headless browser journey (Playwright) |
| `tests/test_backup.py` | Backup module unit tests |

---

## Database Schema (8 Tables)

Quick reference — full DDL in `app/db.py:init_db()`:

- **users** — user accounts, soft-delete support
- **texts** — reading passages per user
- **text_sentences** — sentences split from texts
- **user_words** — word state tracking (known/unknown/never_seen)
- **meanings** — word definitions per user
- **word_details** — mnemonic notes per word
- **user_text_positions** — current read position per text
- **srs_cards** — spaced repetition cards
- **srs_daily_new_counts** — daily new card intro tracking

---

## Key Subsystems

### SRS (Spaced Repetition)

- **Window:** 3:30 AM local to 3:30 AM next day (not midnight)
- **Intervals:** `[1, 2, 4, 7, 12, 21, 35, 56]` days (8 stages)
- **Daily cap:** 20 new cards/day
- **Due logic:** Cards due anytime during the day window, shown all at once (Anki-style)
- **Entry point:** `app/main.py:get_srs_session()`
- **Review:** `app/main.py:review_srs_card()` advances stage or resets to 0
- **Helpers:** `srs_window_bounds()`, `ensure_srs_cards_for_unknown_words()`

**See also:** `specs/srs-feature-spec.md`

### Auto-Backup

- **Location:** `~/.hreader/backups/hreader-YYYY-MM-DD.db`
- **Trigger:** Once per day on first request (middleware at `app/main.py:backup_middleware()`)
- **Retention:** Keeps 7 most recent backups
- **Status endpoint:** `GET /v1/backup/status` returns "ok" | "overdue" | "failed"
- **Module:** `app/backup.py`

**See also:** `specs/auto-backup-plan.md`

### Hebrew Tokenization

- Handles nikkud (vowel marks), normalization, eligibility (skip numbers/punctuation)
- Regex: `NIKKUD_RE` in `app/tokenizer.py`
- **Usage:** Parse reader text into word tokens, track unique normalized forms

### Meaning Generation

- Subprocess call to `codex exec` (AI via CLI)
- Validates English-only output, normalizes whitespace
- Fallback to 502/504 on failure

---

## Architecture Patterns (Follow These!)

### Backend

1. **Row mappers** — Convert SQLite rows to domain objects:
   - `row_to_user()`, `row_to_word()`, `row_to_meaning()`, `row_to_srs_card()`
   - Defined in `app/main.py`, reuse everywhere

2. **Schema DDL** — Lives only in `app/db.py:init_db()`. Never re-declare elsewhere.

3. **DateTime formatting** — Use `to_iso_utc(dt)` (always), `utc_now_iso()` (shorthand)

4. **SRS card sync** — `_sync_srs_card(conn, user_id, normalized, state, now)` on word state change

### Frontend

1. **Request versioning** — `nextRequestVersion(key)` / `isCurrentRequest(key, version)` guard stale responses

2. **Form UX** — Save button text, set to "Saving...", restore in `finally` block

3. **Status messages** — `setStateMessage(el, msg, isError?)` for user feedback

4. **Fire-and-forget async** — `void asyncFn()` pattern for non-critical background tasks

---

## Feature Documentation

### Current Features (Implemented)

- User lifecycle (create/list/delete/restore/select)
- Text library (import/rename/delete with progress tracking)
- Reader view with sentence navigation
- Word state tracking (known/unknown/never_seen)
- Meaning generation and manual entry
- **SRS system with daily windows**
- **Auto-backup with status monitoring**
- Word details panel (inline, desktop only)

**See:** `docs/v1-checklist.md`, `README.md`

### Feature Specs (Detailed)

- `specs/srs-feature-spec.md` — SRS design, card lifecycle, window logic
- `specs/auto-backup-plan.md` — Backup strategy, retention, implementation
- `specs/word-details-reader-panel-spec.md` — Inline word details UI
- `docs/hebrew-word-bubble-ordering-spec.md` — Word bubble display order

### Operational & QA

- `docs/visual-qa.md` — UI screenshot validation checklist
- `docs/ui-beauty-spec.md` — UI design guidelines
- `docs/qa-reports/` — Automated test reports (desktop browsers)

---

## Common Tasks

### Add a New API Endpoint

1. Define request/response model in `app/models.py`
2. Add route handler in `app/main.py` (use `Depends(get_conn)`)
3. Use existing row mappers or create new ones
4. Add test in `tests/test_api.py`

### Modify Database Schema

1. Update `init_db()` in `app/db.py` (table definitions only)
2. Create migration if needed (not automated; manual for now)
3. Update row mapper if columns change
4. Test with `make test`

### Change Frontend UI/Logic

1. Edit `app/static/app.js` (state, render functions, event handlers)
2. Update `app/static/index.html` if DOM structure changes
3. Update CSS in `app/static/styles.css`
4. Test with `make test` (browser journey tests)

### Add Feature Documentation

1. Create spec in `specs/` folder or detailed doc in `docs/`
2. Link from this file (DEVELOPER.md) under "Feature Documentation"
3. Keep main README.md for operational stuff (run/test/deploy)

---

## Running & Testing

```bash
# Setup
make venv && make install

# Run
make run          # starts on :8000

# Test (all automated suites)
make test

# Quick smoke test
make smoke-local

# Visual QA snapshots
make visual-qa
```

See `README.md` for full commands.

---

## Design Constraints (Non-Negotiable)

- **Desktop only** — no mobile UX
- **Reader word details** — inline panel below sentence (never modal/overlay)
- **Default local server** — `http://127.0.0.1:8001/` in AGENTS.md

---

## Codebase Stats

- ~1000 LOC backend (main.py)
- ~1600 LOC frontend (app.js)
- ~300 LOC tests
- ~400 LOC helper modules (tokenizer, backup, meanings)
- ~100 LOC models
- ~50 LOC database

Total ~3.5k LOC (excludes deps).

---

## Next Steps for New Development

1. **Understand the domain:** Read `README.md` (user-facing features)
2. **Review constraints:** Check this file's "Design Constraints" section
3. **Locate relevant code:** Use file reference table above
4. **Check feature spec:** Search `specs/` for related documentation
5. **Study existing patterns:** Look at similar features in `app/main.py` or `app/static/app.js`
6. **Write tests first:** Add test case in `tests/` before coding
7. **Update docs:** Link from this file if creating new features

---

**Last Updated:** 2026-03-04
