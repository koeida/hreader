# Backend V1 Spec - Hebrew Reading Helper

Last updated: 2026-02-23

## Goal
Deliver a local, no-auth backend for a family Hebrew reading helper with per-user word states, per-user private texts, sentence-by-sentence reading, and meaning generation via Codex CLI.

## Feature 1: Project Skeleton + Health
Build the runnable API service shell and baseline conventions.

### Scope
- FastAPI service with `/v1` prefix.
- SQLite single shared DB file.
- Health endpoint.
- Standard JSON error envelope.

### Success Criteria
- Service starts with one command.
- `GET /health` returns `200` and `{ "status": "ok" }`.
- Any unknown `/v1/*` route returns JSON `404`.
- DB file is created automatically on first run.

## Feature 2: User Lifecycle (No Auth)
Support API-managed user profiles with soft delete + restore.

### Scope
- Create user (`display_name` only in request).
- List users (exclude deleted by default; opt-in include deleted).
- Soft delete user.
- Restore soft-deleted user.
- Timestamps on user records.

### Success Criteria
- Creating user returns generated `user_id` and timestamps.
- Deleted user is absent from default list.
- Deleted user appears when `include_deleted=true`.
- Restored user reappears in default list.
- Deleting non-existent user returns `404`.

## Feature 3: Text CRUD (Per-User Private)
Allow users to manage private texts and pre-split sentences.

### Scope
- Create text with `title` + `content` under a user.
- Split sentences server-side on period (`.`) only.
- Drop empty/whitespace fragments.
- Preserve original sentence formatting inside each sentence.
- List user texts.
- Read single text metadata.
- Rename text title.
- Hard delete text.

### Success Criteria
- Importing `"א. ב. ג."` stores exactly 3 non-empty sentences.
- Repeated spaces/newlines inside a sentence remain unchanged.
- User A cannot fetch User B text (`404` or equivalent hidden-not-found behavior).
- Renaming title updates only title, not sentence content.
- Deleting text removes it from list and sentence loads fail with `404`.

## Feature 4: Tokenization + Normalization Engine
Implement canonical token processing rules used across state and meaning features.

### Scope
- Strip nikkud for normalized lookup token.
- Split on Hebrew maqaf (`־`).
- Ignore punctuation-only tokens.
- Ignore numeric-only tokens.
- Keep and lowercase non-Hebrew alphabetic tokens.

### Success Criteria
- Same Hebrew word with/without nikkud normalizes to one token key.
- Maqaf-connected input yields separate tokens.
- Tokens like `"2026"` and punctuation do not enter tracked word set.
- Token `"Hello"` normalizes to `"hello"` and is trackable.
- Tokenization behavior is deterministic (same input => same outputs).

## Feature 5: Sentence Load API + Never-Seen Population
Serve sentence-by-sentence reading and introduce words to user bank on read.

### Scope
- Load sentence by `text_id + sentence_index` (0-based).
- Include navigation hints (`prev_sentence_index`, `next_sentence_index`).
- Out-of-range sentence index => `404`.
- On sentence load, add missing normalized tokens to user bank as `never_seen`.
- Re-loading sentence is idempotent.

### Success Criteria
- First load of sentence inserts only eligible new tokens as `never_seen`.
- Second load of same sentence does not duplicate word records.
- Response includes sentence text and per-token state.
- `sentence_index=-1` and too-large index return `404`.
- First sentence has `prev=null`; last sentence has `next=null`.

## Feature 6: Word State Management (Single-Word, Idempotent)
Allow user to set state per word.

### Scope
- Set one normalized word state (`known|unknown|never_seen`) for a user.
- Idempotent updates (same state re-set succeeds with no side effects).
- No bulk update endpoint in v1.

### Success Criteria
- Setting `unknown -> known` persists and is visible in subsequent reads/lists.
- Setting `known -> known` returns success and unchanged `updated_at` policy is consistent/documented.
- Invalid state values return `400`.
- Word state change for one user does not affect another user.

## Feature 7: User Word List + Filters + Pagination
Deliver the core per-user vocabulary list experience.

### Scope
- List user words with filters: `all`, `unknown`, `known`, `never_seen`.
- Pagination via `page` + `limit`.
- Default sorting: state priority (`unknown` before `known`) then alphabetical by normalized word.
- Include timestamps.

### Success Criteria
- Each filter returns only matching states.
- `page` and `limit` produce stable deterministic slices.
- Default sort places all `unknown` entries ahead of `known`.
- List reflects sentence-load-created `never_seen` entries.
- Invalid pagination params return `400`.

## Feature 8: Per-Text Vocabulary Overlay + Progress
Provide computed text-specific stats using canonical user word bank.

### Scope
- Endpoint for per-text word breakdown by state for selected user.
- Computed only from text tokens + user states (no separate persisted list).
- Return summary metrics: `known_count`, `unknown_count`, `never_seen_count`, `known_percent`.

### Success Criteria
- Counts sum to total unique eligible words in the text.
- `known_percent` is correctly derived and bounded `0..100`.
- State changes in user word bank immediately affect overlay results.
- Text with no eligible words returns zeroed metrics without error.

## Feature 9: Text List with Embedded Progress
Expose reading progress in main text listing.

### Scope
- User text list includes progress summary per text:
  - `known_count`
  - `unknown_count`
  - `never_seen_count`
  - `known_percent`

### Success Criteria
- List response includes all four fields for each text.
- Progress values match Feature 8 calculations for the same text/user.
- Values update after word state changes without re-importing text.

## Feature 10: Meanings API (Per-User, Multi-Entry)
Support lookup and expansion of generated meanings for a word.

### Scope
- Get existing meanings list for a normalized word (per user).
- Generate another meaning using Codex CLI with sentence context.
- Delete one meaning entry.
- Sync call behavior for generation.
- Cache by `(user_id, normalized_word)`.
- On CLI failure/timeout return error (no placeholder/fallback).

### Success Criteria
- Repeated `get meanings` returns same stored list order/shape.
- `generate another` appends a new meaning entry.
- Deleting a meaning removes only that entry.
- Meaning entries are not visible across users.
- Simulated CLI timeout returns documented error code and payload.
- Cache hit path is exercised and measurably avoids duplicate CLI call.

## Feature 11: Cross-Cutting Hardening
Lock baseline reliability for local usage.

### Scope
- Input validation and typed error responses.
- Consistent timestamp serialization.
- Basic integration test coverage across core flows.

### Success Criteria
- Invalid IDs, enums, and malformed payloads return predictable JSON errors.
- End-to-end test passes:
  1. create user
  2. upload text
  3. load sentence
  4. verify never_seen population
  5. update word state
  6. verify list + per-text progress
  7. generate/delete meaning
- Test suite is runnable with one command and green in clean environment.

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
11. Feature 11

## Out of Scope for V1
- Authentication/authorization.
- Bulk word-state edits.
- Text body editing after import.
- Export word list.
- Reset-all-word-states endpoint.
- State-change audit/history.
- Meaning text manual editing.

## Handoff Note
If backend v1 is feature-complete against this spec, move implementation planning and execution to:
- `/home/keegan/dev/hreader/frontend-v1-spec.md`
