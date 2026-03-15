from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
import random
from typing import Any
from uuid import UUID, uuid4

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.backup import BACKUP_DIR, prune_old_backups, run_backup
from app.db import DEFAULT_DB_PATH, get_connection, init_db
from app.meanings import MeaningGenerationError, MeaningGenerator, normalize_english_meaning_text
from app.models import (
    HealthResponse,
    MeaningCreateRequest,
    MeaningGenerateRequest,
    MeaningsListResponse,
    MeaningResponse,
    MeaningUpdateRequest,
    ProgressBucket,
    ProgressHistoryResponse,
    SentenceResponse,
    SentenceTokenResponse,
    SrsCardResponse,
    SrsReviewRequest,
    SrsReviewResponse,
    SrsSessionAddNewRequest,
    SrsSessionAddNewResponse,
    SrsSessionResponse,
    TextCreateRequest,
    TextListResponse,
    TextPositionResponse,
    TextPositionUpdateRequest,
    TextProgress,
    TextResponse,
    TextUpdateRequest,
    UserCreateRequest,
    UserResponse,
    UsersListResponse,
    WordDetailsResponse,
    WordDetailsUpdateRequest,
    WordListFilter,
    WordStateResponse,
    WordStateUpdateRequest,
    WordsListResponse,
    WordsReadBucket,
    WordsReadHistoryResponse,
)
from app.tokenizer import NIKKUD_RE, normalize_token, tokenize_eligible

SRS_DAILY_NEW_CAP = 20
SRS_INTERVAL_DAYS = [1, 2, 4, 7, 12, 21, 35, 56]

# Percentage of words that are unique (not just variants with prefixes)
# Calculated from Keegan's wordbank: 714 unique base words / 881 total words = 81.04%
# Strips common Hebrew prefixes: ו ב ל ש כ ה
# Used to estimate "unique known words" on progress page
UNIQUE_WORD_ESTIMATE_PERCENT = 0.8104


def to_iso_utc(value: datetime) -> str:
    return value.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def utc_now_iso() -> str:
    return to_iso_utc(datetime.now(UTC))


def split_sentences(content: str) -> list[str]:
    items: list[str] = []
    for fragment in content.split("."):
        if fragment.strip():
            items.append(fragment.strip())
    return items


def ensure_uuid(value: str, field_name: str) -> str:
    try:
        UUID(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"invalid_{field_name}") from exc
    return value


def parse_progress(conn: Any, user_id: str, text_id: str) -> TextProgress:
    rows = conn.execute(
        "SELECT sentence_text FROM text_sentences WHERE text_id = ? ORDER BY sentence_index ASC",
        (text_id,),
    ).fetchall()

    unique_words: set[str] = set()
    for row in rows:
        for token in tokenize_eligible(row["sentence_text"]):
            unique_words.add(token.normalized_word)

    if not unique_words:
        return TextProgress(
            known_count=0,
            unknown_count=0,
            never_seen_count=0,
            known_percent=0.0,
            stage4_percent=0.0,
            total_words=0,
        )

    placeholders = ",".join("?" for _ in unique_words)
    state_rows = conn.execute(
        f"""
        SELECT normalized_word, state
        FROM user_words
        WHERE user_id = ? AND normalized_word IN ({placeholders})
        """,
        (user_id, *sorted(unique_words)),
    ).fetchall()
    state_map = {row["normalized_word"]: row["state"] for row in state_rows}

    # Get SRS stage_index >= 4 for words not already known
    stage4_rows = conn.execute(
        f"""
        SELECT normalized_word
        FROM srs_cards
        WHERE user_id = ? AND normalized_word IN ({placeholders}) AND stage_index >= 4
        """,
        (user_id, *sorted(unique_words)),
    ).fetchall()
    stage4_set = {row["normalized_word"] for row in stage4_rows}

    known = 0
    unknown = 0
    never_seen = 0
    stage4 = 0
    for word in unique_words:
        state = state_map.get(word, "never_seen")
        if state == "known":
            known += 1
        elif state == "unknown":
            unknown += 1
        else:
            never_seen += 1

        # Count stage 4+ separately (doesn't include known words)
        if word in stage4_set and state != "known":
            stage4 += 1

    total = len(unique_words)
    known_percent = round((known / total) * 100.0, 2) if total > 0 else 0.0
    stage4_percent = round((stage4 / total) * 100.0, 2) if total > 0 else 0.0
    return TextProgress(
        known_count=known,
        unknown_count=unknown,
        never_seen_count=never_seen,
        known_percent=known_percent,
        stage4_percent=stage4_percent,
        total_words=total,
    )


def _bucket_progress_history(rows: list[Any], range_key: str) -> list[ProgressBucket]:
    """Generate progress history buckets from user_words rows."""
    events: list[tuple[date, str]] = []

    for row in rows:
        created_at_str = row["created_at"]
        created_date = datetime.fromisoformat(created_at_str.replace("Z", "+00:00")).date()
        events.append((created_date, "encountered"))

        if row["state"] == "known" and row["updated_at"]:
            updated_at_str = row["updated_at"]
            updated_date = datetime.fromisoformat(updated_at_str.replace("Z", "+00:00")).date()
            events.append((updated_date, "known"))

    if not events:
        return []

    today = datetime.now(UTC).date()

    if range_key == "month":
        bucket_keys: list[str] = []
        for i in range(29, -1, -1):
            d = today - timedelta(days=i)
            bucket_keys.append(d.isoformat())
    elif range_key == "year":
        bucket_keys = []
        for i in range(51, -1, -1):
            d = today - timedelta(weeks=i)
            d_monday = d - timedelta(days=d.weekday())
            week_key = f"{d_monday.isocalendar().year}-W{d_monday.isocalendar().week:02d}"
            if not bucket_keys or bucket_keys[-1] != week_key:
                bucket_keys.append(week_key)
    else:
        min_event_date = min(e[0] for e in events)
        bucket_keys = []
        d = min_event_date.replace(day=1)
        while d <= today and len(bucket_keys) < 120:
            bucket_keys.append(d.isoformat()[:7])
            if d.month == 12:
                d = d.replace(year=d.year + 1, month=1)
            else:
                d = d.replace(month=d.month + 1)

    bucket_counts: dict[str, dict[str, int]] = {}
    for key in bucket_keys:
        bucket_counts[key] = {"encountered": 0, "known": 0}

    for event_date, event_type in events:
        if range_key == "month":
            key = event_date.isoformat()
        elif range_key == "year":
            d_monday = event_date - timedelta(days=event_date.weekday())
            key = f"{d_monday.isocalendar().year}-W{d_monday.isocalendar().week:02d}"
        else:
            key = event_date.isoformat()[:7]

        if key in bucket_counts:
            if event_type == "encountered":
                bucket_counts[key]["encountered"] += 1
            elif event_type == "known":
                bucket_counts[key]["known"] += 1

    cumulative_encountered = 0
    cumulative_known = 0
    result: list[ProgressBucket] = []

    for key in bucket_keys:
        cumulative_encountered += bucket_counts[key]["encountered"]
        cumulative_known += bucket_counts[key]["known"]
        result.append(
            ProgressBucket(
                date=key,
                cumulative_encountered=cumulative_encountered,
                cumulative_known=cumulative_known,
            )
        )

    return result


def _bucket_words_read(rows: list[Any], range_key: str) -> list[WordsReadBucket]:
    """Generate words-read history buckets from sentences_read rows."""
    if not rows:
        return []

    events: list[tuple[date, int]] = []
    for row in rows:
        read_date = datetime.fromisoformat(row["read_at"].replace("Z", "+00:00")).date()
        events.append((read_date, row["word_count"]))

    today = datetime.now(UTC).date()

    if range_key == "month":
        bucket_keys: list[str] = []
        for i in range(29, -1, -1):
            d = today - timedelta(days=i)
            bucket_keys.append(d.isoformat())
    elif range_key == "year":
        bucket_keys = []
        for i in range(51, -1, -1):
            d = today - timedelta(weeks=i)
            d_monday = d - timedelta(days=d.weekday())
            week_key = f"{d_monday.isocalendar().year}-W{d_monday.isocalendar().week:02d}"
            if not bucket_keys or bucket_keys[-1] != week_key:
                bucket_keys.append(week_key)
    else:
        min_date = min(e[0] for e in events)
        bucket_keys = []
        d = min_date.replace(day=1)
        while d <= today and len(bucket_keys) < 120:
            bucket_keys.append(d.isoformat()[:7])
            if d.month == 12:
                d = d.replace(year=d.year + 1, month=1)
            else:
                d = d.replace(month=d.month + 1)

    bucket_words: dict[str, int] = {key: 0 for key in bucket_keys}

    for event_date, word_count in events:
        if range_key == "month":
            key = event_date.isoformat()
        elif range_key == "year":
            d_monday = event_date - timedelta(days=event_date.weekday())
            key = f"{d_monday.isocalendar().year}-W{d_monday.isocalendar().week:02d}"
        else:
            key = event_date.isoformat()[:7]
        if key in bucket_words:
            bucket_words[key] += word_count

    cumulative = 0
    result: list[WordsReadBucket] = []
    for key in bucket_keys:
        cumulative += bucket_words[key]
        result.append(WordsReadBucket(date=key, cumulative_words=cumulative))

    return result


def ensure_active_user(conn: Any, user_id: str) -> None:
    row = conn.execute(
        "SELECT user_id FROM users WHERE user_id = ? AND deleted_at IS NULL",
        (user_id,),
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="user_not_found")


def ensure_user_text(conn: Any, user_id: str, text_id: str) -> Any:
    row = conn.execute(
        """
        SELECT text_id, user_id, title, content, created_at, updated_at
        FROM texts
        WHERE text_id = ? AND user_id = ?
        """,
        (text_id, user_id),
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="text_not_found")
    return row


def row_to_user(row: Any) -> UserResponse:
    return UserResponse(
        user_id=row["user_id"],
        display_name=row["display_name"],
        deleted_at=row["deleted_at"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def row_to_word(row: Any) -> WordStateResponse:
    return WordStateResponse(
        user_id=row["user_id"],
        normalized_word=row["normalized_word"],
        state=row["state"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def row_to_meaning(row: Any) -> MeaningResponse:
    return MeaningResponse(
        meaning_id=row["meaning_id"],
        user_id=row["user_id"],
        normalized_word=row["normalized_word"],
        meaning_text=row["meaning_text"],
        source_sentence=row["source_sentence"],
        created_at=row["created_at"],
    )


def row_to_word_details(row: Any, user_id: str, normalized_word: str) -> WordDetailsResponse:
    if not row:
        return WordDetailsResponse(
            user_id=user_id,
            normalized_word=normalized_word,
            mnemonic=None,
            created_at=None,
            updated_at=None,
        )
    return WordDetailsResponse(
        user_id=row["user_id"],
        normalized_word=row["normalized_word"],
        mnemonic=row["mnemonic"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def row_to_text_position(row: Any, user_id: str, text_id: str) -> TextPositionResponse:
    if not row:
        return TextPositionResponse(
            user_id=user_id,
            text_id=text_id,
            sentence_index=0,
            updated_at=None,
        )
    return TextPositionResponse(
        user_id=row["user_id"],
        text_id=row["text_id"],
        sentence_index=row["sentence_index"],
        updated_at=row["updated_at"],
    )


def normalize_meaning_text(value: str) -> str:
    normalized = " ".join(value.strip().split())
    if not normalized:
        raise HTTPException(status_code=400, detail="invalid_meaning_text")
    return normalized


def srs_window_bounds(now_utc: datetime, timezone_offset_minutes: int) -> tuple[datetime, datetime]:
    offset = timedelta(minutes=timezone_offset_minutes)
    local_now = now_utc - offset
    start_local = datetime.combine(local_now.date(), time(hour=3, minute=30), tzinfo=UTC)
    if local_now.time() < time(hour=3, minute=30):
        start_local -= timedelta(days=1)
    window_start_utc = start_local + offset
    window_end_utc = window_start_utc + timedelta(days=1)
    return window_start_utc, window_end_utc


def row_to_srs_card(row: Any) -> SrsCardResponse:
    return row_to_srs_card_with_display(row, row["normalized_word"])


def row_to_srs_card_with_display(row: Any, display_word: str) -> SrsCardResponse:
    return SrsCardResponse(
        user_id=row["user_id"],
        normalized_word=row["normalized_word"],
        display_word=display_word,
        is_new=bool(row["is_new"]),
        is_introduced=bool(row["is_introduced"]),
        stage_index=row["stage_index"],
        due_at=row["due_at"],
        introduced_at=row["introduced_at"],
        last_reviewed_at=row["last_reviewed_at"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def resolve_srs_display_words(conn: Any, user_id: str, normalized_words: list[str]) -> dict[str, str]:
    targets = {word for word in normalized_words if word}
    if not targets:
        return {}

    display_map: dict[str, str] = {}
    has_nikkud_map: dict[str, bool] = {}
    rows = conn.execute(
        """
        SELECT ts.sentence_text
        FROM text_sentences ts
        JOIN texts t ON t.text_id = ts.text_id
        WHERE t.user_id = ?
        ORDER BY t.created_at ASC, ts.sentence_index ASC
        """,
        (user_id,),
    ).fetchall()

    for row in rows:
        if len(display_map) == len(targets) and all(has_nikkud_map.get(w, False) for w in targets):
            break
        sentence_text = row["sentence_text"]
        for token in tokenize_eligible(sentence_text):
            normalized = token.normalized_word
            if normalized not in targets:
                continue
            token_text = token.token
            token_has_nikkud = bool(NIKKUD_RE.search(token_text))
            if normalized not in display_map:
                display_map[normalized] = token_text
                has_nikkud_map[normalized] = token_has_nikkud
                continue
            if token_has_nikkud and not has_nikkud_map.get(normalized, False):
                display_map[normalized] = token_text
                has_nikkud_map[normalized] = True

    return {word: display_map.get(word, word) for word in normalized_words}


def get_daily_new_count(conn: Any, user_id: str, window_start_at: str) -> int:
    row = conn.execute(
        """
        SELECT new_count
        FROM srs_daily_new_counts
        WHERE user_id = ? AND window_start_at = ?
        """,
        (user_id, window_start_at),
    ).fetchone()
    return int(row["new_count"]) if row else 0


def increment_daily_new_count(conn: Any, user_id: str, window_start_at: str, count: int) -> None:
    conn.execute(
        """
        INSERT INTO srs_daily_new_counts (user_id, window_start_at, new_count)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id, window_start_at)
        DO UPDATE SET new_count = new_count + excluded.new_count
        """,
        (user_id, window_start_at, count),
    )


def ensure_srs_cards_for_unknown_words(conn: Any, user_id: str) -> None:
    now = utc_now_iso()
    conn.execute(
        """
        INSERT INTO srs_cards (
            user_id, normalized_word, is_new, is_introduced, stage_index, due_at,
            introduced_at, last_reviewed_at, created_at, updated_at
        )
        SELECT uw.user_id, uw.normalized_word, 1, 0, 0, ?, NULL, NULL, ?, ?
        FROM user_words uw
        LEFT JOIN srs_cards sc
          ON sc.user_id = uw.user_id AND sc.normalized_word = uw.normalized_word
        WHERE uw.user_id = ? AND uw.state = 'unknown' AND sc.normalized_word IS NULL
        """,
        (now, now, now, user_id),
    )
    conn.commit()


def _sync_srs_card(conn: Any, user_id: str, normalized: str, state: str, now: str) -> None:
    if state == "unknown":
        conn.execute(
            """
            INSERT INTO srs_cards (
                user_id, normalized_word, is_new, is_introduced, stage_index, due_at,
                introduced_at, last_reviewed_at, created_at, updated_at
            )
            VALUES (?, ?, 1, 0, 0, ?, NULL, NULL, ?, ?)
            ON CONFLICT(user_id, normalized_word)
            DO UPDATE SET
                is_new = 1,
                is_introduced = 0,
                stage_index = 0,
                due_at = excluded.due_at,
                introduced_at = NULL,
                updated_at = excluded.updated_at
            """,
            (user_id, normalized, now, now, now),
        )
    else:
        conn.execute(
            "DELETE FROM srs_cards WHERE user_id = ? AND normalized_word = ?",
            (user_id, normalized),
        )


def create_app(db_path: str = str(DEFAULT_DB_PATH), meaning_generator: Any | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(_: FastAPI) -> Any:
        conn = get_connection(db_path)
        try:
            init_db(conn)
        finally:
            conn.close()
        yield

    app = FastAPI(title="Hebrew Reading Helper API", version="1.0.0", lifespan=lifespan)
    app.state.db_path = db_path
    app.state.meaning_generator = meaning_generator or MeaningGenerator()
    app.state.static_dir = Path(__file__).resolve().parent / "static"
    app.state.backup_last_date = None
    app.state.backup_failed = False

    if app.state.static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(app.state.static_dir)), name="static")

        @app.get("/", include_in_schema=False)
        def serve_ui() -> FileResponse:
            return FileResponse(app.state.static_dir / "index.html")

    def get_conn() -> Any:
        conn = get_connection(app.state.db_path)
        try:
            yield conn
        finally:
            conn.close()

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = "not_found" if exc.status_code == 404 else "http_error"
        message = str(exc.detail) if exc.detail else code
        if request.url.path.startswith("/v1"):
            return JSONResponse(status_code=exc.status_code, content={"error": {"code": code, "message": message}})
        return JSONResponse(status_code=exc.status_code, content={"error": {"code": code, "message": message}})

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={"error": {"code": "validation_error", "message": str(exc.errors())}},
        )

    @app.middleware("http")
    async def backup_middleware(request: Request, call_next: Any) -> Any:
        """Run backup once per day on the first request after midnight."""
        today = date.today()
        if app.state.backup_last_date != today:
            db_path = Path(app.state.db_path)
            if db_path.exists():
                try:
                    run_backup(db_path)
                    prune_old_backups(BACKUP_DIR, keep=7)
                    app.state.backup_last_date = today
                    app.state.backup_failed = False
                except Exception:
                    app.state.backup_last_date = today
                    app.state.backup_failed = True
        return await call_next(request)

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(status="ok")

    @app.get("/v1/backup/status")
    def backup_status() -> dict[str, Any]:
        """Get the current backup status."""
        today = date.today()

        if app.state.backup_last_date is None or app.state.backup_last_date < today:
            status = "overdue"
        elif app.state.backup_failed:
            status = "failed"
        else:
            status = "ok"

        return {
            "last_backup_date": app.state.backup_last_date.isoformat() if app.state.backup_last_date else None,
            "status": status,
        }

    @app.post("/v1/users", response_model=UserResponse)
    def create_user(payload: UserCreateRequest, conn: Any = Depends(get_conn)) -> UserResponse:
        user_id = str(uuid4())
        now = utc_now_iso()
        conn.execute(
            "INSERT INTO users (user_id, display_name, deleted_at, created_at, updated_at) VALUES (?, ?, NULL, ?, ?)",
            (user_id, payload.display_name.strip(), now, now),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        return row_to_user(row)

    @app.get("/v1/users", response_model=UsersListResponse)
    def list_users(
        include_deleted: bool = Query(default=False),
        conn: Any = Depends(get_conn),
    ) -> UsersListResponse:
        if include_deleted:
            rows = conn.execute("SELECT * FROM users ORDER BY created_at ASC").fetchall()
        else:
            rows = conn.execute("SELECT * FROM users WHERE deleted_at IS NULL ORDER BY created_at ASC").fetchall()
        return UsersListResponse(items=[row_to_user(row) for row in rows])

    @app.delete("/v1/users/{user_id}", response_model=UserResponse)
    def delete_user(user_id: str, conn: Any = Depends(get_conn)) -> UserResponse:
        user_id = ensure_uuid(user_id, "user_id")
        row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="user_not_found")
        now = utc_now_iso()
        conn.execute("UPDATE users SET deleted_at = ?, updated_at = ? WHERE user_id = ?", (now, now, user_id))
        conn.commit()
        updated = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        return row_to_user(updated)

    @app.post("/v1/users/{user_id}/restore", response_model=UserResponse)
    def restore_user(user_id: str, conn: Any = Depends(get_conn)) -> UserResponse:
        user_id = ensure_uuid(user_id, "user_id")
        row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="user_not_found")
        now = utc_now_iso()
        conn.execute("UPDATE users SET deleted_at = NULL, updated_at = ? WHERE user_id = ?", (now, user_id))
        conn.commit()
        updated = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        return row_to_user(updated)

    @app.post("/v1/users/{user_id}/texts", response_model=TextResponse)
    def create_text(user_id: str, payload: TextCreateRequest, conn: Any = Depends(get_conn)) -> TextResponse:
        user_id = ensure_uuid(user_id, "user_id")
        ensure_active_user(conn, user_id)
        text_id = str(uuid4())
        now = utc_now_iso()
        conn.execute(
            "INSERT INTO texts (text_id, user_id, title, content, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (text_id, user_id, payload.title.strip(), payload.content, now, now),
        )
        for i, sentence in enumerate(split_sentences(payload.content)):
            conn.execute(
                "INSERT INTO text_sentences (text_id, sentence_index, sentence_text) VALUES (?, ?, ?)",
                (text_id, i, sentence),
            )
        conn.commit()
        return TextResponse(
            text_id=text_id,
            user_id=user_id,
            title=payload.title.strip(),
            created_at=now,
            updated_at=now,
            progress=parse_progress(conn, user_id, text_id),
        )

    @app.get("/v1/users/{user_id}/texts", response_model=TextListResponse)
    def list_texts(user_id: str, conn: Any = Depends(get_conn)) -> TextListResponse:
        user_id = ensure_uuid(user_id, "user_id")
        ensure_active_user(conn, user_id)
        rows = conn.execute(
            "SELECT text_id, user_id, title, created_at, updated_at FROM texts WHERE user_id = ? ORDER BY created_at ASC",
            (user_id,),
        ).fetchall()
        items = [
            TextResponse(
                text_id=row["text_id"],
                user_id=row["user_id"],
                title=row["title"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                progress=parse_progress(conn, user_id, row["text_id"]),
            )
            for row in rows
        ]
        return TextListResponse(items=items)

    @app.get("/v1/users/{user_id}/texts/{text_id}", response_model=TextResponse)
    def get_text(user_id: str, text_id: str, conn: Any = Depends(get_conn)) -> TextResponse:
        user_id = ensure_uuid(user_id, "user_id")
        text_id = ensure_uuid(text_id, "text_id")
        ensure_active_user(conn, user_id)
        row = ensure_user_text(conn, user_id, text_id)
        return TextResponse(
            text_id=row["text_id"],
            user_id=row["user_id"],
            title=row["title"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            progress=parse_progress(conn, user_id, text_id),
        )

    @app.get("/v1/users/{user_id}/texts/{text_id}/position", response_model=TextPositionResponse)
    def get_text_position(user_id: str, text_id: str, conn: Any = Depends(get_conn)) -> TextPositionResponse:
        user_id = ensure_uuid(user_id, "user_id")
        text_id = ensure_uuid(text_id, "text_id")
        ensure_active_user(conn, user_id)
        ensure_user_text(conn, user_id, text_id)
        row = conn.execute(
            """
            SELECT user_id, text_id, sentence_index, updated_at
            FROM user_text_positions
            WHERE user_id = ? AND text_id = ?
            """,
            (user_id, text_id),
        ).fetchone()
        return row_to_text_position(row, user_id, text_id)

    @app.put("/v1/users/{user_id}/texts/{text_id}/position", response_model=TextPositionResponse)
    def update_text_position(
        user_id: str,
        text_id: str,
        payload: TextPositionUpdateRequest,
        conn: Any = Depends(get_conn),
    ) -> TextPositionResponse:
        user_id = ensure_uuid(user_id, "user_id")
        text_id = ensure_uuid(text_id, "text_id")
        ensure_active_user(conn, user_id)
        ensure_user_text(conn, user_id, text_id)
        now = utc_now_iso()
        conn.execute(
            """
            INSERT INTO user_text_positions (user_id, text_id, sentence_index, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, text_id)
            DO UPDATE SET sentence_index = excluded.sentence_index, updated_at = excluded.updated_at
            """,
            (user_id, text_id, payload.sentence_index, now),
        )
        conn.commit()
        row = conn.execute(
            """
            SELECT user_id, text_id, sentence_index, updated_at
            FROM user_text_positions
            WHERE user_id = ? AND text_id = ?
            """,
            (user_id, text_id),
        ).fetchone()
        return row_to_text_position(row, user_id, text_id)

    @app.patch("/v1/users/{user_id}/texts/{text_id}", response_model=TextResponse)
    def rename_text(user_id: str, text_id: str, payload: TextUpdateRequest, conn: Any = Depends(get_conn)) -> TextResponse:
        user_id = ensure_uuid(user_id, "user_id")
        text_id = ensure_uuid(text_id, "text_id")
        ensure_active_user(conn, user_id)
        ensure_user_text(conn, user_id, text_id)
        now = utc_now_iso()
        conn.execute(
            "UPDATE texts SET title = ?, updated_at = ? WHERE text_id = ? AND user_id = ?",
            (payload.title.strip(), now, text_id, user_id),
        )
        conn.commit()
        updated = ensure_user_text(conn, user_id, text_id)
        return TextResponse(
            text_id=updated["text_id"],
            user_id=updated["user_id"],
            title=updated["title"],
            created_at=updated["created_at"],
            updated_at=updated["updated_at"],
            progress=parse_progress(conn, user_id, text_id),
        )

    @app.delete("/v1/users/{user_id}/texts/{text_id}")
    def delete_text(user_id: str, text_id: str, conn: Any = Depends(get_conn)) -> dict[str, str]:
        user_id = ensure_uuid(user_id, "user_id")
        text_id = ensure_uuid(text_id, "text_id")
        ensure_active_user(conn, user_id)
        ensure_user_text(conn, user_id, text_id)
        conn.execute("DELETE FROM texts WHERE text_id = ? AND user_id = ?", (text_id, user_id))
        conn.commit()
        return {"status": "deleted"}

    @app.get("/v1/users/{user_id}/texts/{text_id}/sentences/{sentence_index}", response_model=SentenceResponse)
    def load_sentence(user_id: str, text_id: str, sentence_index: int, conn: Any = Depends(get_conn)) -> SentenceResponse:
        user_id = ensure_uuid(user_id, "user_id")
        text_id = ensure_uuid(text_id, "text_id")
        ensure_active_user(conn, user_id)
        ensure_user_text(conn, user_id, text_id)

        if sentence_index < 0:
            raise HTTPException(status_code=404, detail="sentence_not_found")

        row = conn.execute(
            "SELECT sentence_text FROM text_sentences WHERE text_id = ? AND sentence_index = ?",
            (text_id, sentence_index),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="sentence_not_found")

        sentence_text = row["sentence_text"]
        tokens = tokenize_eligible(sentence_text)

        now = utc_now_iso()
        conn.execute(
            """
            INSERT OR IGNORE INTO sentences_read (user_id, text_id, sentence_index, word_count, read_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, text_id, sentence_index, len(tokens), now),
        )
        missing = sorted({tok.normalized_word for tok in tokens})
        for normalized_word in missing:
            conn.execute(
                """
                INSERT OR IGNORE INTO user_words (user_id, normalized_word, state, created_at, updated_at)
                VALUES (?, ?, 'never_seen', ?, ?)
                """,
                (user_id, normalized_word, now, now),
            )
        conn.commit()

        if missing:
            placeholders = ",".join("?" for _ in missing)
            state_rows = conn.execute(
                f"SELECT normalized_word, state FROM user_words WHERE user_id = ? AND normalized_word IN ({placeholders})",
                (user_id, *missing),
            ).fetchall()
            state_map = {r["normalized_word"]: r["state"] for r in state_rows}
        else:
            state_map = {}

        max_row = conn.execute(
            "SELECT MAX(sentence_index) AS max_index FROM text_sentences WHERE text_id = ?",
            (text_id,),
        ).fetchone()
        max_index = max_row["max_index"]
        prev_index = sentence_index - 1 if sentence_index > 0 else None
        next_index = sentence_index + 1 if sentence_index < max_index else None

        return SentenceResponse(
            text_id=text_id,
            sentence_index=sentence_index,
            sentence_text=sentence_text,
            prev_sentence_index=prev_index,
            next_sentence_index=next_index,
            tokens=[
                SentenceTokenResponse(
                    token=tok.token,
                    normalized_word=tok.normalized_word,
                    state=state_map.get(tok.normalized_word, "never_seen"),
                )
                for tok in tokens
            ],
        )

    @app.put("/v1/users/{user_id}/words/{normalized_word}", response_model=WordStateResponse)
    def update_word_state(
        user_id: str,
        normalized_word: str,
        payload: WordStateUpdateRequest,
        conn: Any = Depends(get_conn),
    ) -> WordStateResponse:
        user_id = ensure_uuid(user_id, "user_id")
        ensure_active_user(conn, user_id)

        normalized = normalize_token(normalized_word)
        if normalized is None:
            raise HTTPException(status_code=400, detail="invalid_word")

        existing = conn.execute(
            "SELECT * FROM user_words WHERE user_id = ? AND normalized_word = ?",
            (user_id, normalized),
        ).fetchone()

        if not existing:
            now = utc_now_iso()
            conn.execute(
                "INSERT INTO user_words (user_id, normalized_word, state, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, normalized, payload.state, now, now),
            )
            _sync_srs_card(conn, user_id, normalized, payload.state, now)
            conn.commit()
            row = conn.execute(
                "SELECT * FROM user_words WHERE user_id = ? AND normalized_word = ?",
                (user_id, normalized),
            ).fetchone()
            return row_to_word(row)

        if existing["state"] != payload.state:
            now = utc_now_iso()
            conn.execute(
                "UPDATE user_words SET state = ?, updated_at = ? WHERE user_id = ? AND normalized_word = ?",
                (payload.state, now, user_id, normalized),
            )
            _sync_srs_card(conn, user_id, normalized, payload.state, now)
            conn.commit()
            existing = conn.execute(
                "SELECT * FROM user_words WHERE user_id = ? AND normalized_word = ?",
                (user_id, normalized),
            ).fetchone()

        return row_to_word(existing)

    @app.get("/v1/users/{user_id}/words", response_model=WordsListResponse)
    def list_words(
        user_id: str,
        state: str = Query(default="all"),
        page: int = Query(default=1),
        limit: int = Query(default=50),
        conn: Any = Depends(get_conn),
    ) -> WordsListResponse:
        user_id = ensure_uuid(user_id, "user_id")
        ensure_active_user(conn, user_id)

        try:
            f = WordListFilter(state=state, page=page, limit=limit)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"invalid_pagination_or_filter: {exc}") from exc

        where = "WHERE user_id = ?"
        params: list[Any] = [user_id]
        if f.state != "all":
            where += " AND state = ?"
            params.append(f.state)

        total = conn.execute(f"SELECT COUNT(*) AS total FROM user_words {where}", params).fetchone()["total"]

        offset = (f.page - 1) * f.limit
        order_clause = (
            "ORDER BY CASE state "
            "WHEN 'unknown' THEN 0 "
            "WHEN 'known' THEN 1 "
            "WHEN 'never_seen' THEN 2 "
            "ELSE 3 END, normalized_word ASC"
        )
        rows = conn.execute(
            f"SELECT * FROM user_words {where} {order_clause} LIMIT ? OFFSET ?",
            [*params, f.limit, offset],
        ).fetchall()

        return WordsListResponse(
            page=f.page,
            limit=f.limit,
            total=total,
            items=[row_to_word(row) for row in rows],
        )

    @app.get("/v1/users/{user_id}/srs/session", response_model=SrsSessionResponse)
    def get_srs_session(
        user_id: str,
        timezone_offset_minutes: int = Query(default=0, ge=-840, le=840),
        conn: Any = Depends(get_conn),
    ) -> SrsSessionResponse:
        user_id = ensure_uuid(user_id, "user_id")
        ensure_active_user(conn, user_id)
        ensure_srs_cards_for_unknown_words(conn, user_id)

        now = datetime.now(UTC)
        window_start_utc, window_end_utc = srs_window_bounds(now, timezone_offset_minutes)
        window_start_iso = to_iso_utc(window_start_utc)
        window_end_iso = to_iso_utc(window_end_utc)
        due_rows = conn.execute(
            """
            SELECT *
            FROM srs_cards
            WHERE user_id = ? AND is_introduced = 1 AND due_at >= ? AND due_at < ?
            """,
            (user_id, window_start_iso, window_end_iso),
        ).fetchall()
        due_word_order = [row["normalized_word"] for row in due_rows]
        due_display_words = resolve_srs_display_words(conn, user_id, due_word_order)
        due_cards = [
            row_to_srs_card_with_display(row, due_display_words.get(row["normalized_word"], row["normalized_word"]))
            for row in due_rows
        ]
        random.shuffle(due_cards)

        available_new_count = conn.execute(
            """
            SELECT COUNT(*) AS total
            FROM srs_cards
            WHERE user_id = ? AND is_new = 1 AND is_introduced = 0
            """,
            (user_id,),
        ).fetchone()["total"]
        used = get_daily_new_count(conn, user_id, window_start_iso)
        daily_new_remaining = max(0, SRS_DAILY_NEW_CAP - used)
        return SrsSessionResponse(
            due_cards=due_cards,
            daily_new_remaining=daily_new_remaining,
            available_new_count=available_new_count,
            daily_reset_at=to_iso_utc(window_end_utc),
        )

    @app.post("/v1/users/{user_id}/srs/session/add-new", response_model=SrsSessionAddNewResponse)
    def add_srs_new_cards(
        user_id: str,
        payload: SrsSessionAddNewRequest,
        conn: Any = Depends(get_conn),
    ) -> SrsSessionAddNewResponse:
        user_id = ensure_uuid(user_id, "user_id")
        ensure_active_user(conn, user_id)
        ensure_srs_cards_for_unknown_words(conn, user_id)

        now = datetime.now(UTC)
        now_iso = to_iso_utc(now)
        window_start_utc, window_end_utc = srs_window_bounds(now, payload.timezone_offset_minutes)
        window_start_iso = to_iso_utc(window_start_utc)
        used = get_daily_new_count(conn, user_id, window_start_iso)
        cap_remaining = max(0, SRS_DAILY_NEW_CAP - used)
        target = min(payload.count, cap_remaining)

        selected_rows: list[Any] = []
        if target > 0:
            selected_rows = conn.execute(
                """
                SELECT *
                FROM srs_cards
                WHERE user_id = ? AND is_new = 1 AND is_introduced = 0
                ORDER BY created_at ASC, normalized_word ASC
                LIMIT ?
                """,
                (user_id, target),
            ).fetchall()

        selected_words = [row["normalized_word"] for row in selected_rows]
        if selected_words:
            placeholders = ",".join("?" for _ in selected_words)
            conn.execute(
                f"""
                UPDATE srs_cards
                SET is_new = 0, is_introduced = 1, introduced_at = ?, updated_at = ?
                WHERE user_id = ? AND normalized_word IN ({placeholders})
                """,
                (now_iso, now_iso, user_id, *selected_words),
            )
            increment_daily_new_count(conn, user_id, window_start_iso, len(selected_words))
            conn.commit()
            updated_rows = conn.execute(
                f"""
                SELECT *
                FROM srs_cards
                WHERE user_id = ? AND normalized_word IN ({placeholders})
                """,
                (user_id, *selected_words),
            ).fetchall()
            added_word_order = [row["normalized_word"] for row in updated_rows]
            added_display_words = resolve_srs_display_words(conn, user_id, added_word_order)
            added_cards = [
                row_to_srs_card_with_display(row, added_display_words.get(row["normalized_word"], row["normalized_word"]))
                for row in updated_rows
            ]
        else:
            added_cards = []

        random.shuffle(added_cards)
        daily_new_remaining = max(0, SRS_DAILY_NEW_CAP - used - len(added_cards))
        available_new_count = conn.execute(
            """
            SELECT COUNT(*) AS total
            FROM srs_cards
            WHERE user_id = ? AND is_new = 1 AND is_introduced = 0
            """,
            (user_id,),
        ).fetchone()["total"]

        return SrsSessionAddNewResponse(
            added_cards=added_cards,
            daily_new_remaining=daily_new_remaining,
            available_new_count=available_new_count,
            daily_reset_at=to_iso_utc(window_end_utc),
        )

    @app.post("/v1/users/{user_id}/srs/review", response_model=SrsReviewResponse)
    def review_srs_card(
        user_id: str,
        payload: SrsReviewRequest,
        conn: Any = Depends(get_conn),
    ) -> SrsReviewResponse:
        user_id = ensure_uuid(user_id, "user_id")
        ensure_active_user(conn, user_id)
        normalized = normalize_token(payload.normalized_word)
        if normalized is None:
            raise HTTPException(status_code=400, detail="invalid_word")

        row = conn.execute(
            """
            SELECT *
            FROM srs_cards
            WHERE user_id = ? AND normalized_word = ?
            """,
            (user_id, normalized),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="srs_card_not_found")

        now = datetime.now(UTC)
        now_iso = to_iso_utc(now)
        if payload.result == "right":
            current_stage = int(row["stage_index"])
            next_stage = min(current_stage + 1, 7)
            if current_stage >= 7:
                interval_days = SRS_INTERVAL_DAYS[7]
            else:
                interval_days = SRS_INTERVAL_DAYS[current_stage]
            next_due = now + timedelta(days=interval_days)
            conn.execute(
                """
                UPDATE srs_cards
                SET stage_index = ?, due_at = ?, last_reviewed_at = ?, updated_at = ?, is_introduced = 1, is_new = 0
                WHERE user_id = ? AND normalized_word = ?
                """,
                (next_stage, to_iso_utc(next_due), now_iso, now_iso, user_id, normalized),
            )
        else:
            wrong_delay_hours = random.randint(4, 12)
            wrong_due = now + timedelta(hours=wrong_delay_hours)
            conn.execute(
                """
                UPDATE srs_cards
                SET stage_index = 0, due_at = ?, last_reviewed_at = ?, updated_at = ?, is_introduced = 1, is_new = 0
                WHERE user_id = ? AND normalized_word = ?
                """,
                (to_iso_utc(wrong_due), now_iso, now_iso, user_id, normalized),
            )
        conn.commit()

        updated = conn.execute(
            """
            SELECT *
            FROM srs_cards
            WHERE user_id = ? AND normalized_word = ?
            """,
            (user_id, normalized),
        ).fetchone()
        display_word = resolve_srs_display_words(conn, user_id, [normalized]).get(normalized, normalized)
        return SrsReviewResponse(card=row_to_srs_card_with_display(updated, display_word))

    @app.get("/v1/users/{user_id}/texts/{text_id}/progress", response_model=TextProgress)
    def text_progress(user_id: str, text_id: str, conn: Any = Depends(get_conn)) -> TextProgress:
        user_id = ensure_uuid(user_id, "user_id")
        text_id = ensure_uuid(text_id, "text_id")
        ensure_active_user(conn, user_id)
        ensure_user_text(conn, user_id, text_id)
        return parse_progress(conn, user_id, text_id)

    @app.get("/v1/users/{user_id}/words/{normalized_word}/meanings", response_model=MeaningsListResponse)
    def list_meanings(user_id: str, normalized_word: str, conn: Any = Depends(get_conn)) -> MeaningsListResponse:
        user_id = ensure_uuid(user_id, "user_id")
        ensure_active_user(conn, user_id)
        normalized = normalize_token(normalized_word)
        if normalized is None:
            raise HTTPException(status_code=400, detail="invalid_word")

        rows = conn.execute(
            """
            SELECT * FROM meanings
            WHERE user_id = ? AND normalized_word = ?
            ORDER BY created_at ASC, meaning_id ASC
            """,
            (user_id, normalized),
        ).fetchall()
        return MeaningsListResponse(items=[row_to_meaning(row) for row in rows])

    @app.post("/v1/users/{user_id}/words/{normalized_word}/meanings", response_model=MeaningResponse)
    def create_meaning(
        user_id: str,
        normalized_word: str,
        payload: MeaningCreateRequest,
        conn: Any = Depends(get_conn),
    ) -> MeaningResponse:
        user_id = ensure_uuid(user_id, "user_id")
        ensure_active_user(conn, user_id)
        normalized = normalize_token(normalized_word)
        if normalized is None:
            raise HTTPException(status_code=400, detail="invalid_word")

        meaning_id = str(uuid4())
        now = utc_now_iso()
        meaning_text = normalize_meaning_text(payload.meaning_text)
        source_sentence = payload.source_sentence.strip() if payload.source_sentence else None
        conn.execute(
            """
            INSERT INTO meanings (meaning_id, user_id, normalized_word, meaning_text, source_sentence, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (meaning_id, user_id, normalized, meaning_text, source_sentence, now),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM meanings WHERE meaning_id = ?", (meaning_id,)).fetchone()
        return row_to_meaning(row)

    @app.post("/v1/users/{user_id}/words/{normalized_word}/meanings/generate", response_model=MeaningResponse)
    def generate_meaning(
        user_id: str,
        normalized_word: str,
        payload: MeaningGenerateRequest,
        conn: Any = Depends(get_conn),
    ) -> MeaningResponse:
        user_id = ensure_uuid(user_id, "user_id")
        ensure_active_user(conn, user_id)
        normalized = normalize_token(normalized_word)
        if normalized is None:
            raise HTTPException(status_code=400, detail="invalid_word")

        try:
            meaning_raw = app.state.meaning_generator.generate(normalized, payload.sentence_context)
            meaning_text = normalize_english_meaning_text(meaning_raw)
        except MeaningGenerationError as exc:
            msg = str(exc)
            if msg == "meaning_generation_timeout":
                raise HTTPException(status_code=504, detail=msg) from exc
            raise HTTPException(status_code=502, detail=msg) from exc

        now = utc_now_iso()
        meaning_id = str(uuid4())
        conn.execute(
            """
            INSERT INTO meanings (meaning_id, user_id, normalized_word, meaning_text, source_sentence, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (meaning_id, user_id, normalized, meaning_text, payload.sentence_context, now),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM meanings WHERE meaning_id = ?", (meaning_id,)).fetchone()
        return row_to_meaning(row)

    @app.put("/v1/users/{user_id}/words/{normalized_word}/meanings/{meaning_id}", response_model=MeaningResponse)
    def update_meaning(
        user_id: str,
        normalized_word: str,
        meaning_id: str,
        payload: MeaningUpdateRequest,
        conn: Any = Depends(get_conn),
    ) -> MeaningResponse:
        user_id = ensure_uuid(user_id, "user_id")
        meaning_id = ensure_uuid(meaning_id, "meaning_id")
        ensure_active_user(conn, user_id)
        normalized = normalize_token(normalized_word)
        if normalized is None:
            raise HTTPException(status_code=400, detail="invalid_word")

        meaning_text = normalize_meaning_text(payload.meaning_text)
        cursor = conn.execute(
            "UPDATE meanings SET meaning_text = ? WHERE meaning_id = ? AND user_id = ? AND normalized_word = ?",
            (meaning_text, meaning_id, user_id, normalized),
        )
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="meaning_not_found")
        row = conn.execute("SELECT * FROM meanings WHERE meaning_id = ?", (meaning_id,)).fetchone()
        return row_to_meaning(row)

    @app.delete("/v1/users/{user_id}/words/{normalized_word}/meanings/{meaning_id}")
    def delete_meaning(user_id: str, normalized_word: str, meaning_id: str, conn: Any = Depends(get_conn)) -> dict[str, str]:
        user_id = ensure_uuid(user_id, "user_id")
        meaning_id = ensure_uuid(meaning_id, "meaning_id")
        ensure_active_user(conn, user_id)
        normalized = normalize_token(normalized_word)
        if normalized is None:
            raise HTTPException(status_code=400, detail="invalid_word")
        cursor = conn.execute(
            "DELETE FROM meanings WHERE meaning_id = ? AND user_id = ? AND normalized_word = ?",
            (meaning_id, user_id, normalized),
        )
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="meaning_not_found")
        return {"status": "deleted"}

    @app.get("/v1/users/{user_id}/words/{normalized_word}/details", response_model=WordDetailsResponse)
    def get_word_details(user_id: str, normalized_word: str, conn: Any = Depends(get_conn)) -> WordDetailsResponse:
        user_id = ensure_uuid(user_id, "user_id")
        ensure_active_user(conn, user_id)
        normalized = normalize_token(normalized_word)
        if normalized is None:
            raise HTTPException(status_code=400, detail="invalid_word")

        row = conn.execute(
            """
            SELECT user_id, normalized_word, mnemonic, created_at, updated_at
            FROM word_details
            WHERE user_id = ? AND normalized_word = ?
            """,
            (user_id, normalized),
        ).fetchone()
        return row_to_word_details(row, user_id, normalized)

    @app.put("/v1/users/{user_id}/words/{normalized_word}/details", response_model=WordDetailsResponse)
    def update_word_details(
        user_id: str,
        normalized_word: str,
        payload: WordDetailsUpdateRequest,
        conn: Any = Depends(get_conn),
    ) -> WordDetailsResponse:
        user_id = ensure_uuid(user_id, "user_id")
        ensure_active_user(conn, user_id)
        normalized = normalize_token(normalized_word)
        if normalized is None:
            raise HTTPException(status_code=400, detail="invalid_word")

        mnemonic = (payload.mnemonic or "").strip() or None
        now = utc_now_iso()
        conn.execute(
            """
            INSERT INTO word_details (user_id, normalized_word, mnemonic, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id, normalized_word)
            DO UPDATE SET mnemonic = excluded.mnemonic, updated_at = excluded.updated_at
            """,
            (user_id, normalized, mnemonic, now, now),
        )
        conn.commit()
        row = conn.execute(
            """
            SELECT user_id, normalized_word, mnemonic, created_at, updated_at
            FROM word_details
            WHERE user_id = ? AND normalized_word = ?
            """,
            (user_id, normalized),
        ).fetchone()
        return row_to_word_details(row, user_id, normalized)

    @app.get("/v1/users/{user_id}/progress/history", response_model=ProgressHistoryResponse)
    def progress_history(
        user_id: str,
        range: str = Query(default="month"),
        conn: Any = Depends(get_conn),
    ) -> ProgressHistoryResponse:
        user_id = ensure_uuid(user_id, "user_id")
        ensure_active_user(conn, user_id)
        if range not in ("month", "year", "all"):
            raise HTTPException(status_code=400, detail="invalid_range")
        rows = conn.execute(
            "SELECT state, created_at, updated_at FROM user_words WHERE user_id = ?",
            (user_id,),
        ).fetchall()
        return ProgressHistoryResponse(range=range, buckets=_bucket_progress_history(rows, range))

    @app.get("/v1/users/{user_id}/progress/words-read", response_model=WordsReadHistoryResponse)
    def words_read_history(
        user_id: str,
        range: str = Query(default="month"),
        conn: Any = Depends(get_conn),
    ) -> WordsReadHistoryResponse:
        user_id = ensure_uuid(user_id, "user_id")
        ensure_active_user(conn, user_id)
        if range not in ("month", "year", "all"):
            raise HTTPException(status_code=400, detail="invalid_range")
        rows = conn.execute(
            "SELECT word_count, read_at FROM sentences_read WHERE user_id = ?",
            (user_id,),
        ).fetchall()
        return WordsReadHistoryResponse(range=range, buckets=_bucket_words_read(rows, range))

    return app


app = create_app()
