# V1 Completion Checklist

Last updated: 2026-02-24

This checklist reconciles implemented behavior against:
- `backend-v1-spec.md`
- `frontend-v1-spec.md`

Legend:
- `Complete`: delivered and validated by automated checks.
- `Pending`: still required before full end-to-end sign-off.

## Backend V1

1. Project Skeleton + Health: `Complete`
Evidence: `/health`, `/v1` JSON 404 behavior, API boot in tests/smoke.

2. User Lifecycle (No Auth): `Complete`
Evidence: create/list/delete/restore API + e2e API tests.

3. Text CRUD (Per-User Private): `Complete`
Evidence: create/list/get/patch/delete text API + sentence splitting checks.

4. Tokenization + Normalization Engine: `Complete`
Evidence: tokenizer behavior validated in API flow assertions.

5. Sentence Load API + Never-Seen Population: `Complete`
Evidence: sentence load API + idempotent never-seen insertion checks.

6. Word State Management (Single-Word, Idempotent): `Complete`
Evidence: `PUT /words/{normalized_word}` tests and smoke mutation checks.

7. User Word List + Filters + Pagination: `Complete`
Evidence: state filters + page/limit checks in API tests and smoke.

8. Per-Text Vocabulary Overlay + Progress: `Complete`
Evidence: text progress endpoint and count/percent assertions.

9. Text List with Embedded Progress: `Complete`
Evidence: list payload includes progress fields; exercised in frontend + smoke.

10. Meanings API (Per-User, Multi-Entry): `Complete`
Evidence: get/generate/delete meaning flow in integration tests.

11. Cross-Cutting Hardening: `Complete`
Evidence: typed validation errors + deterministic timestamped payload checks; `pytest` + smoke green.

## Frontend V1

1. App Shell + API Connectivity: `Complete`
Evidence: app shell, health indicator, shared status regions.

2. User Selector + User Management: `Complete`
Evidence: create/select/delete/restore controls and browser journey coverage.

3. Text Library Screen (Per User): `Complete`
Evidence: create/open/rename/delete text and progress rendering.

4. Reader Screen (Sentence-by-Sentence): `Complete`
Evidence: prev/next/jump controls and boundary handling in browser + smoke.

5. Word State Editing (Single Token): `Complete`
Evidence: inline token modal state updates and persistence checks.

6. User Word List Screen (Core Feature): `Complete`
Evidence: filter tabs + pagination + per-word updates in browser journey.

7. Per-Text Vocabulary Overlay: `Complete`
Evidence: per-text progress panel/metrics shown and refreshed after updates.

8. Meanings Panel (On-Demand Only): `Complete`
Evidence: explicit fetch + generate + delete meaning actions in UI.

9. Cross-View Data Consistency: `Complete`
Evidence: request-version guards in frontend, mutation-driven refresh across panels.

10. UX Hardening + Basic QA Gates: `Complete`
Evidence complete: keyboard tab navigation, accessibility roles/labels, smoke + browser + visual QA artifacts, Playwright Chromium mobile emulation checks for iPhone 12 + Pixel 5 (tab reachability, modal close paths, narrow-width wrapping), and Playwright WebKit iPhone 12 emulation coverage for modal focus restoration + tab state changes; desktop browser QA matrix pass for Chromium + Firefox + WebKit. Real-device QA PASS report: `docs/qa-reports/desktop-browser-qa-20260224.md`.

## Current Release Gate

Project is functionally complete in automated checks.
All V1 checklist items are complete.
