# Visual QA Notes

This project includes a lightweight visual QA pass for the family-ready UI.

## Generate Current Screenshots

```bash
make visual-qa
```

This command captures screenshots to:

- `docs/visual-qa/01-empty-shell.png`
- `docs/visual-qa/02-user-and-text-library.png`
- `docs/visual-qa/03-reader-modal.png`
- `docs/visual-qa/04-reader-and-words.png`

Any non-canonical PNG files already under `docs/visual-qa/` are removed automatically on each run.

## Quick Review Checklist

- API controls are visible and health status updates from `Unknown` to `Healthy`.
- Creating a user updates the active user selector and users list.
- Creating a text updates the texts list with progress data.
- Opening a text renders Hebrew sentence content in the reader panel.
- Clicking an inline sentence word opens the modal with state controls.
- Escape closes the word modal and returns focus to reader flow.
- Word state changes are reflected in the words panel when filtered by `known`.

## Real-Device Mobile QA Checklist

Run this pass manually on:
- iOS Safari (current iOS major release).
- Android Chrome (current Android major release).

Checks:
- Tap an inline sentence word, then close via backdrop, Escape-equivalent/keyboard (if attached), and Close button; focus should remain logical and no off-screen jumps should occur.
- With narrow width (`<= 390px`), sentence words wrap naturally without overlap/cut-off in reader panel.
- Top-level view tabs remain reachable and correctly update selected state.
- Word modal controls remain fully visible without horizontal scrolling.
