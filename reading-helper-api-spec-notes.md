# Hebrew Reading Helper API - Product Spec Notes

Last updated: 2026-02-23

## Confirmed Product Scope
- Local family app.
- Multi-user, no auth/passwords.
- App has a user selector; backend still stores separate user data.
- Texts are private per user (not shared by default).

## Core Domain
- Reading flow is sentence-by-sentence.
- Per-user word states:
  - `known`
  - `unknown`
  - `never_seen`
- Word identity is per unique normalized token (simple token model, no stemming/lemma logic).
- Nikkud is stripped for word-bank/state tasks, while display text keeps original nikkud.

## User Management (V1)
- Users are API-managed.
- Create user with `display_name`; server generates user ID.
- Soft delete users.
- Deleted users are hidden from normal list responses.
- List endpoint can optionally include deleted users.
- Soft-deleted users can be restored.

## Text Management (V1)
- Text upload/create supports `title` + `content` only.
- Texts are owned by the uploader user and visible only to that user.
- Sentence splitting is server-side at import.
- Sentence split rule for v1: split on period (`.`) only.
- Empty/whitespace-only sentence fragments are dropped.
- Original sentence text/formatting is preserved (no whitespace normalization).
- Users can:
  - list their texts
  - read a text
  - rename text title
  - hard-delete text
- Users cannot:
  - edit text body in place (delete + re-upload instead)
  - duplicate texts in v1

## Sentence Load Behavior (V1)
- Sentence addressing is 0-based (`sentence_index=0` is first sentence).
- Out-of-range sentence index returns not found behavior (`404`).
- Sentence response includes previous/next navigation hints.
- Loading a sentence is what introduces new words into the user word bank as `never_seen`.
- Importing text alone does not populate `never_seen`.
- Re-loading the same sentence re-checks idempotently (no read-history/analytics requirement in v1).

## Token Normalization Rules (V1)
- Ignore punctuation-only tokens for word-state tracking.
- Ignore numeric-only tokens for word-state tracking.
- Hebrew maqaf (`־`) splits tokens.
- Non-Hebrew alphabetic tokens are tracked and lowercased.

## Word List and Progress (V1)
- Canonical feature is per-user word list.
- Per-text vocab views are computed overlays against per-user data.
- Word list supports pagination (`page` + `limit`).
- Word list supports tabs/filtering across:
  - `all`
  - `unknown`
  - `known`
  - `never_seen`
- Default ordering prioritizes `unknown` before `known`, with alphabetical secondary ordering.
- No bulk state update actions in v1 (single-word updates only).
- State updates are idempotent.
- Text list responses include per-text progress summary:
  - `known_count`
  - `unknown_count`
  - `never_seen_count`
  - `known_percent`

## Meanings Feature (V1)
- Meanings are separate from sentence load; only returned via dedicated lookup endpoints.
- Meaning entries are private per user.
- A word can have multiple generated meanings (list model).
- Product behavior:
  - fetch existing meanings for a word
  - request generation of another meaning for that word (uses sentence context via Codex CLI)
  - delete a meaning entry
- No manual text editing of meanings in v1.
- Meaning generation is synchronous in v1.
- On Codex CLI failure/timeout, return an error (no fallback placeholder).
- Meaning cache key is per user + normalized word.

## API/Product Conventions Chosen
- API version prefix is `/v1`.
- Include standard timestamps (`created_at`, `updated_at`) on records.
- No state-change audit history in v1 (current state only).
- No export feature in v1.
- No “reset all word states” feature in v1.

## Implementation Defaults (Agent Chosen)
- Stack: Python + FastAPI + SQLite.
- SQLite as one shared app DB file (data separated by user IDs).

## Open Product Questions For Later
1. Should text list include lightweight search (by title) in v1?
2. Should word list support additional sorts (recently changed, frequency) beyond default?
3. Should users be able to hide/archive meanings without deleting them?
4. Should there be a “practice mode” endpoint that serves only unknown words in context?
5. Should per-text overlays expose additional metrics (coverage trend over time) in later versions?

## Next Session Starting Point
1. Convert this into concrete endpoint list and request/response schemas.
2. Lock exact behavior for per-user word list filters and per-text overlay response shape.
3. Define DB tables and indexes.
4. Define Codex CLI integration contract (timeouts, error payloads).
