from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.db import DEFAULT_DB_PATH, get_connection, init_db
from app.meanings import MeaningGenerationError, MeaningGenerator, normalize_english_meaning_text
from app.models import (
    HealthResponse,
    MeaningCreateRequest,
    MeaningGenerateRequest,
    MeaningsListResponse,
    MeaningResponse,
    MeaningUpdateRequest,
    SentenceResponse,
    SentenceTokenResponse,
    TextCreateRequest,
    TextListResponse,
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
)
from app.tokenizer import normalize_token, tokenize_eligible


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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

    known = 0
    unknown = 0
    never_seen = 0
    for word in unique_words:
        state = state_map.get(word, "never_seen")
        if state == "known":
            known += 1
        elif state == "unknown":
            unknown += 1
        else:
            never_seen += 1

    total = len(unique_words)
    known_percent = round((known / total) * 100.0, 2) if total > 0 else 0.0
    return TextProgress(
        known_count=known,
        unknown_count=unknown,
        never_seen_count=never_seen,
        known_percent=known_percent,
    )


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


def normalize_meaning_text(value: str) -> str:
    normalized = " ".join(value.strip().split())
    if not normalized:
        raise HTTPException(status_code=400, detail="invalid_meaning_text")
    return normalized


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

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(status="ok")

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

    return app


app = create_app()
