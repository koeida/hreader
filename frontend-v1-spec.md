# Frontend V1 Spec - Hebrew Reading Helper

Last updated: 2026-02-23

## Goal
Deliver a first-pass UI that fully exercises the backend v1 API: user selection, private text management, sentence-by-sentence reading, per-user vocabulary management, per-text progress overlays, and meaning lookup/generation/deletion.

## Product Constraints
- Local family app; no auth screens.
- User must be selected before user-scoped actions.
- UI should be usable on desktop and mobile.
- First pass prioritizes function, clarity, and stable API integration over polish.

## Feature 1: App Shell + API Connectivity
Create a working shell that can reach API and show operational status.

### Scope
- Global layout with top-level navigation.
- API base URL configuration.
- Startup health check indicator.
- Reusable loading/error/empty states.

### Success Criteria
- App boots and renders with no selected user.
- API reachable state is visible (healthy/unhealthy).
- Any network/API error shows actionable message and retry action.
- Shared loading/empty/error components are used by all major views.

## Feature 2: User Selector + User Management
Implement no-auth user entry point.

### Scope
- User selector control visible globally.
- User list load from API.
- Create user dialog/form (`display_name`).
- Soft delete user action.
- Restore user flow (view deleted users + restore).

### Success Criteria
- User can be created and immediately selected.
- Soft-deleted users disappear from default list.
- Deleted users can be viewed and restored.
- User-scoped screens block actions until a user is selected.

## Feature 3: Text Library Screen (Per User)
Manage a selected user’s private texts.

### Scope
- Text list page scoped to selected user.
- Upload/create text form (`title`, `content`).
- Text row actions: open reader, rename title, delete text.
- Display embedded progress metrics per text:
  - `known_count`
  - `unknown_count`
  - `never_seen_count`
  - `known_percent`

### Success Criteria
- New text appears in list after successful upload.
- Rename updates title in list without page reload artifacts.
- Delete removes text from list and future opens fail gracefully.
- Progress stats render correctly for each text and refresh after state changes.

## Feature 4: Reader Screen (Sentence-by-Sentence)
Support core reading flow and word-state visibility.

### Scope
- Reader view for one text at a time.
- Sentence navigation controls (prev/next and direct index jump).
- Sentence content display preserving original text formatting.
- Token-level state rendering per sentence (`known`, `unknown`, `never_seen`).
- Handles first/last sentence boundaries.

### Success Criteria
- Opening a text lands on sentence index `0`.
- Prev/next controls follow API navigation hints correctly.
- Out-of-range navigation attempts are prevented or gracefully handled.
- Sentence load triggers backend never-seen insertion and reflects returned states.

## Feature 5: Word State Editing (Single Token)
Enable direct per-word learning state updates from reading context.

### Scope
- Tap/click token in reader to open state action UI.
- Set token state to `known`, `unknown`, or `never_seen`.
- Optimistic or pessimistic update strategy with rollback/error handling.
- Reflect updated state in current sentence and dependent views.

### Success Criteria
- State update action persists and is visible on reloading same sentence.
- Re-applying same state shows successful no-op UX (no duplicate side effects).
- API failure shows error and keeps UI consistent.
- State updates affect text progress values after refresh/requery.

## Feature 6: User Word List Screen (Core Feature)
Deliver vocabulary management UI for selected user.

### Scope
- Dedicated word list page.
- Tabs/filters: `All`, `Unknown`, `Known`, `Never Seen`.
- Pagination controls (`page`, `limit`).
- Default sort presentation consistent with backend ordering.
- Row action to change a word’s state (single word only).

### Success Criteria
- Each tab returns and displays only expected states.
- Pagination changes dataset slice predictably.
- Unknown words appear before known words in default view.
- State edits from this screen persist and are reflected in reader/text progress.

## Feature 7: Per-Text Vocabulary Overlay
Expose text-specific vocabulary status computed from canonical user word bank.

### Scope
- Text detail panel/page showing words found in that text with their states.
- Summary metrics:
  - `known_count`
  - `unknown_count`
  - `never_seen_count`
  - `known_percent`
- Optional quick links from words back to reader sentence context (if available).

### Success Criteria
- Overlay counts match backend response and sum correctly.
- Changing word state updates overlay after refresh/requery.
- Text with zero eligible words displays valid empty state and zeroed metrics.

## Feature 8: Meanings Panel (On-Demand Only)
Support explicit meaning workflows separate from automatic reading display.

### Scope
- Meaning lookup is triggered only by explicit user action.
- For selected word, show existing meanings list.
- Action to generate another meaning via API call (sentence context supplied).
- Action to delete a meaning entry.
- Loading/error states for meaning generation and fetch.

### Success Criteria
- No meanings are auto-fetched during passive reading.
- Existing meanings render in stable list order.
- “Generate another” appends a new entry after success.
- Delete removes only targeted meaning and updates UI without full app reload.
- CLI/API failure displays clear recoverable error state.

## Feature 9: Cross-View Data Consistency
Ensure all screens remain consistent after mutations.

### Scope
- Cache invalidation/requery strategy across reader, text library, word list, and meanings.
- Consistent timestamp formatting and state labels.
- Prevent stale user context leaks when switching active user.

### Success Criteria
- After word state change, dependent screens show consistent values.
- Switching user resets user-scoped data and prevents cross-user bleed.
- After text delete, orphan links/routes recover to safe screen.
- No duplicate in-flight mutation effects from rapid repeat clicks.

## Feature 10: UX Hardening + Basic QA Gates
Add minimum quality gates for v1 usability.

### Scope
- Keyboard and touch-friendly controls for main flows.
- Basic accessibility labels for forms/buttons/tabs.
- Smoke test checklist for core journeys.

### Success Criteria
- Core flows work on common mobile viewport and desktop viewport.
- Primary actions are reachable via keyboard navigation.
- Smoke checklist passes:
  1. create/select user
  2. upload text
  3. read sentences
  4. set word state
  5. verify word list filters
  6. verify per-text overlay
  7. lookup/generate/delete meaning

## Recommended Build Order
1. Feature 1
2. Feature 2
3. Feature 3
4. Feature 4
5. Feature 5
6. Feature 6
7. Feature 7
8. Feature 8
9. Feature 9
10. Feature 10

## Out of Scope for Frontend V1
- Authentication UI.
- Bulk word-state edit UX.
- Advanced reader personalization.
- Offline-first sync behavior.
- Word list export UX.
- Analytics dashboards/history timelines.
