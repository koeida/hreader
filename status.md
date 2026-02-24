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
  - Completed in this loop: explicit RTL contract on reader sentence (`lang="he" dir="rtl"`), bidi styling fix, Playwright regression test for visual bubble order, and a fresh desktop-browser matrix report at `docs/qa-reports/desktop-browser-qa-20260224.md` (Chromium/Firefox/WebKit all PASS).
  - Remaining to close this item: explicit manual (human) desktop verification notes with screenshots called out as manual evidence.
- Create a spec for making the UI look beautiful and 2026 and hip and responsive and modern-blue. No mobile focus. Desktop only. Reference that spec here and work it to completion. Ideally spawn a separate Codex instance to evaluate whether the UI is beautiful enough.
  - Completed in this loop: authored `docs/ui-beauty-spec.md` and shipped Phase 1 desktop modern-blue UI implementation.
  - Remaining to close this item: independent visual review pass against the new spec and a Phase 2 refinement sweep.

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
- Validation run:
  - `.venv/bin/pytest -q tests/test_frontend.py tests/test_docs.py tests/test_visual_qa.py tests/test_ui_browser.py::test_reader_sentence_enforces_rtl_word_bubble_order` (PASS)
  - `make visual-qa` (PASS)
  - `.venv/bin/python scripts/run_desktop_browser_qa.py --date 2026-02-24 --force` (PASS)

## Next Goals
1. Run and document explicit manual desktop QA notes/screenshots for Hebrew bubble ordering across Chromium/Firefox/WebKit (human-verified evidence).
2. Run an independent design review against `docs/ui-beauty-spec.md` and apply Phase 2 polish updates (spacing, typography tuning, contrast passes).


## Autopilot done_code Contract
- All remaining work completed here; `TOTALLY_DONE` is now valid, otherwise 'CONTINUE'
