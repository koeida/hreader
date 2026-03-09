# UI Redesign Specification

## Status: Implementation Complete (Gates 1-3) - Testing Phase

### Completion Summary
- **Gate 1 (Navigation & User Selection)**: ✅ COMPLETE
  - Persistent header with nav buttons
  - User selection modal (non-blocking overlay)
  - Login/logout flow implemented
  - State management (`currentView`, `isLoggedIn`)

- **Gate 2 (Library Grid)**: ✅ COMPLETE
  - CSS Grid layout (3/4 columns responsive)
  - Color-coded text cards (gradient based on highest %)
  - Word count and statistics display
  - Empty state messaging

- **Gate 3 (Full-Screen Reader & Exit)**: ✅ COMPLETE
  - Reader shows full-screen when text selected
  - Header hides in reader mode
  - Exit button returns to library
  - Position/state restoration on reload

### Test Status
- **47 tests passing** (all backend + frontend structure tests)
- **7 browser tests failing** (UI interaction tests - need updating for new flow)
  - All failures due to expected UI changes
  - Core functionality verified via smoke test ✅

### Known Issues / TODO
1. **Edit/Delete text card buttons** - handlers stubbed out, need implementation
2. **Browser test updates** - old tests expect previous UI flow
3. **Rename text functionality** - needs inline form implementation in grid
4. **Delete confirmation** - needs modal or inline confirmation

### Next Steps
1. Implement Edit/Delete handlers for text cards
2. Fix/update browser tests for new UI
3. Polish hover states and animations
4. User acceptance testing
5. Deploy to production

---

## Overview
Redesign the hreader UI to use a persistent navigation structure with full-screen views for Library (text selector) and Reader modes. Three gated implementation phases.

---

## Gate 1: Navigation & User Selection

### Technical Requirements

**Navigation Structure:**
- Create persistent header with:
  - Left side: "Library" and "SRS" navigation buttons
  - Right side: Logout link (visible only when logged in)
  - Height: `60px` (recommended)
  - Always visible except in full-screen Reader mode (see Gate 3)

**User Selection Modal:**
- Show only when `sessionStorage` has no `user_id` or after explicit logout
- Display as centered modal/overlay on blank page
- Contains dropdown of existing users (fetch from `GET /v1/users`)
- Clicking a user logs in and dismisses modal
- After login, modal never appears until logout

**State Management:**
- Add to `state` object:
  - `state.currentView` — "library" | "srs" | "reader" (controls visibility)
  - `state.isLoggedIn` — boolean
- Update session management to set/clear `isLoggedIn` on auth flow
- Logout handler: clear `user_id`, set `isLoggedIn = false`, show modal

**HTML Changes:**
- Wrap existing content in container with id `main-content`
- Create new persistent `<header id="app-header">` with nav buttons and logout link
- Create new modal div for user selection: `<div id="user-selection-modal">`
- Adjust main content to account for header height

**CSS Changes:**
- `#app-header`: position sticky/fixed, flex layout, z-index above content
- `#main-content`: Add top padding to account for header
- `#user-selection-modal`: position fixed, center on screen, z-index above header
- `.nav-button`, `.logout-link`: Hover states and active state

**JavaScript Changes:**
- `renderUserSelection()` — Fetch users, populate dropdown, attach click handlers
- `showUserSelection()` / `hideUserSelection()` — Toggle modal visibility
- `switchView(viewName)` — Update `state.currentView`, show/hide sections, update active nav button
- `handleNavigation(view)` — Click handler for nav buttons
- `handleLogout()` — Clear session, show user selection, reset UI

### Acceptance Criteria
- [ ] Header visible and persistent on all views (except Reader)
- [ ] User selection modal shows when no user logged in
- [ ] Clicking user logs in and dismisses modal
- [ ] Nav buttons switch between Library and SRS views
- [ ] Logout link appears in header when logged in
- [ ] Clicking logout shows user selection modal
- [ ] No visual glitches or layout shifts

---

## Gate 2: Library Grid Redesign

### Technical Requirements

**Grid Layout:**
- Replace existing text list with CSS Grid
- Responsive columns:
  - Desktop (≥1200px): 4 columns
  - Tablet (768px-1199px): 3 columns
  - Small (≥0px): Use 3 as fallback
- Gap: `24px` (spacious)
- Padding: `24px` on all sides
- Full-screen within `#main-content` minus header

**Widget Structure:**
Each text card contains:
```
┌─────────────────────────────┐
│  Title (large, bold)        │
│  Word Count: 1,234          │
│  Known: 85% | Stage 4+: 92% │
│  [Edit] [Delete] (on hover) │
└─────────────────────────────┘
```

**Widget Data & Display:**
- Fetch text metadata: `id`, `title`, `original_filename`, `created_at`
- Calculate stats from API:
  - Word count (from text table or compute on backend if needed)
  - Percentage known: `known_count / total_unique_words` (call new endpoint or derive from existing)
  - Percentage stage 4+: Count SRS cards with `stage_index >= 4` / total unique words
  - **Use highest percentage (stage 4+) for color coding**
- Title: Font size ~24px, bold, dominates the card

**Color Coding:**
- Compute highest percentage from text stats
- Apply background color with gradient transition:
  - `0-69%`: Shade of red (`#fee2e2` to `#dc2626` range)
  - `70-79%`: Shade of yellow/amber (`#fef3c7` to `#f59e0b` range)
  - `80-89%`: Shade of yellow/green (`#fef3c7` to `#84cc16` range)
  - `90-100%`: Shade of green (`#dcfce7` to `#22c55e` range)
- Use CSS `background` or `background-color` with calculated RGB/HSL

**Edit/Delete Buttons:**
- Positioned absolute in card top-right
- Show only on `.widget:hover`
- Small icon buttons: `16px` icons, `8px` padding
- Edit: pencil icon ✎, Delete: trash icon 🗑
- Z-index above card content

**Empty State:**
- If no texts, show centered message: "No texts yet. Create one to get started."
- Display in grid area with full-screen centering

**JavaScript Changes:**
- `renderLibraryGrid()` — Fetch texts, compute stats, render cards
- `calculateHighestPercentage(textId)` — Fetch/compute stats, return number
- `colorForPercentage(pct)` — Return background color string based on percentage
- `calculatePercentageColor(pct)` — Implement gradient logic
- Update state on text selection for reader launch (Gate 3)

**CSS Changes:**
- `#library-grid`: CSS Grid with responsive columns, gap, padding
- `.text-widget`: Card styling, position relative, background color based on data
- `.text-widget:hover .edit-delete-buttons`: Show buttons on hover
- `.text-widget__title`: Large, bold typography
- `.text-widget__stats`: Smaller font, muted color
- `.edit-icon`, `.delete-icon`: 16px, hover effects

**API Requirements:**
- Verify existing endpoint returns word count: `GET /v1/texts/{text_id}`
- If not, may need new endpoint: `GET /v1/texts/{text_id}/stats` returning:
  ```json
  {
    "total_words": 1234,
    "unique_words": 456,
    "known_count": 389,
    "stage_4_plus_count": 423
  }
  ```

### Acceptance Criteria
- [ ] Grid renders with correct responsive columns (3-4)
- [ ] Each widget displays title, word count, and stats
- [ ] Background color correctly reflects highest percentage with smooth gradient
- [ ] Edit/Delete buttons appear only on hover
- [ ] Grid is full-screen and spacious (24px gap/padding)
- [ ] Empty state displays when no texts
- [ ] No layout shifts or jank on hover

---

## Gate 3: Full-Screen Reader & Exit

### Technical Requirements

**Reader Visibility:**
- Reader should be hidden by default (display: none or visibility: hidden)
- When text selected from Library:
  1. Store selected text ID in `state.selectedTextId`
  2. Set `state.currentView = "reader"`
  3. Show reader, hide library
  4. Hide header (persistent nav disappears)
- Clicking exit returns to library

**Exit Button:**
- Positioned fixed in top-right corner
- Only visible in Reader mode
- Small button (40px square recommended)
- Label: "← Library" or just "×" with title="Exit Reader"
- Click handler: `handleReaderExit()` → Set view back to "library", show header

**State Updates:**
- `state.selectedTextId` — Track current text in reader
- `state.currentView = "reader"` — Hides header, library; shows reader
- Exit clears `selectedTextId`, sets `currentView = "library"`

**HTML Changes:**
- Wrap reader section in container: `<section id="reader-section">`
- Add exit button: `<button id="reader-exit-btn" class="reader-exit">...</button>`
- Position in reader section

**CSS Changes:**
- `#app-header`: Hide when `state.currentView === "reader"` (class `is-hidden` or display: none)
- `#reader-section`: Display: none by default, display: block when active
- Full-screen reader: width 100%, height 100vh (or calc(100vh - header-height) when header shows)
- `.reader-exit`: position fixed, top 20px, right 20px, z-index high

**JavaScript Changes:**
- `selectTextForReading(textId)` — Update state, trigger view change
- `handleReaderExit()` — Clear selected text, return to library view
- `updateViewVisibility()` — Called on `state.currentView` change:
  - Show/hide header based on view
  - Show/hide library based on view
  - Show/hide reader based on view
- Attach click handler to exit button

**Navigation Flow:**
- Library (default) → Click text widget → Reader (full-screen, header hidden)
- Reader → Click exit → Library (header visible again)

### Acceptance Criteria
- [ ] Reader hidden on page load and in Library view
- [ ] Clicking text widget launches full-screen reader
- [ ] Header hidden in Reader mode
- [ ] Exit button visible in top-right of Reader
- [ ] Clicking exit returns to Library with header visible
- [ ] No layout jank during view transitions
- [ ] Reader takes full screen (no scrollbars from header/nav)

---

## Cross-Gate Requirements

### State Management
Extend `state` object:
```javascript
{
  currentView: "library" | "srs" | "reader",
  isLoggedIn: boolean,
  selectedTextId: null | number,
  // ... existing state
}
```

### Navigation Rules
- User selection modal: Always visible when `!isLoggedIn`
- Header: Visible when `isLoggedIn && currentView !== "reader"`
- Library: Visible when `isLoggedIn && currentView === "library"`
- SRS: Visible when `isLoggedIn && currentView === "srs"` (no changes)
- Reader: Visible when `isLoggedIn && currentView === "reader"`

### Testing Plan

**Gate 1 Tests:**
- User selection appears when logged out
- User selection disappears after login
- Nav buttons switch between Library and SRS
- Logout button appears/disappears correctly
- Logout shows user selection again

**Gate 2 Tests:**
- Grid renders with correct number of columns per breakpoint
- Cards display correct title, word count, and stats
- Color gradient transitions correctly across percentage ranges
- Edit/Delete buttons appear only on hover
- Grid is responsive and spacious
- Empty state displays when no texts

**Gate 3 Tests:**
- Clicking text widget launches Reader
- Header hidden in Reader
- Exit button visible and clickable
- Exit button returns to Library
- Header reappears after exit

### File Changes Summary
- `app/static/index.html` — Add header, user selection modal, reorganize sections
- `app/static/styles.css` — Header styles, grid layout, responsive design, hover effects
- `app/static/app.js` — Navigation logic, view switching, grid rendering, exit handling
- Possibly `app/main.py` — New stats endpoint if word count not available

### Browser Compatibility
- Modern browsers (Chrome, Firefox, Safari, Edge)
- CSS Grid support required
- LocalStorage/sessionStorage for auth state

---

## Not Included (Future Work)
- Mobile responsive design (desktop only per constraints)
- Reader view improvements (handled separately)
- SRS view changes (kept as-is)
- Create new user flow (deferred)
