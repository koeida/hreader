from __future__ import annotations

import contextlib
import json
import socket
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Iterator

import pytest
import uvicorn

from app.main import create_app


def _find_free_port() -> int:
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("127.0.0.1", 0))
        sock.listen(1)
        return int(sock.getsockname()[1])


def _wait_for_health(base_url: str, timeout_seconds: float = 10.0) -> None:
    deadline = time.monotonic() + timeout_seconds
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(f"{base_url}/health", timeout=1.0) as resp:
                if resp.status == 200:
                    return
        except (OSError, urllib.error.URLError) as err:
            last_error = err
        time.sleep(0.1)
    raise RuntimeError(f"Server did not become healthy at {base_url}: {last_error}")


@pytest.fixture
def live_server(tmp_path: Path) -> Iterator[str]:
    app = create_app(db_path=str(tmp_path / "ui-browser.db"))
    port = _find_free_port()
    base_url = f"http://127.0.0.1:{port}"

    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    _wait_for_health(base_url)
    try:
        yield base_url
    finally:
        server.should_exit = True
        thread.join(timeout=10)


def test_reader_word_details_panel_select_cycle_and_reset(live_server: str, tmp_path: Path) -> None:
    playwright = pytest.importorskip("playwright.sync_api")

    with playwright.sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
        except playwright.Error as exc:
            pytest.skip(f"Playwright browser runtime unavailable: {exc}")

        # Create test user and text via API
        user_resp = urllib.request.urlopen(
            urllib.request.Request(
                f"{live_server}/v1/users",
                method="POST",
                data=json.dumps({"display_name": "Browser User"}).encode(),
                headers={"Content-Type": "application/json"},
            )
        )
        user_data = json.load(user_resp)
        user_id = user_data["user_id"]

        text_body = "שָׁלוֹם לָכֶם. אָבָא אִמָא יֶלֶד."
        text_resp = urllib.request.urlopen(
            urllib.request.Request(
                f"{live_server}/v1/users/{user_id}/texts",
                method="POST",
                data=json.dumps({"title": "Panel Behavior", "content": text_body}).encode(),
                headers={"Content-Type": "application/json"},
            )
        )
        text_data = json.load(text_resp)
        text_id = text_data["text_id"]

        context = browser.new_context(base_url=live_server)
        page = context.new_page()

        # Set user in localStorage to log in
        page.add_init_script(f"localStorage.setItem('active_user_id', '{user_id}')")
        page.goto("/", wait_until="networkidle")

        assert page.locator("#word-modal").count() == 0
        assert page.locator("#jump-sentence-form").count() == 0
        assert page.locator("text=API Base URL").count() == 0

        # Click on the text card to open reader
        page.wait_for_selector(".text-widget")
        page.click(".text-widget")
        page.click("#next-sentence")
        page.wait_for_selector(".sentence-word")

        first = page.locator(".sentence-word").first
        second = page.locator(".sentence-word").nth(1)

        first.click()
        page.wait_for_function("() => !document.getElementById('word-details-panel').classList.contains('is-hidden')")
        assert page.locator("#word-details-panel h3").count() == 0
        assert page.locator("#word-details-panel >> text=Word Details").count() == 0
        assert page.locator("#word-details-panel >> text=Status:").count() == 0
        assert page.locator("#word-details-panel >> text=Generation context").count() == 0
        assert page.locator("#mnemonic-form button[type='submit']").count() == 0
        assert page.locator("#add-meaning-form button[type='submit']").count() == 0
        page.click("#word-mnemonic-display")
        page.fill("#word-mnemonic", "abba sounds like father")
        page.locator("#word-mnemonic").press("Control+Enter")
        page.wait_for_function("() => document.getElementById('mnemonic-state').textContent.trim() === 'Saved'")
        page.click("#manual-meaning-display")
        page.fill("#manual-meaning", "father")
        page.locator("#manual-meaning").press("Control+Enter")
        page.wait_for_function("() => document.getElementById('meanings-preview').textContent.includes('father')")
        layout_contract = page.evaluate(
            """
            () => {
              const mnemonic = document.getElementById('mnemonic-form').getBoundingClientRect();
              const meaning = document.getElementById('add-meaning-form').getBoundingClientRect();
              const generate = document.getElementById('generate-meaning-form').getBoundingClientRect();
              const panel = document.getElementById('word-details-panel').getBoundingClientRect();
              const latest = document.getElementById('meanings-preview').getBoundingClientRect();
              const saved = document.getElementById('meanings-list').getBoundingClientRect();
              const fieldWidths = Array.from(document.querySelectorAll('#word-details-panel .inline-edit-display'))
                .map((field) => field.getBoundingClientRect().width);
              const verticalOffset = Math.abs(meaning.top - mnemonic.top);
              const giantGutter = meaning.left - mnemonic.right;
              const leftOffset = Math.abs(meaning.left - mnemonic.left);
              const stackedCleanly = leftOffset <= 8 && meaning.top >= mnemonic.bottom - 8;
              const balancedColumns = verticalOffset <= 16
                && generate.left >= meaning.right - 8
                && giantGutter <= panel.width * 0.08;
              const compact = panel.height <= 360
                && Math.max(...fieldWidths) <= panel.width * 0.52
                && latest.height <= 72
                && saved.height <= 96;
              return {
                ok: (stackedCleanly || balancedColumns) && compact,
                reason: `panelHeight=${panel.height}; verticalOffset=${verticalOffset}; giantGutter=${giantGutter}; leftOffset=${leftOffset}; panelWidth=${panel.width}; fields=${fieldWidths.join(',')}; latestHeight=${latest.height}; savedHeight=${saved.height}`,
              };
            }
            """
        )
        assert layout_contract["ok"] is True, layout_contract["reason"]
        screenshot_path = tmp_path / "compact-word-details-panel.png"
        page.locator("#word-details-panel").screenshot(path=str(screenshot_path))
        assert screenshot_path.stat().st_size > 0
        assert page.locator("#word-mnemonic-display").inner_text().strip() == "abba sounds like father"
        assert page.locator("#manual-meaning-display").inner_text().strip() == "father"
        assert page.evaluate("() => document.getElementById('word-details-status').textContent.trim()") == "Unseen"
        first_selected = page.evaluate("() => document.getElementById('word-details-word').textContent.trim()")

        first.click()
        page.wait_for_function("() => document.getElementById('word-details-panel').classList.contains('status-unknown')")
        first.click()
        page.wait_for_function("() => document.getElementById('word-details-panel').classList.contains('status-known')")
        first.click()
        page.wait_for_function("() => !document.getElementById('word-details-panel').classList.contains('status-unknown') && !document.getElementById('word-details-panel').classList.contains('status-known')")

        second.click()
        page.wait_for_function(
            "(word) => document.getElementById('word-details-word').textContent.trim() !== word",
            arg=first_selected,
        )
        assert page.evaluate("() => document.getElementById('word-details-status').textContent.trim()") == "Unseen"

        page.click("#prev-sentence")
        page.wait_for_function("() => document.getElementById('word-details-panel').classList.contains('is-hidden')")

        page.click("#next-sentence")
        page.wait_for_selector(".sentence-word")
        page.locator(".sentence-word").first.click()
        page.wait_for_function("() => !document.getElementById('word-details-panel').classList.contains('is-hidden')")

        # Exit reader to go back to library (hides word-details-panel)
        page.click("#reader-exit-btn")
        page.wait_for_function("() => document.getElementById('word-details-panel').classList.contains('is-hidden')")

        # Click on text card to re-enter reader
        page.wait_for_selector(".text-widget")
        page.click(".text-widget")
        page.wait_for_function("() => document.getElementById('word-details-panel').classList.contains('is-hidden')")

        context.close()
        browser.close()


def test_reader_words_stay_clickable_during_generate_request(live_server: str) -> None:
    playwright = pytest.importorskip("playwright.sync_api")

    with playwright.sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
        except playwright.Error as exc:
            pytest.skip(f"Playwright browser runtime unavailable: {exc}")

        # Create test user and text via API
        user_resp = urllib.request.urlopen(
            urllib.request.Request(
                f"{live_server}/v1/users",
                method="POST",
                data=json.dumps({"display_name": "Async User"}).encode(),
                headers={"Content-Type": "application/json"},
            )
        )
        user_data = json.load(user_resp)
        user_id = user_data["user_id"]

        text_resp = urllib.request.urlopen(
            urllib.request.Request(
                f"{live_server}/v1/users/{user_id}/texts",
                method="POST",
                data=json.dumps({"title": "Async Text", "content": "אָבָא אִמָא יֶלֶד."}).encode(),
                headers={"Content-Type": "application/json"},
            )
        )
        text_data = json.load(text_resp)
        text_id = text_data["text_id"]

        context = browser.new_context(base_url=live_server)
        page = context.new_page()

        page.route(
            "**/meanings/generate",
            lambda route: (time.sleep(0.4), route.continue_()),
        )

        # Set user in localStorage to log in
        page.add_init_script(f"localStorage.setItem('active_user_id', '{user_id}')")
        page.goto("/", wait_until="networkidle")

        # Click on the text card to open reader
        page.wait_for_selector(".text-widget")
        page.click(".text-widget")
        page.wait_for_selector(".sentence-word")

        first = page.locator(".sentence-word").first
        second = page.locator(".sentence-word").nth(1)

        first.click()
        page.click("#generate-meaning-form button[type='submit']")

        first_selected = page.evaluate("() => document.getElementById('word-details-word').textContent.trim()")
        second.click()
        page.wait_for_function(
            "(word) => document.getElementById('word-details-word').textContent.trim() !== word",
            arg=first_selected,
        )

        context.close()
        browser.close()


def test_library_featured_last_read_and_sort_switcher(live_server: str, tmp_path: Path) -> None:
    playwright = pytest.importorskip("playwright.sync_api")

    def post_json(path: str, payload: dict) -> dict:
        resp = urllib.request.urlopen(
            urllib.request.Request(
                f"{live_server}{path}",
                method="POST",
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
            )
        )
        return json.load(resp)

    def put_json(path: str, payload: dict) -> dict:
        resp = urllib.request.urlopen(
            urllib.request.Request(
                f"{live_server}{path}",
                method="PUT",
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
            )
        )
        return json.load(resp)

    def get_json(path: str) -> dict:
        with urllib.request.urlopen(f"{live_server}{path}") as resp:
            return json.load(resp)

    user_id = post_json("/v1/users", {"display_name": "Library Sort User"})["user_id"]
    old_id = post_json(f"/v1/users/{user_id}/texts", {"title": "Old Read", "content": "אָבָא אִמָא.", "language": "hebrew"})["text_id"]
    time.sleep(1.05)
    middle_id = post_json(f"/v1/users/{user_id}/texts", {"title": "Middle Continue", "content": "יֶלֶד סֵפֶר.", "language": "hebrew"})["text_id"]
    time.sleep(1.05)
    post_json(f"/v1/users/{user_id}/texts", {"title": "New Unread", "content": "שָׁלוֹם בַּיִת.", "language": "hebrew"})

    get_json(f"/v1/users/{user_id}/texts/{old_id}/sentences/0")
    put_json(f"/v1/users/{user_id}/texts/{old_id}/position", {"sentence_index": 0})
    put_json(f"/v1/users/{user_id}/words/{urllib.parse.quote('אבא')}", {"state": "known"})
    put_json(f"/v1/users/{user_id}/words/{urllib.parse.quote('אמא')}", {"state": "unknown"})
    time.sleep(1.05)
    get_json(f"/v1/users/{user_id}/texts/{middle_id}/sentences/0")
    put_json(f"/v1/users/{user_id}/texts/{middle_id}/position", {"sentence_index": 0})

    with playwright.sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
        except playwright.Error as exc:
            pytest.skip(f"Playwright browser runtime unavailable: {exc}")

        context = browser.new_context(base_url=live_server, viewport={"width": 1440, "height": 900})
        page = context.new_page()
        page.add_init_script(f"localStorage.setItem('active_user_id', '{user_id}')")
        page.goto("/", wait_until="networkidle")
        page.wait_for_selector(".text-widget--featured")

        assert page.locator(".text-widget--featured .text-widget__title").inner_text().strip() == "Middle Continue"
        assert page.locator("#library-sort-switcher [data-library-sort]").count() == 3
        assert page.locator('[data-library-sort="date-added"]').get_attribute("aria-checked") == "true"

        def list_titles() -> list[str]:
            return page.locator(".library-list .text-widget__title").all_inner_texts()

        assert list_titles() == ["New Unread", "Old Read"]

        page.click('[data-library-sort="percent-read"]')
        assert page.locator('[data-library-sort="percent-read"]').get_attribute("aria-checked") == "true"
        assert list_titles() == ["Old Read", "New Unread"]

        page.click('[data-library-sort="percent-known"]')
        assert page.locator('[data-library-sort="percent-known"]').get_attribute("aria-checked") == "true"
        assert list_titles() == ["Old Read", "New Unread"]

        screenshot_path = tmp_path / "library-featured-sort-switcher-test.png"
        page.screenshot(path=str(screenshot_path), full_page=True)
        assert screenshot_path.stat().st_size > 0

        context.close()
        browser.close()


def test_reader_sentence_enforces_rtl_word_bubble_order(live_server: str) -> None:
    playwright = pytest.importorskip("playwright.sync_api")

    with playwright.sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
        except playwright.Error as exc:
            pytest.skip(f"Playwright browser runtime unavailable: {exc}")

        # Create test user and text via API
        user_resp = urllib.request.urlopen(
            urllib.request.Request(
                f"{live_server}/v1/users",
                method="POST",
                data=json.dumps({"display_name": "RTL User"}).encode(),
                headers={"Content-Type": "application/json"},
            )
        )
        user_data = json.load(user_resp)
        user_id = user_data["user_id"]

        text_resp = urllib.request.urlopen(
            urllib.request.Request(
                f"{live_server}/v1/users/{user_id}/texts",
                method="POST",
                data=json.dumps({"title": "RTL Sentence", "content": "אָבָא אִמָא יֶלֶד."}).encode(),
                headers={"Content-Type": "application/json"},
            )
        )
        text_data = json.load(text_resp)
        text_id = text_data["text_id"]

        context = browser.new_context(base_url=live_server)
        page = context.new_page()

        # Set user in localStorage to log in
        page.add_init_script(f"localStorage.setItem('active_user_id', '{user_id}')")
        page.goto("/", wait_until="networkidle")

        # Click on the text card to open reader
        page.wait_for_selector(".text-widget")
        page.click(".text-widget")
        page.wait_for_selector(".sentence-word")

        rtl_contract = page.evaluate(
            """
            () => {
              const sentence = document.getElementById('reader-sentence');
              const style = window.getComputedStyle(sentence);
              const buttons = Array.from(sentence.querySelectorAll('.sentence-word'));
              if (buttons.length < 3) {
                return { ok: false, reason: `expected 3+ word buttons, got ${buttons.length}` };
              }
              const centers = buttons.slice(0, 3).map((btn) => {
                const rect = btn.getBoundingClientRect();
                return rect.left + rect.width / 2;
              });
              return {
                ok: style.direction === 'rtl' && centers[0] > centers[1] && centers[1] > centers[2],
                reason: `direction=${style.direction}; centers=${centers.join(',')}`,
              };
            }
            """
        )
        assert rtl_contract["ok"] is True, rtl_contract["reason"]

        context.close()
        browser.close()


def test_duplicate_words_cycle_updates_all_occurrences(live_server: str) -> None:
    playwright = pytest.importorskip("playwright.sync_api")

    with playwright.sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
        except playwright.Error as exc:
            pytest.skip(f"Playwright browser runtime unavailable: {exc}")

        # Create test user and text via API
        user_resp = urllib.request.urlopen(
            urllib.request.Request(
                f"{live_server}/v1/users",
                method="POST",
                data=json.dumps({"display_name": "Duplicate User"}).encode(),
                headers={"Content-Type": "application/json"},
            )
        )
        user_data = json.load(user_resp)
        user_id = user_data["user_id"]

        text_resp = urllib.request.urlopen(
            urllib.request.Request(
                f"{live_server}/v1/users/{user_id}/texts",
                method="POST",
                data=json.dumps({"title": "Duplicate Sentence", "content": "אָבָא אָבָא יֶלֶד."}).encode(),
                headers={"Content-Type": "application/json"},
            )
        )
        text_data = json.load(text_resp)
        text_id = text_data["text_id"]

        context = browser.new_context(base_url=live_server)
        page = context.new_page()

        # Set user in localStorage to log in
        page.add_init_script(f"localStorage.setItem('active_user_id', '{user_id}')")
        page.goto("/", wait_until="networkidle")

        # Click on the text card to open reader
        page.wait_for_selector(".text-widget")
        page.click(".text-widget")
        page.wait_for_selector(".sentence-word")

        page.locator(".sentence-word").first.click()
        page.wait_for_function("() => document.getElementById('word-details-status').textContent.trim() === 'Unseen'")
        page.locator(".sentence-word").nth(1).click()
        page.wait_for_function("() => document.getElementById('word-details-status').textContent.trim() === 'Unknown'")

        all_unknown = page.evaluate(
            """
            () => {
              const words = Array.from(document.querySelectorAll('.sentence-word')).filter((node) => node.textContent?.trim() === 'אבא');
              return words.length >= 2 && words.every((node) => node.classList.contains('unknown'));
            }
            """
        )
        assert all_unknown is True

        context.close()
        browser.close()


def test_reader_reopens_text_at_last_persisted_sentence_after_reload(live_server: str) -> None:
    playwright = pytest.importorskip("playwright.sync_api")

    with playwright.sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
        except playwright.Error as exc:
            pytest.skip(f"Playwright browser runtime unavailable: {exc}")

        # Create test user and text via API
        user_resp = urllib.request.urlopen(
            urllib.request.Request(
                f"{live_server}/v1/users",
                method="POST",
                data=json.dumps({"display_name": "Resume User"}).encode(),
                headers={"Content-Type": "application/json"},
            )
        )
        user_data = json.load(user_resp)
        user_id = user_data["user_id"]

        content = " ".join([f"מִשְׁפָּט{i}." for i in range(1, 41)])
        text_resp = urllib.request.urlopen(
            urllib.request.Request(
                f"{live_server}/v1/users/{user_id}/texts",
                method="POST",
                data=json.dumps({"title": "Resume Story", "content": content}).encode(),
                headers={"Content-Type": "application/json"},
            )
        )
        text_data = json.load(text_resp)
        text_id = text_data["text_id"]

        context = browser.new_context(base_url=live_server)
        page = context.new_page()

        # Set user in localStorage to log in
        page.add_init_script(f"localStorage.setItem('active_user_id', '{user_id}')")
        page.goto("/", wait_until="networkidle")

        # Click on the text card to open reader
        page.wait_for_selector(".text-widget")
        page.click(".text-widget")
        for target_sentence in range(1, 32):
            with page.expect_response(
                lambda response: "/position" in response.url
                and response.request.method == "PUT"
                and response.status == 200
            ):
                page.click("#next-sentence")
            page.wait_for_function(
                "(target) => document.getElementById('reader-meta').textContent.includes(`sentence ${target}`)",
                arg=target_sentence,
            )

        # Exit reader and reload
        page.click("#reader-exit-btn")
        page.reload(wait_until="networkidle")
        page.wait_for_selector(".text-widget")
        page.click(".text-widget")
        page.wait_for_function(
            "() => document.getElementById('reader-meta').textContent.includes('sentence 31')"
        )

        context.close()
        browser.close()
