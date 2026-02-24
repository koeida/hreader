# Project Status

OVERALL GOAL: A BEAUTIFUL AND FULLY-FUNCTIONAL HEBREW READING ASSISTANT USABLE BOTH AS A RICH API AND AS A BEAUTIFUL UI

How to do your work:
1) Read this file
2) Do one major feature outlined in it
2.5) Commit your work
3) Output information about the work you did in a timestamped status file in the directory updates/
4) Edit this file to contain the next chunk of work to be done.
5) If you think there is no work to be done to meet the overall goal, mark that you are totally done (see bottom of this file). 

Last updated: 2026-02-24

## Current State
- Backend v1 API is implemented in FastAPI + SQLite.
- Frontend is now scaffolded and integrated as a served SPA-like vanilla JS app at `/` with static assets under `/static/*`.
- Implemented frontend flows:
  - API base URL setting + health check indicator.
  - User list/create/delete/restore/select flow.
  - Per-user text list/create/delete and inline title rename with local validation/error feedback.
  - Reader sentence load + prev/next navigation + direct sentence jump with boundary-safe clamping + inline token state selector (no prompt flow).
  - User word list filter + page/limit controls + prev/next page navigation + single-word state changes.
  - Meanings list/generate/delete for selected token.
- Frontend async panel loading is now version-guarded to prevent stale in-flight responses from overwriting newer user actions (users/texts/sentence/words/meanings loads).
- Added reusable list-state rendering (`Loading...`, `Empty`, error) across users/texts/words/meanings panels and improved reader state messages.
- Added integration coverage for frontend-assisted journeys: inline text rename, sentence navigation/jump boundaries, words pagination, and token-state updates.
- Frontend checks now assert prompt-free interaction hooks plus pagination/jump hooks and stale-request guards.
- Sample short story in easy modern Hebrew with full nikkud is available at `data/sample_story_he_nikkud.txt`.
- Developer loop helpers remain available: `Makefile` targets and `scripts/smoke.sh`.

## Validation Baseline
- Automated tests pass (`14 passed`), including new frontend-assisted journey API integration coverage and stale-request guard checks.
- Seed script works and creates demo user/text in local DB.
- Stronger path-ID validation is in place (`invalid_user_id`, `invalid_text_id`, `invalid_meaning_id`).

## Remaining Work Toward "Totally Done"
- Add browser-level UI automation (or equivalent scripted UI journey) to validate rendered DOM behavior, not only API/static assertions.
- Expand smoke workflow to include rename, multi-page words checks, and a token-state mutation assertion in one script run.
- Final pass on family-ready UX polish/docs checklist with explicit local runbook.

## Working Goals (Next Chunks)
1. Upgrade `scripts/smoke.sh` into a stricter, failing-fast full journey check (rename + jump boundary + paginated words + state mutation verification).
2. Add at least one browser-executed UI journey test (headless) to verify DOM updates across key panels.
3. Finalize README with a concise "family-ready local run checklist" and validation order.

## Completion Gate
Only mark this project as `TOTALLY_DONE` when all are true:
- Backend and frontend specs are implemented.
- Core flows work end-to-end locally.
- Validation/tests/smoke checks pass reliably.
- Documentation reflects final run/test workflow.

## Autopilot done_code Contract
- The autopilot loop expects a JSON field named `done_code`.
- Allowed values are:
  - `CONTINUE`: work is not fully complete yet; continue another loop iteration.
  - `TOTALLY_DONE`: project is fully complete end-to-end and validated; stop the loop.
- Source of truth for schema: `scripts/autopilot_status_schema.json`.
- Loop runner behavior: `scripts/autopilot_status_loop.sh` exits successfully only on `TOTALLY_DONE`.
