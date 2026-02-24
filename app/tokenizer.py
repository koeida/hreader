from __future__ import annotations

import re
from dataclasses import dataclass

HEBREW_MAQAF = "\u05be"
NIKKUD_RE = re.compile(r"[\u0591-\u05bd\u05bf-\u05c7]")
PUNCT_ONLY_RE = re.compile(r"^[^\w\u0590-\u05ff]+$", re.UNICODE)
NUMERIC_ONLY_RE = re.compile(r"^\d+$")
TOKEN_RE = re.compile(r"[\s,;:!?()\[\]{}\"'“”׳״]+")


@dataclass(frozen=True)
class TokenInfo:
    token: str
    normalized_word: str


def strip_nikkud(value: str) -> str:
    return NIKKUD_RE.sub("", value)


def _candidate_chunks(text: str) -> list[str]:
    chunks: list[str] = []
    for base in TOKEN_RE.split(text):
        if not base:
            continue
        chunks.extend([part for part in base.split(HEBREW_MAQAF) if part])
    return chunks


def normalize_token(token: str) -> str | None:
    cleaned = strip_nikkud(token).strip()
    if not cleaned:
        return None
    if NUMERIC_ONLY_RE.match(cleaned):
        return None
    if PUNCT_ONLY_RE.match(cleaned):
        return None
    contains_non_hebrew_alpha = any(("a" <= c.lower() <= "z") for c in cleaned)
    if contains_non_hebrew_alpha:
        cleaned = cleaned.lower()
    if NUMERIC_ONLY_RE.match(cleaned):
        return None
    return cleaned


def tokenize_eligible(text: str) -> list[TokenInfo]:
    out: list[TokenInfo] = []
    for chunk in _candidate_chunks(text):
        normalized = normalize_token(chunk)
        if normalized is None:
            continue
        out.append(TokenInfo(token=chunk, normalized_word=normalized))
    return out
