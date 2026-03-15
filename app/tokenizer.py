from __future__ import annotations

import re
from dataclasses import dataclass

HEBREW_MAQAF = "\u05be"
NIKKUD_RE = re.compile(r"[\u0591-\u05bd\u05bf-\u05c7]")
PUNCT_ONLY_RE = re.compile(r"^[^\w\u0590-\u05ff]+$", re.UNICODE)
NUMERIC_ONLY_RE = re.compile(r"^\d+$")
TOKEN_RE = re.compile(r"[\s,;:!?()\[\]{}\"'""׳״]+")


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


def normalize_token(token: str, language: str = "hebrew") -> str | None:
    if language == "hebrew":
        token = NIKKUD_RE.sub("", token)
    token = token.strip()
    if not token:
        return None
    if NUMERIC_ONLY_RE.match(token):
        return None
    if language == "hebrew":
        if PUNCT_ONLY_RE.match(token):
            return None
        contains_non_hebrew_alpha = any(("a" <= c.lower() <= "z") for c in token)
        if contains_non_hebrew_alpha:
            token = token.lower()
    elif language == "latin":
        token = token.strip(".,;:!?\"'""''")
        if not token:
            return None
        if PUNCT_ONLY_RE.match(token):
            return None
        token = token.lower()
    return token


def tokenize_eligible(text: str, language: str = "hebrew") -> list[TokenInfo]:
    out: list[TokenInfo] = []
    for base in TOKEN_RE.split(text):
        if not base:
            continue
        if language == "hebrew":
            chunks = [part for part in base.split(HEBREW_MAQAF) if part]
        else:
            chunks = [base]
        for chunk in chunks:
            normalized = normalize_token(chunk, language)
            if normalized is None:
                continue
            out.append(TokenInfo(token=chunk, normalized_word=normalized))
    return out
