# Visual QA Notes

This project includes a lightweight visual QA pass for the family-ready UI.
The active desktop design direction is defined in `docs/ui-beauty-spec.md`.

## Generate Current Screenshots

```bash
make visual-qa
```

This command captures screenshots to:

- `docs/visual-qa/01-empty-shell.png`
- `docs/visual-qa/02-user-and-text-library.png`
- `docs/visual-qa/03-reader-word-details.png`
- `docs/visual-qa/04-reader-and-words.png`

Those are the canonical stored screenshots for this visual QA pass. Keep them under `docs/visual-qa/` so they stay discoverable in the repo.

Any non-canonical PNG files already under `docs/visual-qa/` are removed automatically on each run.

## Quick Review Checklist

- API controls are visible and health status updates from `Unknown` to `Healthy`.
- Creating a user updates the active user selector and users list.
- Creating a text updates the texts list with progress data.
- Opening a text renders Hebrew sentence content in the reader panel.
- Clicking an inline sentence word opens the compact Word Details panel with state controls.
- The Word Details panel stays inline below the reader sentence and leaves reader words clickable.
- Word state changes are reflected in the words panel when filtered by `known`.

## Automated Mobile Coverage

`tests/test_ui_browser.py::test_mobile_emulation_modal_tabs_and_wrapping` runs Playwright mobile emulation for:
- iPhone 12 viewport profile.
- Pixel 5 viewport profile.

`tests/test_ui_browser.py::test_mobile_webkit_emulation_modal_tabs_and_focus` adds a WebKit-based mobile pass for:
- iPhone 12 viewport profile on the WebKit engine (Safari-family behavior proxy).

Automated checks cover:
- Top-level tab buttons remain reachable and update `aria-selected`.
- Reader sentence layout at narrow widths does not horizontally overflow.
- Word Details panel opens inline within viewport width without scroll jumps.
- Word Details controls remain reachable while the originating inline word button stays in the reader flow.

## Desktop Browser QA Checklist

Run this pass manually on:
- Desktop Chromium (current stable major release).
- Desktop Firefox (current stable major release).
- Desktop WebKit (Safari-family desktop engine/current stable).

Before testing, generate a dated report template:

```bash
.venv/bin/python scripts/new_desktop_qa_report.py
```

Fill the generated file in `docs/qa-reports/desktop-browser-qa-YYYYMMDD.md` while testing.

Optional automated pass (fills the same report format automatically):

```bash
.venv/bin/python scripts/run_desktop_browser_qa.py --force
```

Checks:
- Click an inline sentence word and verify the compact Word Details panel remains inline; focus should remain logical and no off-screen jumps should occur.
- Reader sentence words and panels should remain readable without horizontal overflow at desktop widths.
- Top-level view tabs remain reachable and correctly update selected state.
- Word Details controls remain fully visible within viewport bounds.

After testing:
- If all browsers pass, run:

```bash
.venv/bin/python scripts/finalize_v1_checklist.py --report docs/qa-reports/desktop-browser-qa-YYYYMMDD.md
```

This validates Chromium/Firefox/WebKit PASS rows plus overall PASS, then marks Frontend checklist item 10 `Complete` with a report reference.
- If any browser fails, keep item 10 `Pending` and record defects in the report.
