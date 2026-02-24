# Hebrew Reader Word-Bubble Ordering Spec

## Problem
Inline word bubbles in Reader must follow Hebrew visual flow so sentence tokens appear right-to-left in the same semantic order as the source sentence.

## Scope
- Desktop Reader sentence surface (`#reader-sentence`) and inline token controls (`.sentence-word`).
- Hebrew and mixed Hebrew/punctuation sentence rendering behavior.

## Rendering Contract
1. Reader sentence container must explicitly enforce RTL text flow.
2. Token bubbles must inherit RTL flow and isolate bidi context so punctuation or Latin fragments do not reorder nearby Hebrew tokens.
3. DOM token order remains source order; visual order is produced by RTL layout, not data reversal.

## Validation Plan
1. Static contract checks
- `index.html` contains `lang="he" dir="rtl"` on `#reader-sentence`.
- `styles.css` sets sentence direction/text alignment and bidi behavior for sentence + word bubbles.

2. Browser behavior checks (Playwright)
- Create a short 3-word Hebrew sentence.
- Open in Reader and ensure `.sentence-word` bubbles render.
- Assert computed `direction` for `#reader-sentence` is `rtl`.
- Assert first three bubble x-centers are strictly descending from DOM index 0->2 (rightmost to leftmost).

## Completion Criteria
- Static + browser checks pass in CI.
- Regressions in RTL ordering are caught by automated tests.

## Implementation Status
- [x] Add explicit RTL contract to reader sentence markup and CSS.
- [x] Add bidi isolation for token bubble controls.
- [x] Add Playwright regression test for RTL bubble geometry ordering.
- [ ] Add manual desktop QA screenshot pass confirming ordering in Chromium/Firefox/WebKit.
