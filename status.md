# Project Status

OVERALL GOAL: A BEAUTIFUL AND FULLY-FUNCTIONAL HEBREW READING ASSISTANT USABLE BOTH AS A RICH API AND AS A BEAUTIFUL UI

How to do your work:
1) Read this file
2) Do the work outlined in it
3) Output the work you did in a timestamped status file.
4) Edit this file to contain the next chunk of work to be done.
5) If you think there is no work to be done to meet the overall goal, mark that you are totally done (see bottom of this file). 

Last updated: 2026-02-24

## Current State
- Backend v1 API is implemented in FastAPI + SQLite.
- Health endpoint, JSON error envelope, user lifecycle, per-user private texts, sentence load flow, token normalization, word states, per-text progress, meanings generation, and integration tests are in place.
- Sample short story in easy modern Hebrew with full nikkud is available at `data/sample_story_he_nikkud.txt`.
- Developer loop helpers were added: `Makefile` targets and `scripts/smoke.sh`.

## Validation Baseline
- Automated tests pass (`9 passed`).
- Seed script works and creates demo user/text in local DB.
- Stronger path-ID validation is in place (`invalid_user_id`, `invalid_text_id`, `invalid_meaning_id`).

## Remaining Work Toward "Totally Done"
- Build and integrate the frontend UI from `frontend-v1-spec.md`.
- Connect UI flows to backend endpoints end-to-end:
  - user selection and lifecycle actions
  - text import/list/details
  - sentence-by-sentence reading view with prev/next navigation
  - word state updates and filtered/paginated word list
  - per-text progress display
  - meanings list/generate/delete UX and error handling
- Add frontend tests and/or smoke coverage for core user journeys.
- Verify full product flow locally as a family-ready app.

## Working Goals (Next Chunks)
1. Scaffold frontend app structure and API client contract.
2. Implement core pages/components for users, texts, reader, words, and meanings.
3. Add robust form/input validation and empty/error states in UI.
4. Add integration/smoke checks that validate backend + frontend together.
5. Update docs with one-command local run instructions for full stack.

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
