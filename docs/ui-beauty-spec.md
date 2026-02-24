# Desktop UI Beauty Spec (2026 Modern-Blue)

## Objective
Deliver a desktop-first UI that feels modern, clear, and premium while preserving fast reading workflows and Hebrew RTL correctness.

## Scope
- In scope: desktop and large-laptop viewports (>=1100px) as the primary layout target.
- Secondary support: tablet and narrow windows with graceful collapse.
- Out of scope: native mobile-first redesign.

## Visual Direction
- Color language: cool modern blue palette with high-contrast text and soft glass surfaces.
- Typography: keep Space Grotesk + Noto Sans Hebrew pairing for readable Hebrew/English mixed UI.
- Depth: layered cards, subtle gradients, and restrained shadows (avoid flat default look).
- Motion: keep existing modal and interaction transitions; ensure they remain purposeful and not distracting.

## Layout Contract
1. Desktop shell uses a multi-column composition with dedicated areas for users, texts, reader, and words.
2. Reader remains visually dominant and keeps explicit Hebrew RTL contract (`lang="he" dir="rtl"` + bidi-safe token bubbles).
3. No horizontal overflow in reader sentence area and modal surface remains within viewport bounds.

## Accessibility + UX Guardrails
- Preserve keyboard tab semantics and `aria-selected` updates for top-level view navigation.
- Keep focus-return behavior on modal close (Escape, backdrop, close button).
- Preserve status and error messaging contrast.

## Execution Plan
1. Phase 1: Foundation restyle (palette, elevation, desktop grid shell, modern-blue controls).
2. Phase 2: Independent design review + refinement sweep (typography hierarchy, spacing rhythm, contrast, button/input polish).
3. Phase 3: Visual QA refresh screenshots, verify desktop browser matrix still passes, and attach explicit manual reviewer notes.

## Completion Criteria
- Phase 1 CSS/HTML shipped without regressions in frontend/browser tests.
- Phase 2 refinement pass is reflected in shipped HTML/CSS and reviewed against this spec.
- Visual QA screenshot set regenerated to reflect new design language.
- Desktop browser QA report remains PASS for Chromium/Firefox/WebKit and includes reviewer-authored manual evidence notes.
