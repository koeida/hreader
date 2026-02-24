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

## Quick Review Checklist

- API controls are visible and health status updates from `Unknown` to `Healthy`.
- Creating a user updates the active user selector and users list.
- Creating a text updates the texts list with progress data.
- Opening a text renders Hebrew sentence content in the reader panel.
- Clicking an inline sentence word opens the modal with state controls.
- Escape closes the word modal and returns focus to reader flow.
- Word state changes are reflected in the words panel when filtered by `known`.
