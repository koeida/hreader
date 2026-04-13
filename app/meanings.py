from __future__ import annotations

import re
import subprocess


class MeaningGenerationError(Exception):
    pass


HEBREW_CHARS_RE = re.compile(r"[\u0590-\u05FF]")
ASCII_LETTER_RE = re.compile(r"[A-Za-z]")

LANGUAGE_PROMPT_PREFIX = {
    "hebrew": "You are a Hebrew tutor. Give one concise English meaning/gloss for the target Hebrew word used in sentence context.",
    "latin": "You are a Latin tutor. Give one concise English meaning/gloss for the target Latin word used in sentence context.",
}

RESTATEMENT_EXAMPLE = (
    "Example of the style you should imitate:\n"
    'Original: "The tyrant hypothesized that slaying the burglars in the suburbs would inaugurate an era of peace."\n'
    'Restatement: "The powerful and evil ruler believed that killing all the criminals who break into homes in order to steal stuff '
    "(those criminals living just outside the city) would cause a time of greater peace to begin.\"\n"
    "Notice: every difficult word is replaced with plain words, parenthetical asides clarify concepts, "
    "and the restatement is noticeably longer and more explicit than the original.\n"
)

RESTATEMENT_PROMPT_PREFIX = {
    "hebrew": (
        "You are a Hebrew language tutor. A student is reading a Hebrew text. "
        "Restate the TARGET SENTENCE in simpler, more explanatory Hebrew. "
        "Replace each difficult or rare word with a plain equivalent, add brief parenthetical clarifications "
        "for implied or culturally dense concepts, and make every part of the meaning fully explicit. "
        "The restatement should be noticeably longer than the original. "
        "Do NOT translate — stay entirely in Hebrew. "
        "Return ONLY the restatement, no labels or meta-commentary.\n\n"
        + RESTATEMENT_EXAMPLE
    ),
    "latin": (
        "You are a Latin language tutor. A student is reading a Latin text. "
        "Restate the TARGET SENTENCE in simpler, more explanatory Latin. "
        "Replace each difficult or rare word with a plain equivalent, add brief parenthetical clarifications "
        "for implied or culturally dense concepts, and make every part of the meaning fully explicit. "
        "The restatement should be noticeably longer than the original. "
        "Do NOT translate — stay entirely in Latin. "
        "Return ONLY the restatement, no labels or meta-commentary.\n\n"
        + RESTATEMENT_EXAMPLE
    ),
}

GRAMMAR_PROMPT_PREFIX = {
    "hebrew": (
        "You are a Hebrew grammar expert. Analyze the grammatical structure of the following Hebrew sentence. "
        "Identify: the main subject (with gender and number), the main verb (root, binyan, tense/aspect, "
        "person, number, gender), any direct and indirect objects, prepositional phrases, construct chains, "
        "relative clauses, and other notable features. Write the analysis in clear English. "
        "Return ONLY the analysis, no introductory text."
    ),
    "latin": (
        "You are a Latin grammar expert. Analyze the grammatical structure of the following Latin sentence. "
        "Identify: the main subject (case, number, gender), the main verb (conjugation, tense, mood, voice, "
        "person, number), any objects and their cases, subordinate clauses, ablatives absolute, and other "
        "notable grammatical features. Write the analysis in clear English. "
        "Return ONLY the analysis, no introductory text."
    ),
}


def normalize_english_meaning_text(value: str) -> str:
    normalized = " ".join(value.strip().split())
    if not normalized:
        raise MeaningGenerationError("meaning_generation_empty")
    if HEBREW_CHARS_RE.search(normalized) or not ASCII_LETTER_RE.search(normalized):
        raise MeaningGenerationError("meaning_generation_non_english")
    return normalized


class MeaningGenerator:
    def __init__(self, command: list[str] | None = None, timeout_seconds: int = 120) -> None:
        self.command = command or ["codex", "exec"]
        self.timeout_seconds = timeout_seconds

    def generate(self, normalized_word: str, sentence_context: str | None, language: str = "hebrew") -> str:
        prefix = LANGUAGE_PROMPT_PREFIX.get(language, LANGUAGE_PROMPT_PREFIX["hebrew"])
        prompt = (
            f"{prefix} "
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

    def _run_prompt(self, prompt: str) -> str:
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
        text = " ".join((result.stdout or "").strip().split())
        if not text:
            raise MeaningGenerationError("meaning_generation_empty")
        return text

    def generate_restatement(self, sentence: str, context_sentences: list[str], language: str = "hebrew") -> str:
        prefix = RESTATEMENT_PROMPT_PREFIX.get(language, RESTATEMENT_PROMPT_PREFIX["hebrew"])
        context_block = ""
        if context_sentences:
            context_block = "Previous context:\n" + "\n".join(context_sentences) + "\n\n"
        prompt = f"{prefix}\n\n{context_block}Target sentence: {sentence}\n"
        return self._run_prompt(prompt)

    def generate_grammar(self, sentence: str, language: str = "hebrew") -> str:
        prefix = GRAMMAR_PROMPT_PREFIX.get(language, GRAMMAR_PROMPT_PREFIX["hebrew"])
        prompt = f"{prefix}\n\nSentence: {sentence}\n"
        return self._run_prompt(prompt)


class FakeMeaningGenerator:
    def __init__(self) -> None:
        self.calls = 0

    def generate(self, normalized_word: str, sentence_context: str | None, language: str = "hebrew") -> str:
        self.calls += 1
        suffix = f" ({self.calls})"
        return f"Concise meaning for {normalized_word}{suffix}"

    def generate_restatement(self, sentence: str, context_sentences: list[str], language: str = "hebrew") -> str:
        self.calls += 1
        return f"Simplified restatement ({self.calls}): {sentence}"

    def generate_grammar(self, sentence: str, language: str = "hebrew") -> str:
        self.calls += 1
        return f"Grammar analysis ({self.calls}): Subject + Verb + Object structure."
