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
    language: str = "hebrew"


class TextUpdateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)


class TextPositionResponse(BaseModel):
    user_id: str
    text_id: str
    sentence_index: int
    updated_at: datetime | None


class TextPositionUpdateRequest(BaseModel):
    sentence_index: int = Field(ge=0)


class TextProgress(BaseModel):
    known_count: int
    unknown_count: int
    never_seen_count: int
    known_percent: float
    stage4_percent: float
    total_words: int


class TextResponse(BaseModel):
    text_id: str
    user_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    last_read_at: datetime | None = None
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
    language: str
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


class MeaningCreateRequest(BaseModel):
    meaning_text: str = Field(min_length=1, max_length=500)
    source_sentence: str | None = Field(default=None, max_length=1000)


class MeaningUpdateRequest(BaseModel):
    meaning_text: str = Field(min_length=1, max_length=500)


class MeaningGenerateRequest(BaseModel):
    sentence_context: str | None = None


class WordDetailsResponse(BaseModel):
    user_id: str
    normalized_word: str
    mnemonic: str | None
    mnemonic_reveal_count: int
    created_at: datetime | None
    updated_at: datetime | None


class WordDetailsUpdateRequest(BaseModel):
    mnemonic: str | None = Field(default=None, max_length=500)


class SrsCardResponse(BaseModel):
    user_id: str
    language: str
    normalized_word: str
    display_word: str
    is_new: bool
    is_introduced: bool
    stage_index: int
    due_at: datetime
    introduced_at: datetime | None
    last_reviewed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class SrsSessionResponse(BaseModel):
    due_cards: list[SrsCardResponse]
    daily_new_remaining: int
    available_new_count: int
    daily_reset_at: datetime


class SrsSessionAddNewRequest(BaseModel):
    count: int = Field(default=10, ge=1, le=100)
    timezone_offset_minutes: int = Field(default=0, ge=-840, le=840)
    language: str = "hebrew"


class SrsSessionAddNewResponse(BaseModel):
    added_cards: list[SrsCardResponse]
    daily_new_remaining: int
    available_new_count: int
    daily_reset_at: datetime


class SrsReviewRequest(BaseModel):
    normalized_word: str = Field(min_length=1)
    result: Literal["right", "wrong"]
    language: str = "hebrew"
    timezone_offset_minutes: int = Field(default=0, ge=-840, le=840)


class SrsReviewResponse(BaseModel):
    card: SrsCardResponse


class SrsDeleteResponse(BaseModel):
    normalized_word: str
    deleted_at: datetime


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


class ProgressBucket(BaseModel):
    date: str
    cumulative_known: int
    cumulative_encountered: int


class ProgressHistoryResponse(BaseModel):
    range: str
    buckets: list[ProgressBucket]


class WordsReadBucket(BaseModel):
    date: str
    cumulative_words: int
    cumulative_words_nikkud_off: int


class WordsReadHistoryResponse(BaseModel):
    range: str
    buckets: list[WordsReadBucket]


class WordsReadSummary(BaseModel):
    words_today: int
    daily_rate_14d: float
    projected_month: int
    projected_year: int


class StreakDay(BaseModel):
    local_day: str
    active: bool
    is_today: bool
    reader_sentence_count: int
    word_state_count: int
    srs_review_count: int
    srs_new_count: int
    languages: list[str]


class StreakResponse(BaseModel):
    current_streak: int
    longest_streak: int
    active_today: bool
    today_local_day: str
    next_reset_at: datetime
    last_active_local_day: str | None
    days: list[StreakDay]


class SrsHistoryBucket(BaseModel):
    date: str
    stage0: int
    stage1: int
    stage2: int
    stage3: int
    stage4_plus: int


class SrsHistoryResponse(BaseModel):
    range: str
    buckets: list[SrsHistoryBucket]


class SentenceAnalysisResponse(BaseModel):
    text: str


class SrsPostponeRequest(BaseModel):
    target_due_count: int = Field(ge=0)


class SrsPostponeResponse(BaseModel):
    postponed_count: int
    due_before: int
    due_after: int
    postponed_until: datetime


# Torah mode models

class TorahVerse(BaseModel):
    verse: int
    torah_he: str
    modern_he: str | None = None
    rashi_voweled: str | None = None


class TorahChapterResponse(BaseModel):
    book: str
    chapter: int
    verses: list[TorahVerse]


class TorahPositionResponse(BaseModel):
    user_id: str
    book: str
    chapter: int
    verse: int
    updated_at: str


class TorahPositionUpdate(BaseModel):
    book: str
    chapter: int
    verse: int
    timezone_offset_minutes: int = 0
