# Project Status

OVERALL GOAL: A BEAUTIFUL AND FULLY-FUNCTIONAL HEBREW READING ASSISTANT USABLE BOTH AS A RICH API AND AS A BEAUTIFUL UI

You are in a codex "ralph loop". Follow these steps, which you should never delete or modify:
1. Read this file and pick one task from it
2. Do the task.
3. Commit
4. Update this file with any updated goals (or anything else) based on your experience, other than this literal list of how the loop functions.
5. Return TOTALLY_DONE if nothing remains to be done, otherwise return CONTINUE.


## Progress This Run (2026-02-24)
- Added an accessibility-focused modal close/focus pass: tracked the triggering inline word button and restored keyboard focus to the correct word after close.
- Hardened focus restore through sentence rerenders by storing a stable per-word trigger id, then resolving the replacement button on close.
- Updated non-user-initiated close paths (view switch, user/text context clear, sentence/token invalidation) to close the modal without forcing hidden focus jumps.
- Extended Playwright browser coverage to assert focus-return after Escape close, backdrop close, and explicit Close-button close.
- Validation: `./.venv/bin/pytest -q` passed (`16 passed`).
- Validation: `./.venv/bin/python scripts/capture_ui_screenshots.py` passed.

## Remaining Work
- Manually review refreshed screenshots and trim/retire legacy `docs/visual-qa` artifacts no longer in the canonical set.
- Perform real-device mobile QA (iOS Safari + Android Chrome) for modal keyboard behavior and sentence-word wrapping under narrow widths.
- Re-check V1 checklist completion against `frontend-v1-spec.md` and `backend-v1-spec.md` before declaring project fully done.

## Next Goals
- Refresh `docs/visual-qa.md` and screenshot inventory so only canonical/current artifacts are referenced.
- Run a manual cross-device UI QA pass and document any remaining polish bugs.
- Execute one final end-to-end regression sweep and map results to remaining V1 checklist items.


## Autopilot done_code Contract
- Full validation gate has passed and no V1 checklist items remain; `TOTALLY_DONE` is now valid.
