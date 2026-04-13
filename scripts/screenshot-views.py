#!/usr/bin/env python3
"""Screenshot each view for visual verification."""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

VIEWS = ["library", "srs", "progress"]
OUTPUT_DIR = Path("/tmp/view-screenshots")
OUTPUT_DIR.mkdir(exist_ok=True)

def screenshot_view(view_name: str, headless: bool = True):
    """Screenshot a specific view."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page(viewport={"width": 1400, "height": 900})

        try:
            print(f"📸 Screenshotting {view_name}...")
            page.goto("http://127.0.0.1:8000/", wait_until="domcontentloaded")
            page.wait_for_timeout(1500)  # Wait for JS init

            # Try to navigate to view
            nav_selector = f"[data-view-target='{view_name}']"
            nav_btn = page.query_selector(nav_selector)

            if nav_btn:
                print(f"  Found nav button via {nav_selector}")
                # Use Playwright click instead of JS
                try:
                    nav_btn.click(timeout=1000, force=True, no_wait_after=True)
                except:
                    pass
                page.wait_for_timeout(800)
            else:
                print(f"  ⚠️  Nav button not found, trying text search...")
                # Find by text and click directly
                all_buttons = page.query_selector_all("button")
                for btn in all_buttons:
                    if view_name.lower() in btn.text_content().lower():
                        btn.click(force=True, no_wait_after=True)
                        page.wait_for_timeout(800)
                        break

            # Verify we're on the right view
            current_view = page.evaluate("document.querySelector('.view-section.active')?.id || 'unknown'")
            print(f"  Active section: {current_view}")

            # Take screenshot
            output_path = OUTPUT_DIR / f"{view_name}.png"
            page.screenshot(path=str(output_path), full_page=False)
            print(f"  ✅ Saved to {output_path}")

            return output_path

        except Exception as e:
            print(f"  ❌ Error: {e}")
            return None
        finally:
            browser.close()

if __name__ == "__main__":
    headless = "--headless" in sys.argv or "-h" in sys.argv

    print(f"📷 Screenshotting all views to {OUTPUT_DIR}\n")

    results = {}
    for view in VIEWS:
        results[view] = screenshot_view(view, headless=headless)

    print(f"\n✨ Done!")
    for view, path in results.items():
        status = "✅" if path and path.exists() else "❌"
        print(f"{status} {view}: {path}")
