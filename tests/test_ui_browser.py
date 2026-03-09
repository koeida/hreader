from __future__ import annotations

import contextlib
import json
import socket
import threading
import time
import urllib.error
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


def test_reader_word_details_panel_select_cycle_and_reset(live_server: str) -> None:
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
        assert page.locator("#word-details-status").inner_text().strip() == "Unseen"
        first_selected = page.locator("#word-details-word").inner_text().strip()

        first.click()
        page.wait_for_function("() => document.getElementById('word-details-status').textContent.trim() === 'Unknown'")
        first.click()
        page.wait_for_function("() => document.getElementById('word-details-status').textContent.trim() === 'Known'")
        first.click()
        page.wait_for_function("() => document.getElementById('word-details-status').textContent.trim() === 'Unseen'")

        second.click()
        page.wait_for_function(
            "(word) => document.getElementById('word-details-word').textContent.trim() !== word",
            arg=first_selected,
        )
        assert page.locator("#word-details-status").inner_text().strip() == "Unseen"

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
        page.fill("#meaning-context", "context")
        page.click("#generate-meaning-form button[type='submit']")

        first_selected = page.locator("#word-details-word").inner_text().strip()
        second.click()
        page.wait_for_function(
            "(word) => document.getElementById('word-details-word').textContent.trim() !== word",
            arg=first_selected,
        )

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
              const words = Array.from(document.querySelectorAll('.sentence-word')).filter((node) => node.textContent?.trim() === 'אָבָא');
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
        for _ in range(31):
            page.click("#next-sentence")
        page.wait_for_function(
            "() => document.getElementById('reader-meta').textContent.includes('sentence 31')"
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
