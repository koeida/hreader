# Agent Instructions

## Product Constraints

- Never develop for mobile. Prioritize desktop-only behavior and UX across the product unless explicitly overridden by the user in that session.
- Reader word details must be implemented as an inline desktop panel below the reader sentence, never as a modal or overlay.

## Documentation (Start Here!)

**New to this codebase?** Read these in order:

1. **[`INDEX.md`](INDEX.md)** — Navigation hub for all documentation, organized by role
2. **[`docs/DEVELOPER.md`](docs/DEVELOPER.md)** — One-page architecture reference with file purposes, subsystems, patterns, and common tasks
3. **[`README.md`](README.md)** — Setup, run, test commands

For specific features, see the `specs/` folder.

## Server Recovery (Local)

- Default local target is `http://127.0.0.1:8001/`.
- To return backend to a known-good state:
  - `PORT=8001 bash scripts/start_server.sh`
  - `curl -sS http://127.0.0.1:8001/health`
  - `curl -sS "http://127.0.0.1:8001/v1/users/<USER_ID>/srs/session?timezone_offset_minutes=300"`
- If SRS routes return `404`, you are not running the current `app.main:app` from this repo on `8001`; restart with the command above.
