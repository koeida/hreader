# Project Status

OVERALL GOAL: A BEAUTIFUL AND FULLY-FUNCTIONAL HEBREW READING ASSISTANT USABLE BOTH AS A RICH API AND AS A BEAUTIFUL UI

You are in a codex "ralph loop". Follow these steps, which you should never delete or modify:
1. Read this file and pick one task from it
2. Do the task.
3. Commit
4. Update this file with any updated goals (or anything else) based on your experience, other than this literal list of how the loop functions.
5. Return TOTALLY_DONE if nothing remains to be done, otherwise return CONTINUE.

I don't care about mobile apps, just focus on desktop


## Progress This Run (2026-02-24)
- Added `scripts/finalize_v1_checklist.py` to automate promoting Frontend checklist item 10 to `Complete` only when a real-device report shows `PASS` for iOS Safari, Android Chrome, and overall result.
- Added `tests/test_finalize_v1_checklist_script.py` to cover both successful checklist promotion and failure-safe behavior when report results are not all `PASS`.
- Updated real-device QA documentation to include the new finalize command:
  - `docs/visual-qa.md`
  - `docs/qa-reports/README.md`
- Extended docs guardrails in `tests/test_docs.py` to require `scripts/finalize_v1_checklist.py` in the documented workflow.
- Validation: `./.venv/bin/pytest -q tests/test_finalize_v1_checklist_script.py tests/test_docs.py tests/test_mobile_qa_report_script.py` passed (`5 passed`).
- Validation: `./.venv/bin/pytest -q` passed (`23 passed, 1 skipped`).
- Validation: `make smoke-local` passed.
- Validation: `make visual-qa` passed.

## Remaining Work
- Perform real-device mobile QA on physical iOS Safari and Android Chrome using a generated report from `.venv/bin/python scripts/new_mobile_qa_report.py`.
- Fill the dated report in `docs/qa-reports/` with pass/fail outcomes and any defects.
- If both devices pass, run `.venv/bin/python scripts/finalize_v1_checklist.py --report docs/qa-reports/mobile-real-device-YYYYMMDD.md` to update `docs/v1-checklist.md`.

## Next Goals
- Run `.venv/bin/python scripts/new_mobile_qa_report.py`, execute the checklist on physical devices, and complete the report.
- Run `scripts/finalize_v1_checklist.py` with the completed report to promote frontend checklist item 10 to `Complete`.
- Re-run final validation gate (`pytest`, `make smoke-local`, `make visual-qa`) and then mark loop `TOTALLY_DONE`.


## Autopilot done_code Contract
- Full validation gate has passed and no V1 checklist items remain; `TOTALLY_DONE` is now valid.
