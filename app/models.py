from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

WordState = Literal["known", "unknown", "never_seen"]


class ErrorEnvelope(BaseModel):
    error: dict[str, str]


class UserCreateRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=100)


class UserResponse(BaseModel):
    user_id: str
    display_name: str
    deleted_at: datetime | None
    created_at: datetime
    updated_at: datetime


class UsersListResponse(BaseModel):
    items: list[UserResponse]


class TextCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)


class TextUpdateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)


class TextProgress(BaseModel):
    known_count: int
    unknown_count: int
    never_seen_count: int
    known_percent: float


class TextResponse(BaseModel):
    text_id: str
    user_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    progress: TextProgress


class TextListResponse(BaseModel):
    items: list[TextResponse]


class SentenceTokenResponse(BaseModel):
    token: str
    normalized_word: str
    state: WordState


class SentenceResponse(BaseModel):
    text_id: str
    sentence_index: int
    sentence_text: str
    prev_sentence_index: int | None
    next_sentence_index: int | None
    tokens: list[SentenceTokenResponse]


class WordStateUpdateRequest(BaseModel):
    state: WordState


class WordStateResponse(BaseModel):
    user_id: str
    normalized_word: str
    state: WordState
    created_at: datetime
    updated_at: datetime


class WordsListResponse(BaseModel):
    page: int
    limit: int
    total: int
    items: list[WordStateResponse]


class MeaningResponse(BaseModel):
    meaning_id: str
    user_id: str
    normalized_word: str
    meaning_text: str
    source_sentence: str | None
    created_at: datetime


class MeaningsListResponse(BaseModel):
    items: list[MeaningResponse]


class MeaningGenerateRequest(BaseModel):
    sentence_context: str | None = None


class HealthResponse(BaseModel):
    status: str


class WordListFilter(BaseModel):
    model_config = ConfigDict(extra="forbid")

    state: Literal["all", "unknown", "known", "never_seen"] = "all"
    page: int = 1
    limit: int = 50

    @field_validator("page")
    @classmethod
    def validate_page(cls, value: int) -> int:
        if value < 1:
            raise ValueError("page must be >= 1")
        return value

    @field_validator("limit")
    @classmethod
    def validate_limit(cls, value: int) -> int:
        if value < 1 or value > 200:
            raise ValueError("limit must be between 1 and 200")
        return value
