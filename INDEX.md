# hreader Documentation Index

Quick links to get oriented. Pick your role:

## I'm an LLM / New Developer

Start here: **[`docs/DEVELOPER.md`](docs/DEVELOPER.md)**

One-page reference with:
- Project structure & file purposes
- Key subsystems (SRS, backup, tokenization)
- Database schema overview
- Architecture patterns to follow
- Common tasks (add endpoint, modify schema, etc.)

## I'm Running This Locally

Start here: **[`README.md`](README.md)**

- Setup commands (make venv, make install, make run)
- Testing (make test, make smoke-local)
- Visual QA (make visual-qa)
- API endpoint list
- Sample data and seeding

## I'm Implementing a Feature

1. Check constraints in `AGENTS.md` (desktop only, inline panels, etc.)
2. Read relevant spec in `specs/` folder:
   - `specs/srs-feature-spec.md` — Spaced repetition system
   - `specs/auto-backup-plan.md` — Daily backup automation
   - `specs/word-details-reader-panel-spec.md` — Inline word details UI
3. Review `docs/DEVELOPER.md` for code patterns
4. Write tests in `tests/` before coding
5. Run `make test` to validate

## I'm Reviewing Code Quality

- `docs/v1-checklist.md` — Feature completeness checklist
- `docs/visual-qa.md` — UI screenshot validation
- `docs/ui-beauty-spec.md` — Design guidelines
- `docs/qa-reports/` — Automated test results

## I'm Diving Deep on a Subsystem

| System | Files | Spec |
|--------|-------|------|
| **SRS (Spaced Repetition)** | `app/main.py:get_srs_session()`, `srs_window_bounds()` | `specs/srs-feature-spec.md` |
| **Backup** | `app/backup.py`, `app/main.py:backup_middleware()` | `specs/auto-backup-plan.md` |
| **Tokenization** | `app/tokenizer.py` | — |
| **Meanings** | `app/meanings.py` | — |
| **Frontend State** | `app/static/app.js:state` object | — |

---

## Document Overview

| Document | Purpose | For Whom |
|----------|---------|----------|
| [`README.md`](README.md) | Setup, run, test, deploy | Everyone |
| [`docs/DEVELOPER.md`](docs/DEVELOPER.md) | Code structure & patterns | Developers, LLMs |
| [`AGENTS.md`](AGENTS.md) | Product constraints & UX rules | All contributors |
| [`specs/srs-feature-spec.md`](specs/srs-feature-spec.md) | SRS design & implementation | SRS feature work |
| [`specs/auto-backup-plan.md`](specs/auto-backup-plan.md) | Backup strategy & testing | Backup work |
| [`specs/word-details-reader-panel-spec.md`](specs/word-details-reader-panel-spec.md) | Inline word details UI | Reader/UI work |
| [`docs/visual-qa.md`](docs/visual-qa.md) | UI screenshot checklist | QA, design review |
| [`docs/ui-beauty-spec.md`](docs/ui-beauty-spec.md) | Design guidelines | UI/CSS work |
| [`docs/v1-checklist.md`](docs/v1-checklist.md) | Feature completion tracker | Project leads |

---

## Source Code Map

```
app/
  ├─ main.py           ~1000 LOC: routes, SRS logic, helpers
  ├─ db.py             Schema DDL, connection pooling
  ├─ models.py         ~40 Pydantic request/response models
  ├─ tokenizer.py      Hebrew text parsing, nikkud handling
  ├─ meanings.py       AI meaning generation (codex exec)
  ├─ backup.py         Daily backup automation
  └─ static/
      ├─ app.js        ~1600 LOC: all frontend logic & UI
      ├─ index.html    SPA shell, 4-panel layout
      └─ styles.css    Responsive design, theme

tests/
  ├─ test_api.py       API endpoint tests
  ├─ test_frontend.py   Asset & hook tests
  ├─ test_ui_browser.py Playwright journey tests
  └─ test_backup.py    Backup module tests

docs/
  ├─ DEVELOPER.md      ← START HERE (for code)
  ├─ v1-checklist.md   Feature completion status
  ├─ visual-qa.md      UI snapshot checklist
  ├─ ui-beauty-spec.md Design guidelines
  └─ qa-reports/       Automated test reports

specs/
  ├─ srs-feature-spec.md              SRS design
  ├─ auto-backup-plan.md              Backup design
  └─ word-details-reader-panel-spec.md Word panel design

data/
  └─ hreader.db        SQLite database
```

---

## Quick Reference

**Key commands:**
```bash
make venv       # Create venv
make install    # Install deps + Playwright
make run        # Start server on :8000
make test       # Run all tests
make smoke-local # Quick smoke test
make visual-qa  # Generate UI screenshots
```

**Health check:**
```bash
curl http://127.0.0.1:8000/health
```

**SRS endpoint (example):**
```bash
curl "http://127.0.0.1:8000/v1/users/<USER_ID>/srs/session?timezone_offset_minutes=0"
```

---

**Last Updated:** 2026-03-04
