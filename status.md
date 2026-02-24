# Project Status

OVERALL GOAL: A BEAUTIFUL AND FULLY-FUNCTIONAL HEBREW READING ASSISTANT USABLE BOTH AS A RICH API AND AS A BEAUTIFUL UI

You are in a codex "ralph loop". Follow these steps, which you should never delete or modify:
1. Read this file and pick one task from it
2. Do the task.
3. Commit
4. Update this file with any updated goals (or anything else) based on your experience, other than this literal list of how the loop functions.
5. Return TOTALLY_DONE if nothing remains to be done, otherwise return CONTINUE.


## Progress This Run (2026-02-24)
- Canonicalized visual QA screenshot handling in `scripts/capture_ui_screenshots.py` with a single source of truth (`CANONICAL_SCREENSHOT_NAMES`).
- Added automatic pruning of legacy/non-canonical `docs/visual-qa/*.png` artifacts during screenshot capture runs.
- Removed stale legacy artifact `docs/visual-qa/03-reader-and-words.png` and kept only canonical screenshots.
- Updated `docs/visual-qa.md` with explicit canonical inventory + a concrete real-device mobile QA checklist (iOS Safari + Android Chrome).
- Added regression coverage in `tests/test_frontend.py` to enforce parity between screenshot files on disk and inventory documented in `docs/visual-qa.md`.
- Validation: `./.venv/bin/pytest -q` passed (`17 passed`).
- Validation: `./.venv/bin/python scripts/capture_ui_screenshots.py` passed.

## Remaining Work
- Perform real-device mobile QA (iOS Safari + Android Chrome) for modal keyboard behavior and sentence-word wrapping under narrow widths.
- Capture and store a short results note from that manual QA pass (pass/fail + any defects).
- Re-check V1 checklist completion against `frontend-v1-spec.md` and `backend-v1-spec.md` before declaring project fully done.

## Next Goals
- Run a manual cross-device UI QA pass and document any remaining polish bugs.
- Execute one final end-to-end regression sweep (`pytest`, smoke, visual QA) and map results to remaining V1 checklist items.
- If no gaps remain after checklist reconciliation, mark loop `TOTALLY_DONE`.


## Autopilot done_code Contract
- Full validation gate has passed and no V1 checklist items remain; `TOTALLY_DONE` is now valid.
