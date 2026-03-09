# Unique Word Estimate Calculation

## Overview

The "Estimated Unique Words" feature estimates the percentage of words in a vocabulary that represent distinct concepts, accounting for Hebrew prefix attachments. Many Hebrew words appear multiple times in a corpus with different prefixes attached (e.g., בית, הבית, לבית all mean "house" with different grammatical particles).

## Calculation Method

### Dataset
- **Source**: Keegan's Hebrew wordbank in the hreader database
- **Date Calculated**: 2026-03-09
- **Total Unique Words**: 881

### Prefix Stripping Strategy
We use a simple single-prefix stripping approach that removes common Hebrew prefixes:
- `ו` (and)
- `ב` (in/with/on)
- `ל` (to/for)
- `ש` (that)
- `כ` (like/as)
- `ה` (the)

**Note**: We do NOT handle prefix stacking (e.g., וכה = and+like+the). This is a simplification that can be enhanced in future recalculations.

### Deduplication Process
1. For each word in the wordbank, strip each prefix in order
2. Once a prefix is stripped, stop and use that as the base form
3. Count how many unique base forms exist
4. Calculate: `unique_percentage = (unique_base_forms / total_words) * 100`

### Results
- **Unique Base Words**: 714
- **Total Words**: 881
- **Unique Percentage**: **81.04%** (0.8104)

This means ~19% of words are variants (same root with different prefixes).

## Examples of Duplicate Clusters

```
אל (to): אל, ושאל, לשאל, שאל
בית (house): בבית, הבית, לבית
דה (field): בשדה, לשדה
היא (she/is): היא, שהיא
זה (this): הזה, זה, כזה, שזה
```

## Implementation

### Frontend
- **File**: `app/static/app.js`
- **Constant**: `UNIQUE_WORD_ESTIMATE_PERCENT = 0.8104`
- **Feature**: Toggle checkbox on the Progress view to switch between "Known Words" and "Known Words (Unique Est.)"
- **Calculation**: `unique_known = known_words * UNIQUE_WORD_ESTIMATE_PERCENT`

### Backend
- **File**: `app/main.py`
- **Constant**: `UNIQUE_WORD_ESTIMATE_PERCENT = 0.8104`
- **Documentation**: Comment block explaining the calculation method

## How to Recalculate

To recalculate this percentage with updated data:

```bash
# Run the calculation script with the production database
python << 'EOF'
import sqlite3
from pathlib import Path

db_path = Path("data/hreader.db")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

rows = conn.execute(
    "SELECT DISTINCT normalized_word FROM user_words ORDER BY normalized_word"
).fetchall()

words = [row["normalized_word"] for row in rows]
PREFIXES = ['ו', 'ב', 'ל', 'ש', 'כ', 'ה']

def strip_prefixes(word):
    for prefix in PREFIXES:
        if word.startswith(prefix) and len(word) > len(prefix):
            word = word[len(prefix):]
    return word

base_forms = {}
for word in words:
    base = strip_prefixes(word)
    if base not in base_forms:
        base_forms[base] = []
    base_forms[base].append(word)

unique_percentage = (len(base_forms) / len(words)) * 100
print(f"Unique percentage: {unique_percentage:.2f}%")
print(f"Decimal: {unique_percentage / 100:.4f}")

conn.close()
EOF
```

Then update:
1. `UNIQUE_WORD_ESTIMATE_PERCENT` in `app/main.py`
2. `UNIQUE_WORD_ESTIMATE_PERCENT` in `app/static/app.js`
3. The calculation date and results in this document

## Future Enhancements

1. **Prefix Stacking**: Handle combinations like `וכה` (and+like+the)
2. **Linguistic Root Analysis**: Use actual Hebrew 3-letter roots (שורש) instead of prefix stripping
3. **Per-Text Analysis**: Calculate unique percentages per text for more granular estimates
4. **Automatic Recalculation**: Add endpoint to recalculate the estimate on-demand or scheduled
5. **Validation**: Cross-validate with known Hebrew corpora

## Limitations

- Single prefix stripping only (no stacking)
- String matching (no linguistic analysis)
- Based on one user's vocabulary (will generalize over time)
- Does not account for spelling variations or typos
