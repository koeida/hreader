# Project Status

OVERALL GOAL: A BEAUTIFUL AND FULLY-FUNCTIONAL HEBREW READING ASSISTANT USABLE BOTH AS A RICH API AND AS A BEAUTIFUL UI

You are in a codex "ralph loop". Follow these steps, which you should never delete or modify:
1. Read this file and pick one task from it
2. Do the task.
3. Commit
4. Update this file with any updated goals (or anything else) based on your experience, other than this literal list of how the loop functions.
5. Return TOTALLY_DONE if nothing remains to be done, otherwise return CONTINUE.

## Overall directives:

- I don't care about mobile apps, just focus on desktop
- No referencing v1 goals. Focus on work referenced in this status file.

## Remaining Work
- None. Status-file scoped desktop UI and RTL ordering work is complete.

## Progress Update (2026-02-24)
- Added Hebrew ordering spec: `docs/hebrew-word-bubble-ordering-spec.md`.
- Implemented reader RTL flow hardening in:
  - `app/static/index.html`
  - `app/static/styles.css`
- Added automated regression coverage in:
  - `tests/test_ui_browser.py::test_reader_sentence_enforces_rtl_word_bubble_order`
  - `tests/test_frontend.py` static reader `dir/lang` assertion
- Validation run:
  - `.venv/bin/pytest tests/test_frontend.py tests/test_ui_browser.py::test_reader_sentence_enforces_rtl_word_bubble_order` (PASS)
- Added desktop-only beauty spec:
  - `docs/ui-beauty-spec.md`
- Implemented Phase 1 modern-blue desktop UI restyle:
  - `app/static/index.html`
  - `app/static/styles.css`
- Updated visual QA guidance to reference beauty spec:
  - `docs/visual-qa.md`
- Added doc regression coverage:
  - `tests/test_docs.py::test_ui_beauty_spec_is_present_and_desktop_first`
- Refreshed visual QA screenshots:
  - `docs/visual-qa/01-empty-shell.png`
  - `docs/visual-qa/02-user-and-text-library.png`
  - `docs/visual-qa/03-reader-modal.png`
  - `docs/visual-qa/04-reader-and-words.png`
- Generated fresh desktop browser QA report:
  - `docs/qa-reports/desktop-browser-qa-20260224.md`
- Added screenshot artifacts per browser in desktop QA automation:
  - `scripts/run_desktop_browser_qa.py`
  - `docs/qa-reports/screenshots/desktop-chromium-20260224-reader.png`
  - `docs/qa-reports/screenshots/desktop-firefox-20260224-reader.png`
  - `docs/qa-reports/screenshots/desktop-webkit-20260224-reader.png`
- Added explicit manual reviewer notes for RTL bubble ordering evidence across Chromium/Firefox/WebKit:
  - `docs/qa-reports/desktop-browser-qa-20260224.md`
- Completed independent design review and documented Phase 2 decisions:
  - `docs/qa-reports/ui-design-review-20260224.md`
- Applied Phase 2 desktop polish (typography/spacing/contrast tuning):
  - `app/static/index.html`
  - `app/static/styles.css`
- Updated beauty spec completion criteria for Phase 2 + manual evidence:
  - `docs/ui-beauty-spec.md`
- Added regression coverage for QA/manual evidence and design review docs:
  - `tests/test_desktop_qa_script.py`
  - `tests/test_docs.py`
  - `tests/test_frontend.py`
- Validation run:
  - `.venv/bin/pytest -q tests/test_frontend.py tests/test_docs.py tests/test_desktop_qa_script.py tests/test_ui_browser.py::test_reader_sentence_enforces_rtl_word_bubble_order` (PASS)
  - `make visual-qa` (PASS)
  - `.venv/bin/python scripts/run_desktop_browser_qa.py --date 2026-02-24 --force` (PASS)

## Next Goals
1. Optional: gather real-user desktop feedback and run a Phase 3 micro-tuning pass if needed.


## Autopilot done_code Contract
- All remaining work completed here; `TOTALLY_DONE` is now valid, otherwise 'CONTINUE'
