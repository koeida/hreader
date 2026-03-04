# SRS Feature Spec

## Scope
Build a new desktop `SRS` view where unknown words are reviewed with fixed-interval spaced repetition.
No mobile behavior; desktop only.

## Confirmed Product Rules
1. Marking a word `unknown` immediately creates/updates an SRS card with `due_at = now` and marks it as `new`.
2. `new` cards are not part of mandatory due reviews until explicitly introduced via "add new cards."
3. In SRS, user must clear all due reviews first, including cards answered wrong in the same session.
4. After due queue is empty, prompt for number of new cards with default `10`.
5. Daily new-card cap is `20`, reset at user-local `03:30`.
6. If requested new count exceeds available, add all remaining.
7. Due review order is randomized.
8. Selected new cards come from oldest-new first, then randomized for presentation.
9. Reviewer flow: front (word) -> reveal (space or Show) -> definitions + mnemonic -> answer.
10. Keyboard: `Space` = show answer, `0` = wrong, `1` = right.
11. Right uses fixed intervals: `1,2,4,7,12,21,35,56` days; then stays at `56`.
12. Wrong resets card to first stage and `due_at = now`.
13. Wrong cards must reappear in same session with minimum spacing of `2` other cards when possible; otherwise at back.
14. If mnemonic is empty in review, user can type/save one inline there.
15. If no due and no new available: show "All caught up" with link to stats placeholder.

## Data Model Changes
1. Add table `srs_cards` in `app/db.py`:
   - `user_id TEXT`, `normalized_word TEXT`, PK `(user_id, normalized_word)`
   - `is_new INTEGER NOT NULL DEFAULT 1`
   - `is_introduced INTEGER NOT NULL DEFAULT 0`
   - `stage_index INTEGER NOT NULL DEFAULT 0`
   - `due_at TEXT NOT NULL`
   - `introduced_at TEXT NULL`
   - `last_reviewed_at TEXT NULL`
   - `created_at TEXT NOT NULL`, `updated_at TEXT NOT NULL`
2. Add table `srs_daily_new_counts`:
   - `user_id TEXT`, `window_start_at TEXT`, `new_count INTEGER`
   - PK `(user_id, window_start_at)`
3. Add indexes:
   - `(user_id, is_introduced, due_at)`
   - `(user_id, is_new, created_at)`

## Backend API Additions
1. Extend word state update in `app/main.py`:
   - On `unknown`: upsert `srs_cards` with `is_new=1`, `is_introduced=0`, `stage_index=0`, `due_at=now`.
   - On `known` or `never_seen`: remove/deactivate SRS card for that word.
2. Add `GET /v1/users/{user_id}/srs/session`:
   - Returns due introduced cards (randomized), daily new remaining, available new count, reset timestamp.
3. Add `POST /v1/users/{user_id}/srs/session/add-new` with `{count}`:
   - Enforce daily cap window (local 03:30 logic using client timezone offset passed from frontend).
   - Select oldest `is_new=1,is_introduced=0` cards, limit by requested count and cap remaining.
   - Mark selected as introduced (`is_introduced=1,is_new=0,introduced_at=now`).
   - Return selected cards randomized.
4. Add `POST /v1/users/{user_id}/srs/review` with `{normalized_word, result: "right"|"wrong"}`:
   - `right`: `stage_index=min(stage+1,7)`, `due_at=now + interval[stage_index]`.
   - `wrong`: `stage_index=0`, `due_at=now`.
   - Return updated card payload.
5. Add response models in `app/models.py` for SRS session/review payloads.
6. Reuse existing meanings/details endpoints for definitions and mnemonic.

## Frontend Changes
1. Add `SRS` tab in `app/static/index.html` and include in view order in `app/static/app.js`.
2. Add SRS panel UI:
   - Card front with word.
   - Reveal state with definitions list + mnemonic editor.
   - Buttons: `Show`, `Wrong`, `Right`.
   - "Add new cards" prompt with default value `10`.
   - "All caught up" state with stats link placeholder.
3. Session queue logic in `app.js`:
   - Load due queue from session endpoint; shuffle.
   - Block add-new while due queue non-empty.
   - After wrong answer, reinsert card with min-gap-2 strategy; fallback append back.
   - Auto-advance after right/wrong.
4. Keyboard handling (only when SRS view active and no textarea focused):
   - `Space` reveals answer.
   - `0` submits wrong.
   - `1` submits right.
5. Mnemonic behavior:
   - If empty, show input and save action inline in SRS reveal state.
   - Use existing `updateWordDetails`.

## Implementation Steps
1. Add DB schema + indexes + init migration-safe `CREATE TABLE IF NOT EXISTS`.
2. Add SRS Pydantic models.
3. Implement SRS backend endpoints and word-state hook behavior.
4. Extend API client methods in `app.js`.
5. Add SRS view markup + style rules in `app/static/styles.css`.
6. Implement SRS state machine in frontend (`hidden -> revealed -> graded -> next`).
7. Wire keyboard shortcuts and focus guards.
8. Add/update tests.

## Verification Steps
1. Backend tests in `tests/test_api.py`:
   - Unknown creates new SRS card due now.
   - New cards excluded from due queue until added.
   - Daily cap 20 enforced with 03:30 window.
   - Add-new oldest-first selection then randomized output.
   - Right interval progression and max 56-day plateau.
   - Wrong resets stage and due now.
   - Known/never_seen removes from SRS.
2. Frontend structure tests in `tests/test_frontend.py`:
   - SRS tab/panel exists.
   - Reviewer controls and mnemonic input present.
3. Browser tests in `tests/test_ui_browser.py`:
   - Mandatory due-first gating.
   - Wrong card reappears same session with min-gap behavior.
   - Keyboard shortcuts (`Space`, `0`, `1`) and auto-advance.
   - Add-new flow default `10`, cap behavior, all-caught-up state.
4. Manual QA:
   - Mark unknown in reader/words and verify immediate SRS card creation.
   - Verify randomized due order and randomized new display order.
   - Verify no mobile-specific adaptations introduced.
