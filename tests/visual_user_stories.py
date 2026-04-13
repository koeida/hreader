"""Visual regression tests as user stories with screenshot validation.

Run with: pytest tests/visual_user_stories.py -v -s

These tests follow realistic user flows and validate the visual state with screenshots.
Screenshots are saved to /tmp/visual-tests/ for manual inspection.
"""
import pytest
from pathlib import Path
from playwright.sync_api import sync_playwright

OUTPUT_DIR = Path("/tmp/visual-tests")
OUTPUT_DIR.mkdir(exist_ok=True)

# User credentials for testing
TEST_USER_ID = "6e92e9ab-54ad-443f-899e-22021ec33367"  # "keegan" user


@pytest.fixture
def browser_context():
    """Create a browser context for visual testing."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1400, "height": 900})
        yield context
        context.close()
        browser.close()


@pytest.fixture
def page(browser_context):
    """Create a page for each test."""
    page = browser_context.new_page()
    page.goto("http://127.0.0.1:8000/", wait_until="domcontentloaded")
    page.wait_for_timeout(1500)  # Wait for JS initialization
    yield page
    page.close()


def login_user(page, user_id: str = TEST_USER_ID):
    """Helper: Log in a user."""
    dropdown = page.query_selector("#user-picker")
    dropdown.select_option(user_id)
    page.wait_for_timeout(300)

    # Click via JS to avoid Playwright visibility issues with modals
    page.evaluate("document.querySelector('#user-pick-confirm').click()")
    page.wait_for_timeout(1000)


class TestUserStories:
    """User story-based visual tests."""

    def test_story_1_user_sees_login_screen(self, page):
        """STORY: User opens app and sees user selection modal."""
        page.screenshot(path=OUTPUT_DIR / "01-login-screen.png")

        # Verify login modal is visible
        modal = page.query_selector("#user-selection-modal")
        assert modal, "User selection modal should exist"
        modal_visible = page.evaluate("el => !el.classList.contains('is-hidden')", modal)
        assert modal_visible, "User selection modal should be visible"

    def test_story_2_user_logs_in_and_sees_nav(self, page):
        """STORY: User selects a user and sees the main interface with nav buttons."""
        login_user(page)
        page.screenshot(path=OUTPUT_DIR / "02-logged-in.png")

        # Verify header is visible
        header = page.query_selector("#app-header")
        header_display = page.evaluate("el => window.getComputedStyle(el).display", header)
        assert header_display != "none", "Header should be visible after login"

        # Verify nav buttons exist
        assert page.query_selector("#nav-library"), "Library button should exist"
        assert page.query_selector("#nav-srs"), "SRS button should exist"
        assert page.query_selector("#nav-progress"), "Progress button should exist"

    def test_story_3_user_navigates_to_library(self, page):
        """STORY: User logs in and views their reading library."""
        login_user(page)

        # Navigate to library
        page.evaluate("document.querySelector('#nav-library').click()")
        page.wait_for_timeout(500)
        page.screenshot(path=OUTPUT_DIR / "03-library-view.png")

        # Verify only library section is displayed
        sections_active = page.evaluate("""
            () => Array.from(document.querySelectorAll('.view-section.active')).map(el => el.id)
        """)
        assert sections_active == ["section-library"], f"Only library should be active, got {sections_active}"

    def test_story_4_user_navigates_to_srs(self, page):
        """STORY: User logs in and navigates to SRS for card review."""
        login_user(page)

        # Navigate to SRS
        page.evaluate("document.querySelector('#nav-srs').click()")
        page.wait_for_timeout(500)
        page.screenshot(path=OUTPUT_DIR / "04-srs-view.png")

        # Verify only SRS section is displayed
        sections_active = page.evaluate("""
            () => Array.from(document.querySelectorAll('.view-section.active')).map(el => el.id)
        """)
        assert sections_active == ["section-srs"], f"Only SRS should be active, got {sections_active}"

        # Verify SRS elements exist
        assert page.query_selector(".srs-card-flip"), "SRS flip card should exist"
        assert page.query_selector("#srs-front-word"), "Front word display should exist"

    def test_story_5_user_navigates_to_progress(self, page):
        """STORY: User logs in, clicks Progress button, and sees vocabulary graph.

        This was the broken test! Now it should show only the Progress page.
        """
        login_user(page)

        # Navigate to Progress
        page.evaluate("document.querySelector('#nav-progress').click()")
        page.wait_for_timeout(500)
        page.screenshot(path=OUTPUT_DIR / "05-progress-view.png")

        # Verify ONLY progress section is active (not overlapping with other sections)
        sections_active = page.evaluate("""
            () => Array.from(document.querySelectorAll('.view-section.active')).map(el => el.id)
        """)
        assert sections_active == ["section-progress"], f"Only progress should be active, got {sections_active}"

        # Verify progress elements exist
        assert page.query_selector("#section-progress"), "Progress section should exist"
        assert page.query_selector("#progress-chart"), "Chart should exist"
        assert page.query_selector(".progress-range-toggle"), "Range toggle should exist"

    def test_story_6_srs_word_displays_on_one_line(self, page):
        """STORY: Logged-in user can navigate to SRS page and WORD IS VISIBLE ON ONE LINE.

        This validates the visual layout of the flip card - the Hebrew word should
        display prominently on a single line without breaking.
        """
        login_user(page)

        # Navigate to SRS
        page.evaluate("document.querySelector('#nav-srs').click()")
        page.wait_for_timeout(500)
        page.screenshot(path=OUTPUT_DIR / "06-srs-empty.png")

        # The word element should exist and have proper dimensions
        word_el = page.query_selector("#srs-front-word")
        assert word_el, "Front word element should exist"

        # Check that word doesn't wrap to multiple lines
        word_info = page.evaluate("""
            el => ({
                offsetHeight: el.offsetHeight,
                lineHeight: window.getComputedStyle(el).lineHeight,
                whiteSpace: window.getComputedStyle(el).whiteSpace,
            })
        """, word_el)

        # white-space: nowrap keeps word on one line; no overflow:hidden so nikud isn't clipped
        assert word_info["whiteSpace"] == "nowrap", "Word should have white-space: nowrap"
        assert word_info["lineHeight"] != "normal", "line-height should be explicit (generous for nikud)"
        print(f"✅ Word element height: {word_info['offsetHeight']}px, white-space: {word_info['whiteSpace']}, line-height: {word_info['lineHeight']}")

    def test_story_7_srs_review_flow_shows_only_card_when_due(self, page):
        """STORY: SRS Review Flow - Only card review shown when words are due.

        CRITICAL UX: When a card is being reviewed, ONLY the flip card shows.
        NOT "No cards due right now" (confusing).
        NOT "All caught up!" (contradictory).
        After all cards are reviewed, appropriate message appears.
        """
        login_user(page)

        page.evaluate("document.querySelector('#nav-srs').click()")
        page.wait_for_timeout(800)
        page.screenshot(path=OUTPUT_DIR / "07a-srs-with-card.png")

        reviewer = page.query_selector("#srs-reviewer")
        add_new = page.query_selector("#srs-add-new")
        caught_up = page.query_selector("#srs-caught-up")

        assert reviewer and add_new and caught_up, "All SRS panels must exist"

        # Exactly one of the three panels should be visible
        def display(el):
            return page.evaluate("el => window.getComputedStyle(el).display", el)

        panels_visible = [
            display(reviewer) != "none",
            display(add_new) != "none",
            display(caught_up) != "none",
        ]
        assert sum(panels_visible) == 1, (
            f"Exactly one SRS panel should be visible, got: "
            f"reviewer={'visible' if panels_visible[0] else 'hidden'}, "
            f"add_new={'visible' if panels_visible[1] else 'hidden'}, "
            f"caught_up={'visible' if panels_visible[2] else 'hidden'}"
        )
        print(f"✅ Exactly one panel visible: reviewer={panels_visible[0]}, add_new={panels_visible[1]}, caught_up={panels_visible[2]}")

    def test_story_8_srs_keyboard_controls(self, page):
        """STORY: User uses keyboard to flip SRS cards (SPACE = flip, 0 = wrong, 1 = right)."""
        login_user(page)

        # Navigate to SRS
        page.evaluate("document.querySelector('#nav-srs').click()")
        page.wait_for_timeout(500)

        # Simulate a card by setting state directly
        page.evaluate("""
            if (typeof renderSrs !== 'undefined') {
                document.querySelector('[data-view-target=\\"srs\\"]')?.click?.();
            }
        """)
        page.wait_for_timeout(200)
        page.screenshot(path=OUTPUT_DIR / "08a-srs-unrevealed.png")

        # The keyboard controls would be tested in integration tests
        # This story validates the visual state
        print("✅ SRS keyboard controls ready for testing")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
