from __future__ import annotations

import re
import subprocess


class MeaningGenerationError(Exception):
    pass


HEBREW_CHARS_RE = re.compile(r"[\u0590-\u05FF]")
ASCII_LETTER_RE = re.compile(r"[A-Za-z]")


def normalize_english_meaning_text(value: str) -> str:
    normalized = " ".join(value.strip().split())
    if not normalized:
        raise MeaningGenerationError("meaning_generation_empty")
    if HEBREW_CHARS_RE.search(normalized) or not ASCII_LETTER_RE.search(normalized):
        raise MeaningGenerationError("meaning_generation_non_english")
    return normalized


class MeaningGenerator:
    def __init__(self, command: list[str] | None = None, timeout_seconds: int = 15) -> None:
        self.command = command or ["codex", "exec"]
        self.timeout_seconds = timeout_seconds

    def generate(self, normalized_word: str, sentence_context: str | None) -> str:
        prompt = (
            "Give one concise English meaning/gloss for the target word used in sentence context. "
            "Return only the meaning text, no labels.\n"
            f"Target word: {normalized_word}\n"
            f"Sentence: {sentence_context or ''}\n"
        )
        try:
            result = subprocess.run(
                [*self.command, prompt],
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise MeaningGenerationError("meaning_generation_timeout") from exc
        except OSError as exc:
            raise MeaningGenerationError("meaning_generation_unavailable") from exc

        if result.returncode != 0:
            raise MeaningGenerationError("meaning_generation_failed")

        return normalize_english_meaning_text(result.stdout or "")


class FakeMeaningGenerator:
    def __init__(self) -> None:
        self.calls = 0

    def generate(self, normalized_word: str, sentence_context: str | None) -> str:
        self.calls += 1
        suffix = f" ({self.calls})"
        return f"Concise meaning for {normalized_word}{suffix}"
