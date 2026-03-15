from typing import Literal

Language = Literal["hebrew", "latin"]
SUPPORTED_LANGUAGES: set[str] = {"hebrew", "latin"}
LANGUAGE_DIR = {"hebrew": "rtl", "latin": "ltr"}
LANGUAGE_LANG_CODE = {"hebrew": "he", "latin": "la"}


def validate_language(lang: str) -> Language:
    if lang not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unsupported language: {lang!r}")
    return lang  # type: ignore[return-value]
