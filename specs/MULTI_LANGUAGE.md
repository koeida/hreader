# Multi-Language Support: Hebrew + Latin

**Goal:** Add Latin as a second language. All vocabulary tracking, SRS, and progress are independent per language; all data belongs to the same user account. Latin is LTR, Hebrew is RTL.

---

## Scope & Non-Goals

**In scope:**
- Language toggle in header (Hebrew ↔ Latin)
- Language-scoped texts, words, SRS, progress, meanings, mnemonics
- RTL/LTR direction switching in reader and SRS card
- Latin tokenizer (lowercase, no diacritics to strip)
- Meaning generation prompt updated for Latin
- Database migration: existing data tagged `language='hebrew'`
- Sample Latin texts (seeded via script)

**Out of scope:**
- Per-language user settings/profiles
- Language-specific SRS schedules
- Automatic language detection from text content
- More than two languages (design should not assume exactly two, but only these two ship)

---

## Refactorings (Phase 0 — do first, no behavior change)

### 0a. Remove `activeView` from JS state

`state.activeView` is a legacy duplicate of `state.currentView`. The codebase has both; `currentView` is the live one. Delete `activeView` and fix any remaining callers. This reduces confusion before we add `currentLanguage`.

### 0b. Consolidate tokenizer into class

`tokenizer.py` currently exports two module-level functions. Wrap them in a `Tokenizer` class parameterized by language — or just add a `language` parameter to each function. The function approach is simpler and fits the existing style. Keep it functions.

### 0c. Move language constants to one place

In `app/languages.py` (new file, ~20 lines):

```python
from typing import Literal

Language = Literal["hebrew", "latin"]
SUPPORTED_LANGUAGES: set[str] = {"hebrew", "latin"}
LANGUAGE_DIR = {"hebrew": "rtl", "latin": "ltr"}
LANGUAGE_LANG_CODE = {"hebrew": "he", "latin": "la"}

def validate_language(lang: str) -> Language:
    if lang not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unsupported language: {lang!r}")
    return lang  # type: ignore[return-value]
```

Import this everywhere instead of scattering the string literals.

---

## Phase 1: Database Schema

### 1.1 Columns to add

| Table | Column | Type | Default | Notes |
|---|---|---|---|---|
| `texts` | `language` | `TEXT NOT NULL` | `'hebrew'` | Which language this text is in |
| `user_words` | `language` | `TEXT NOT NULL` | `'hebrew'` | Scope word knowledge per-language |
| `meanings` | `language` | `TEXT NOT NULL` | `'hebrew'` | Scope meanings per-language |
| `word_details` | `language` | `TEXT NOT NULL` | `'hebrew'` | Scope mnemonics per-language |
| `srs_cards` | `language` | `TEXT NOT NULL` | `'hebrew'` | Scope SRS per-language |
| `srs_daily_new_counts` | `language` | `TEXT NOT NULL` | `'hebrew'` | Separate daily cap per-language |

Tables that do **not** need `language`:
- `users` — spans all languages
- `text_sentences` — inherits language from its text
- `user_text_positions` — references `text_id`; language derivable if ever needed
- `sentences_read` — same as above

### 1.2 Constraint changes

SQLite cannot ALTER TABLE to change PRIMARY KEY or UNIQUE constraints. These tables need recreation via the standard rename-create-copy-drop migration:

**`user_words`**
```sql
-- Old UNIQUE(user_id, normalized_word)
-- New UNIQUE(user_id, language, normalized_word)
CREATE TABLE user_words_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    language TEXT NOT NULL DEFAULT 'hebrew',
    normalized_word TEXT NOT NULL,
    state TEXT NOT NULL CHECK(state IN ('known', 'unknown', 'never_seen')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    UNIQUE(user_id, language, normalized_word)
);
INSERT INTO user_words_new SELECT id, user_id, 'hebrew', normalized_word, state, created_at, updated_at FROM user_words;
DROP TABLE user_words;
ALTER TABLE user_words_new RENAME TO user_words;
CREATE INDEX IF NOT EXISTS idx_words_user_state ON user_words(user_id, language, state);
```

**`srs_cards`** (PK change)
```sql
CREATE TABLE srs_cards_new (
    user_id TEXT NOT NULL,
    language TEXT NOT NULL DEFAULT 'hebrew',
    normalized_word TEXT NOT NULL,
    is_new INTEGER NOT NULL DEFAULT 1,
    is_introduced INTEGER NOT NULL DEFAULT 0,
    stage_index INTEGER NOT NULL DEFAULT 0,
    due_at TEXT NOT NULL,
    introduced_at TEXT,
    last_reviewed_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (user_id, language, normalized_word),
    FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
INSERT INTO srs_cards_new SELECT user_id, 'hebrew', normalized_word, ... FROM srs_cards;
DROP TABLE srs_cards;
ALTER TABLE srs_cards_new RENAME TO srs_cards;
CREATE INDEX IF NOT EXISTS idx_srs_cards_user_due ON srs_cards(user_id, language, due_at);
CREATE INDEX IF NOT EXISTS idx_srs_cards_user_new ON srs_cards(user_id, language, is_new, is_introduced);
```

**`srs_daily_new_counts`** (PK change)
```sql
CREATE TABLE srs_daily_new_counts_new (
    user_id TEXT NOT NULL,
    language TEXT NOT NULL DEFAULT 'hebrew',
    window_start_at TEXT NOT NULL,
    new_count INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (user_id, language, window_start_at),
    FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
INSERT INTO srs_daily_new_counts_new SELECT user_id, 'hebrew', window_start_at, new_count FROM srs_daily_new_counts;
DROP TABLE srs_daily_new_counts;
ALTER TABLE srs_daily_new_counts_new RENAME TO srs_daily_new_counts;
```

For `texts`, `meanings`, `word_details`: simple `ALTER TABLE ... ADD COLUMN` with default value is sufficient since their PKs and UNIQUE constraints don't change.

### 1.3 Migration implementation

In `app/db.py`, `init_db()` runs once per process start. Extend it with a migration block:

```python
def _migrate(conn):
    """Idempotent schema migrations. Safe to run on every startup."""
    # Check if language column already exists in texts
    cols = {row[1] for row in conn.execute("PRAGMA table_info(texts)")}
    if "language" not in cols:
        _run_language_migration(conn)

def _run_language_migration(conn):
    # ALTER TABLE for simple additions
    conn.execute("ALTER TABLE texts ADD COLUMN language TEXT NOT NULL DEFAULT 'hebrew'")
    conn.execute("ALTER TABLE meanings ADD COLUMN language TEXT NOT NULL DEFAULT 'hebrew'")
    conn.execute("ALTER TABLE word_details ADD COLUMN language TEXT NOT NULL DEFAULT 'hebrew'")
    # Recreate tables that need PK/UNIQUE changes
    # (full SQL as shown above)
    conn.commit()
```

Call `_migrate(conn)` at the end of `init_db()`.

### 1.4 Validation gate

- `make test` — all 55 existing tests pass unchanged (language defaults to 'hebrew' everywhere)
- Manually inspect DB with `sqlite3 data/hreader.db ".schema user_words"` to confirm new column

---

## Phase 2: Backend Changes

### 2.1 New query parameter: `language`

Add `language: str = "hebrew"` as a query param to every endpoint that touches language-scoped data. On receipt, call `validate_language(language)` and raise HTTP 400 if invalid.

Affected endpoints:
```
POST   /v1/users/{user_id}/texts           # body: add language field
GET    /v1/users/{user_id}/texts           # ?language=hebrew
GET    /v1/users/{user_id}/words           # ?language=hebrew
PUT    /v1/users/{user_id}/words/{word}    # ?language=hebrew
GET/POST/PUT/DELETE  .../words/{word}/meanings   # ?language=hebrew
GET/PUT  .../words/{word}/details          # ?language=hebrew
GET    /v1/users/{user_id}/srs/session     # ?language=hebrew (already has timezone_offset_minutes)
POST   /v1/users/{user_id}/srs/session/add-new  # body: add language field
POST   /v1/users/{user_id}/srs/review      # body: add language field
GET    /v1/users/{user_id}/progress/history     # ?language=hebrew
GET    /v1/users/{user_id}/progress/words-read  # ?language=hebrew
```

**Text creation model change:**
```python
class TextCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    language: str = "hebrew"  # NEW
```

**SrsSessionAddNewRequest:**
```python
class SrsSessionAddNewRequest(BaseModel):
    count: int = Field(10, ge=1, le=100)
    timezone_offset_minutes: int = Field(0, ge=-840, le=840)
    language: str = "hebrew"  # NEW
```

**SrsReviewRequest:**
```python
class SrsReviewRequest(BaseModel):
    normalized_word: str
    result: Literal["right", "wrong"]
    language: str = "hebrew"  # NEW
```

### 2.2 Thread `language` through all DB queries

Every SQL query that touches a language-scoped table gets `AND language = ?` added to its WHERE clause (or `language = ?` in its INSERT). Example:

```python
# Before
conn.execute("SELECT * FROM user_words WHERE user_id = ?", (user_id,))
# After
conn.execute("SELECT * FROM user_words WHERE user_id = ? AND language = ?", (user_id, language))
```

All row mappers (`row_to_word`, `row_to_srs_card`, etc.) must be updated to include the `language` field. Add `language` to relevant response models:

```python
class WordStateResponse(BaseModel):
    user_id: str
    language: str  # NEW
    normalized_word: str
    state: WordState
    ...

class SrsCardResponse(BaseModel):
    user_id: str
    language: str  # NEW
    normalized_word: str
    ...
```

### 2.3 Tokenizer: Latin support

In `app/tokenizer.py`, update `normalize_token()` and `tokenize_eligible()`:

```python
def normalize_token(token: str, language: str = "hebrew") -> str | None:
    if language == "hebrew":
        token = NIKKUD_RE.sub("", token)
        # split on HEBREW_MAQAF already done in tokenize_eligible
    # Common path
    token = token.strip()
    if not token:
        return None
    if NUMERIC_ONLY_RE.match(token):
        return None
    if language == "hebrew":
        if PUNCT_ONLY_RE.match(token):
            return None
        # lowercase Latin chars within Hebrew text (existing behavior)
        if re.search(r"[a-zA-Z]", token):
            token = token.lower()
    elif language == "latin":
        # Strip trailing punctuation (periods attached to sentence-final words)
        token = token.strip(".,;:!?\"'""''")
        if not token:
            return None
        if PUNCT_ONLY_RE.match(token):
            return None
        token = token.lower()
    return token

def tokenize_eligible(text: str, language: str = "hebrew") -> list[TokenInfo]:
    parts = TOKEN_RE.split(text)
    result = []
    for part in parts:
        chunks = [part]
        if language == "hebrew":
            # Split on Hebrew maqaf
            chunks = []
            for sub in part.split(HEBREW_MAQAF):
                chunks.append(sub)
        for chunk in chunks:
            normalized = normalize_token(chunk, language)
            if normalized:
                result.append(TokenInfo(token=chunk, normalized_word=normalized))
    return result
```

`PUNCT_ONLY_RE` already uses `\w` which matches Latin letters, so it works for both languages.

Update `parse_progress()` and `split_sentences()` call sites to pass `language`.

### 2.4 Meanings / AI generation

In `app/meanings.py`, the `codex exec` prompt presumably says "Hebrew". Make it language-aware:

```python
LANGUAGE_PROMPTS = {
    "hebrew": "You are a Hebrew tutor. Explain the meaning of the Hebrew word '{word}' in English...",
    "latin": "You are a Latin tutor. Explain the meaning of the Latin word '{word}' in English...",
}

async def generate_meaning(word: str, context: str | None, language: str = "hebrew") -> str:
    prompt_template = LANGUAGE_PROMPTS[language]
    ...
```

(Read `app/meanings.py` before implementing to match the existing subprocess pattern exactly.)

### 2.5 `_sync_srs_card` and `ensure_srs_cards_for_unknown_words`

Both functions need `language` parameter added. All internal SQL includes `language = ?`.

### 2.6 `resolve_srs_display_words`

For Hebrew, this scans `text_sentences` to find a nikkud version of a normalized word. For Latin, this function is a no-op: `display_word = normalized_word`. Add a guard:

```python
def resolve_srs_display_words(conn, normalized_words: list[str], language: str) -> dict[str, str]:
    if language == "latin":
        return {w: w for w in normalized_words}
    # existing Hebrew logic unchanged
    ...
```

### 2.7 Validation gate

- `make test` — 55 tests pass (all use default `language='hebrew'`)
- Add new tests in `tests/test_api.py`:
  - POST text with `language='latin'`, verify it's stored and returned
  - GET texts?language=latin returns only Latin texts, ?language=hebrew returns only Hebrew texts
  - PUT word state with language=latin, verify it doesn't appear in language=hebrew words list
  - SRS session with language=latin is independent of language=hebrew session
  - Progress/history with language=latin returns separate buckets

---

## Phase 3: Frontend — Language State & Switcher

### 3.1 State changes

```javascript
const state = {
  // ... existing fields ...
  currentLanguage: "hebrew",  // NEW: "hebrew" | "latin"
  // Remove: activeView (legacy, confirmed dead)
};
```

Persist `currentLanguage` in `localStorage` like `active_user_id`. On load, read from storage (default `"hebrew"`).

### 3.2 Language switcher UI

In `index.html`, add to the header (between logo and nav buttons):

```html
<div id="language-switcher" class="language-switcher" aria-label="Language">
  <button class="lang-btn active" data-lang="hebrew">Hebrew</button>
  <button class="lang-btn" data-lang="latin">Latin</button>
</div>
```

Only show when logged in (add `hidden` class, remove on login like nav buttons).

### 3.3 Language switching logic

```javascript
function handleLanguageSwitch(lang) {
  if (lang === state.currentLanguage) return;
  state.currentLanguage = lang;
  localStorage.setItem("current_language", lang);
  updateLanguageSwitcher();
  updateDirectionAttributes();
  // Reload everything for the new language
  void loadTexts();
  if (state.currentView === "srs") void loadSrsSession();
  if (state.currentView === "progress") void loadProgressData();
}

function updateLanguageSwitcher() {
  document.querySelectorAll(".lang-btn").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.lang === state.currentLanguage);
  });
}
```

Wire `click` event on `.lang-btn` buttons. When user logs out, reset `currentLanguage` to `"hebrew"` (or persist across sessions — TBD, simpler to persist).

### 3.4 Direction attributes

```javascript
const LANG_ATTRS = {
  hebrew: { dir: "rtl", lang: "he" },
  latin:  { dir: "ltr", lang: "la" },
};

function updateDirectionAttributes() {
  const attrs = LANG_ATTRS[state.currentLanguage];
  const sentence = document.getElementById("reader-sentence");
  const srsWord = document.getElementById("srs-front-word");
  sentence.setAttribute("dir", attrs.dir);
  sentence.setAttribute("lang", attrs.lang);
  srsWord.setAttribute("dir", attrs.dir);
  srsWord.setAttribute("lang", attrs.lang);
}
```

Call `updateDirectionAttributes()` on language switch and on initial page load.

Remove the hardcoded `lang="he" dir="rtl"` from `index.html` for those two elements (replace with `lang="he" dir="rtl"` as the initial default, then let JS update on load).

### 3.5 Thread `currentLanguage` through API calls

Every `ApiClient` method that constructs a URL needs to include language. Add a helper:

```javascript
class ApiClient {
  // Add language param helper
  _langParam(lang) {
    return `language=${encodeURIComponent(lang)}`;
  }

  async getTexts(userId, language) {
    return this._get(`/v1/users/${userId}/texts?${this._langParam(language)}`);
  }

  async getSrsSession(userId, language, timezoneOffsetMinutes) {
    return this._get(`/v1/users/${userId}/srs/session?${this._langParam(language)}&timezone_offset_minutes=${timezoneOffsetMinutes}`);
  }
  // ... etc for all methods
}
```

Pass `state.currentLanguage` at every call site.

### 3.6 Text creation form

The "Add Text" form must include language context. Since the form is shown while the user has a language selected, just send `language: state.currentLanguage` in the POST body. No UI change needed (the switcher already sets the context).

### 3.7 Validation gate

- Switch to Latin → library shows empty (no Latin texts yet)
- Add a Latin text → appears in Latin library, not Hebrew
- Switch back to Hebrew → original texts reappear
- SRS in Latin is independent of Hebrew SRS
- Progress graph for Latin starts empty

---

## Phase 4: CSS Changes

### 4.1 Remove hardcoded RTL

```css
/* BEFORE */
.sentence {
    direction: rtl;
    text-align: right;
    unicode-bidi: bidi-override;
}
.sentence-word {
    direction: rtl;
}

/* AFTER — direction set by dir attribute on element */
.sentence[dir="rtl"] {
    text-align: right;
    unicode-bidi: bidi-override;
}
.sentence[dir="ltr"] {
    text-align: left;
}
/* direction itself comes from the dir HTML attribute — no explicit CSS needed */
```

### 4.2 Language switcher styles

```css
.language-switcher {
    display: none;           /* hidden until logged in */
    gap: 2px;
    background: var(--surface-raised);
    border-radius: 6px;
    padding: 2px;
}
.language-switcher.visible { display: flex; }

.lang-btn {
    padding: 4px 12px;
    border: none;
    border-radius: 4px;
    background: transparent;
    color: var(--text-muted);
    cursor: pointer;
    font-size: 13px;
    transition: all 0.15s;
}
.lang-btn.active {
    background: var(--surface);
    color: var(--text-primary);
    font-weight: 500;
}
.lang-btn:hover:not(.active) {
    color: var(--text-secondary);
}
```

### 4.3 SRS card direction

The SRS front word currently has `lang="he" dir="rtl"` hardcoded. Remove the hardcoded attributes from HTML; `updateDirectionAttributes()` handles it (Phase 3.4).

```css
/* SRS front word: inherits dir from element attribute, so typography works for both */
.srs-front-word[dir="rtl"] {
    font-family: var(--font-hebrew);
}
.srs-front-word[dir="ltr"] {
    font-family: var(--font-latin, Georgia, serif);   /* elegant serif for Latin */
    letter-spacing: 0.02em;
}
```

### 4.4 Reader word direction

When displaying word details (the inline side panel), the selected word is shown in Hebrew (RTL). For Latin, remove RTL styling from the word display span. Use a data-attribute:

```html
<span id="selected-word-display" dir="rtl" lang="he"></span>
```

→ Update via JS alongside `updateDirectionAttributes()`.

---

## Phase 5: Sample Latin Texts

Add a seed script `scripts/seed_latin_texts.py`. Run it manually after setup to populate a user's Latin library. Use public domain classical texts (Project Gutenberg).

### Suggested texts (short excerpts, varied difficulty)

**1. Caesar — De Bello Gallico I.1 (classic beginner text)**
```
Gallia est omnis divisa in partes tres, quarum unam incolunt Belgae, aliam Aquitani, tertiam qui ipsorum lingua Celtae, nostra Galli appellantur.
Hi omnes lingua, institutis, legibus inter se differunt.
Gallos ab Aquitanis Garumna flumen, a Belgis Matrona et Sequana dividit.
```

**2. Cicero — Catiline I.1 (oratory)**
```
Quo usque tandem abutere, Catilina, patientia nostra?
Quam diu etiam furor iste tuus nos eludet?
Quem ad finem sese effrenata iactabit audacia?
```

**3. Phaedrus — Fable I.1 (simple narrative)**
```
Ad rivum eundem lupus et agnus venerant, siti compulsi.
Superior stabat lupus, longeque inferior agnus.
Tunc fauce improba latro incitatus iurgii causam intulit.
```

**4. Vulgate — John 1:1-3 (familiar content)**
```
In principio erat Verbum, et Verbum erat apud Deum, et Deus erat Verbum.
Hoc erat in principio apud Deum.
Omnia per ipsum facta sunt, et sine ipso factum est nihil quod factum est.
```

**Seed script structure:**
```python
#!/usr/bin/env python3
"""
Usage: python scripts/seed_latin_texts.py <user_id>
Seeds the given user's account with sample Latin texts.
"""
import sys, httpx

TEXTS = [
    {"title": "Caesar — De Bello Gallico I.1", "language": "latin", "content": "..."},
    {"title": "Cicero — In Catilinam I.1",     "language": "latin", "content": "..."},
    {"title": "Phaedrus — Lupus et Agnus",     "language": "latin", "content": "..."},
    {"title": "Vulgate — Ioannes 1:1-3",       "language": "latin", "content": "..."},
]

BASE = "http://127.0.0.1:8000"

def seed(user_id: str):
    for text in TEXTS:
        r = httpx.post(f"{BASE}/v1/users/{user_id}/texts", json=text)
        r.raise_for_status()
        print(f"Seeded: {text['title']}")

if __name__ == "__main__":
    seed(sys.argv[1])
```

---

## Phase 6: Visual Tests

Extend `tests/visual_user_stories.py` with language-switching stories:

1. **User switches to Latin** — switcher buttons visible, clicking Latin highlights it
2. **Latin library shows correct texts** — Caesar/Cicero/etc. appear
3. **Latin reader is LTR** — sentence has `dir="ltr"` attribute, text flows left
4. **Latin SRS card is LTR** — front word has `dir="ltr"`
5. **Switch back to Hebrew** — Hebrew texts reappear, reader reverts to RTL
6. **Progress page per language** — Latin progress shows separate (initially empty) chart
7. **Language persists on reload** — set to Latin, reload page, still Latin

Each story: navigate, screenshot, assert DOM attributes where possible.

---

## Implementation Phases Summary

```
Phase 0  Refactoring    Remove activeView, add app/languages.py
Phase 1  DB Schema      Migration: add language column, recreate 3 tables
Phase 2  Backend        Thread language through all routes, tokenizer, meanings
Phase 3  Frontend       State, switcher UI, direction attributes, API calls
Phase 4  CSS            Remove hardcoded RTL, add lang-btn styles
Phase 5  Sample content Seed script + 4 Latin texts
Phase 6  Tests          New API tests, new visual stories
```

**Gate between each phase: `make test` (55 tests) must pass before starting the next.**

---

## Key Risks & Mitigations

| Risk | Mitigation |
|---|---|
| SQLite table recreation loses data | Run migration in a transaction; test on a copy of DB first |
| Stale response guard keys need `language` included | Key on `${key}_${language}` or reset on language switch |
| Meanings prompt produces wrong-language output | Explicitly test Latin meaning generation |
| CSS `direction` attribute vs property cascade order | Use `[dir]` attribute selectors, not class overrides |
| SRS daily cap shared between languages | The `language` PK on `srs_daily_new_counts` separates caps correctly |

---

## Files Changed

| File | Change type |
|---|---|
| `app/languages.py` | NEW — constants and validate_language() |
| `app/db.py` | Migration: _migrate(), _run_language_migration() |
| `app/models.py` | Add language field to TextCreateRequest, SrsReviewRequest, SrsSessionAddNewRequest, SrsCardResponse, WordStateResponse |
| `app/tokenizer.py` | Add language param to normalize_token() and tokenize_eligible() |
| `app/meanings.py` | Language-aware prompt dispatch |
| `app/main.py` | Thread language through all routes, update parse_progress(), resolve_srs_display_words(), _sync_srs_card(), ensure_srs_cards_for_unknown_words() |
| `app/static/index.html` | Language switcher markup, remove hardcoded dir/lang attrs from sentence/SRS word |
| `app/static/app.js` | currentLanguage state, handleLanguageSwitch(), updateDirectionAttributes(), ApiClient method signatures, remove activeView |
| `app/static/styles.css` | dir-attribute selectors, lang-btn styles, SRS font per direction |
| `scripts/seed_latin_texts.py` | NEW — seed script |
| `tests/test_api.py` | New language-scoped tests |
| `tests/visual_user_stories.py` | New language-switch visual stories |
