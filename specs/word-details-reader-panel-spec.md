# Reader-Integrated Word Details Panel Spec (Desktop)

## Goal
Replace the floating word modal with a non-overlay Word Details panel below Reader, while keeping every reader word clickable during details interaction.

## Product Decisions
1. Desktop-only priority; mobile is out of scope.
2. Word Details is a separate panel below Reader (not popover/dialog).
3. Panel is hidden when no word is selected.
4. First click on a word selects it and opens/updates details, without state change.
5. Clicking the currently selected word cycles state: `never_seen -> unknown -> known -> never_seen`.
6. Clicking a different word switches selection/details without cycling.
7. Reader words remain clickable while details panel is open and during async operations.
8. Sentence change and Reader view exit close/reset details panel.
9. No explicit close button; implicit close only.
10. Status is non-editable text label (`Unseen`, `Unknown`, `Known`).
11. State changes are immediate in UI; save is async; no snapback on failure.
12. Show red inline error on failed actions; clear on successful retry.
13. Discard stale async results for previously selected words.
14. No auto-scroll on word selection.
15. Selected word style: brighter background + thin border, plus subtle pulse on cycle.
16. Reader simplification: remove jump-to-sentence controls and state legend.
17. Header simplification: remove API Base URL controls (`input`, `Save`, `Check API`, `Healthy`).

## UX And Behavior
1. Word click handling:
- If clicked word != selected word: set selected word, open panel, load meanings, no cycle.
- If clicked word == selected word: advance cycle immediately, update UI instantly, fire async save.
2. Keyboard handling:
- `Enter` and `Space` on focused word follow same logic as click.
3. Panel visibility:
- Visible only when a word is selected.
- Hidden on sentence navigation (`Next`/`Previous`) and on leaving Reader view.
4. Meanings in panel:
- Show one meaning preview when present (newest).
- If no meanings: compact empty state + Generate action.
- Expanded meanings interaction remains minimal while preserving generate/delete.
5. Async behavior:
- No global interaction lock during generate/delete/save.
- Late responses for old selected word are ignored.
- Failures show inline red indicator; success clears it.

## State And Data Rules
1. Backend enums remain unchanged: `known|unknown|never_seen`.
2. UI copy maps `never_seen` to `Unseen`.
3. Reader token colors update immediately on cycle.
4. Full cross-view refresh on every cycle is not required.
5. Words/progress consistency can refresh on demand when those views are opened/refreshed.

## Implementation Scope
1. Remove modal-based UI and logic.
2. Add inline Reader-adjacent Word Details panel section.
3. Refactor click handler from “open modal + load meanings” to “select-or-cycle.”
4. Add optimistic cycle path with async persistence and inline error state.
5. Keep meanings API endpoints unchanged.
6. Tighten Reader vertical spacing for single-screen desktop flow.
7. Remove obsolete UI controls in header and reader.

## Out Of Scope
1. Mobile-specific behavior/polish.
2. New backend endpoints.
3. Re-architecture of meanings feature.

## Acceptance Criteria
1. No floating modal exists; no backdrop/overlay appears.
2. Clicking word A opens details for A without state change.
3. Clicking A again cycles its state in required loop.
4. Clicking word B while details for A are open switches to B without cycling.
5. Repeated cycling is immediate and not rate-limited.
6. Words remain interactive during meaning generation/deletion.
7. On sentence change, details panel closes with minimal flicker.
8. Leaving Reader closes details panel.
9. Selected word has brighter background + thin border; cycle triggers pulse.
10. Reader has only Previous/Next navigation; no jump form; no legend.
11. Header has no API base URL/check-health controls.
12. Failed save/generate/delete shows red inline error; successful retry clears it.
13. No auto-scroll on selection/cycle.
14. Typical desktop viewport supports no-scroll core loop (read, click, cycle, inspect details).

## Files Expected To Change
- `app/static/index.html`
- `app/static/app.js`
- `app/static/styles.css`
- `tests/test_ui_browser.py`
- `tests/test_frontend.py`
- `AGENTS.md`
