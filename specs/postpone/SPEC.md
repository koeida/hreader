# Postpone Feature Spec

## Overview
Allow users to defer their SRS review queue by shifting all due cards forward N days.
Inspired by SuperMemo's postpone feature — intended as a relief valve when the backlog
is overwhelming, not as a regular habit.

## Trigger
A small, unobtrusive **Postpone** button permanently visible in the SRS view.

## Dialog
On click, opens a dialog containing:
- **Slider** — 1 to 30 days
- **Live readout** — "X cards due today → Y cards due today" (updates as slider moves)
- **Confirm** and **Cancel** buttons

## Which Cards Are Affected
All cards with `due_at <= today` (overdue + due today).

## How Cards Are Moved
Each card shifted by N days relative to its *current* due date (not a fixed target date).
A card due 3 days ago postponed by 5 days becomes due 2 days from now.

## Live Count Math (client-side)
Fetch all due card dates once when dialog opens.
Cards still due after postponing by N = cards where `due_at <= today - N days`.
No additional API calls needed as slider moves.

## Backend
New endpoint: `POST /v1/users/{user_id}/srs/postpone`
Body: `{ "days": N }`

```sql
UPDATE srs_cards
SET due_at = DATE(due_at, '+N days')
WHERE user_id = ? AND due_at <= date('now')
```

## After Confirm
Reload the SRS session. Queue reflects the reduced count.

## Slider Range
1–30 days. User can postpone multiple times if needed beyond 30.
