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
- Hebrew word-bubble ordering spec + implementation is in progress: `docs/hebrew-word-bubble-ordering-spec.md`.
  - Completed in this loop: explicit RTL contract on reader sentence (`lang="he" dir="rtl"`), bidi styling fix, and Playwright regression test for visual bubble order.
  - Remaining to close this item: manual desktop verification pass in Chromium/Firefox/WebKit plus screenshot/report evidence.
- Create a spec for making the UI look beautiful and 2026 and hip and responsive and modern-blue. No mobile focus. Desktop only. Reference that spec here and work it to completion. Ideally spawn a separate Codex instance to evaluate whether the UI is beautiful enough.

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

## Next Goals
1. Run manual desktop QA for Hebrew bubble ordering across Chromium/Firefox/WebKit and capture evidence in docs.
2. Author a dedicated desktop-only UI beauty spec (2026 modern-blue direction), then execute it incrementally with tests and visual QA updates.


## Autopilot done_code Contract
- All remaining work completed here; `TOTALLY_DONE` is now valid, otherwise 'CONTINUE'
