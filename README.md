# Hebrew Reading Helper Backend (V1)

FastAPI + SQLite backend implementing `backend-v1-spec.md`.

## Run

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload
```

Or with `make`:

```bash
make venv
make install
make run
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

## Test

```bash
.venv/bin/pytest -q
```

Or:

```bash
make test
```

## Sample Hebrew Story (Easy Modern Hebrew, Full Nikkud)

Saved at:
- `data/sample_story_he_nikkud.txt`

You can seed it directly:

```bash
.venv/bin/python scripts/seed_sample_story.py
```

Or:

```bash
make seed
```

## Smoke Check

With the API running:

```bash
make smoke
```

## API Highlights

- `POST /v1/users`
- `GET /v1/users?include_deleted=true|false`
- `DELETE /v1/users/{user_id}` (soft delete)
- `POST /v1/users/{user_id}/restore`
- `POST /v1/users/{user_id}/texts`
- `GET /v1/users/{user_id}/texts`
- `GET /v1/users/{user_id}/texts/{text_id}`
- `PATCH /v1/users/{user_id}/texts/{text_id}`
- `DELETE /v1/users/{user_id}/texts/{text_id}`
- `GET /v1/users/{user_id}/texts/{text_id}/sentences/{sentence_index}`
- `PUT /v1/users/{user_id}/words/{normalized_word}`
- `GET /v1/users/{user_id}/words?state=all|unknown|known|never_seen&page=1&limit=50`
- `GET /v1/users/{user_id}/texts/{text_id}/progress`
- `GET /v1/users/{user_id}/words/{normalized_word}/meanings`
- `POST /v1/users/{user_id}/words/{normalized_word}/meanings/generate`
- `DELETE /v1/users/{user_id}/words/{normalized_word}/meanings/{meaning_id}`

## Notes

- Meanings generation is synchronous and calls `codex exec` by default.
- On generator failure/timeout, API returns JSON error (`502`/`504`).
- Unknown `/v1/*` routes return JSON `404` envelope.
