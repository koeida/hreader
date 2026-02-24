from __future__ import annotations

import contextlib
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


def test_browser_journey_user_text_reader_and_words_panels(live_server: str) -> None:
    playwright = pytest.importorskip("playwright.sync_api")

    with playwright.sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
        except playwright.Error as exc:
            pytest.skip(f"Playwright browser runtime unavailable: {exc}")

        context = browser.new_context(base_url=live_server)
        page = context.new_page()

        page.goto("/", wait_until="networkidle")

        page.fill("#new-user-name", "Browser User")
        page.click("#create-user-form button[type='submit']")
        page.wait_for_selector("#users-list li")

        bulk_words = " ".join([f"alpha{i}" for i in range(1, 31)])
        text_body = f"שָׁלוֹם לָכֶם. הַבַּיִת גָּדוֹל. {bulk_words}."
        page.fill("#new-text-title", "מסע דפדפן")
        page.fill("#new-text-content", text_body)
        page.click("#create-text-form button[type='submit']")
        page.wait_for_selector("#texts-list li button:has-text('Open in Reader')")

        page.click("#texts-list li button:has-text('Open in Reader')")
        page.wait_for_function(
            "() => document.getElementById('reader-sentence').textContent.includes('שָׁלוֹם לָכֶם')"
        )

        page.focus("#view-reader")
        page.keyboard.press("ArrowRight")
        page.wait_for_function(
            "() => document.querySelector('[data-view-target=\"words\"]').getAttribute('aria-selected') === 'true'"
        )
        page.keyboard.press("ArrowLeft")
        page.wait_for_function(
            "() => document.querySelector('[data-view-target=\"reader\"]').getAttribute('aria-selected') === 'true'"
        )

        page.click("#next-sentence")
        page.wait_for_function(
            "() => document.getElementById('reader-sentence').textContent.includes('הַבַּיִת גָּדוֹל')"
        )
        page.click("#next-sentence")
        page.wait_for_function(
            "() => document.getElementById('reader-sentence').textContent.includes('alpha1')"
        )

        page.fill("#jump-sentence-index", "99")
        assert page.eval_on_selector("#jump-sentence-index", "el => el.validity.rangeOverflow") is True
        page.click("#jump-sentence-btn")
        page.wait_for_function(
            "() => document.getElementById('reader-sentence').textContent.includes('alpha1')"
        )

        page.click(".sentence-word")
        page.wait_for_selector("#word-modal.is-open")
        page.keyboard.press("Escape")
        page.wait_for_function("() => !document.getElementById('word-modal').classList.contains('is-open')")
        page.wait_for_function("() => document.activeElement?.classList?.contains('sentence-word') === true")

        page.click(".sentence-word")
        page.wait_for_selector("#word-modal.is-open")
        page.eval_on_selector("#word-modal-backdrop", "el => el.click()")
        page.wait_for_function("() => !document.getElementById('word-modal').classList.contains('is-open')")
        page.wait_for_function("() => document.activeElement?.classList?.contains('sentence-word') === true")

        page.click(".sentence-word")
        page.wait_for_selector("#word-modal.is-open")
        page.select_option("#modal-word-state", "known")
        page.click("#close-word-modal")
        page.wait_for_function("() => document.activeElement?.classList?.contains('sentence-word') === true")
        page.click("#view-words")
        page.select_option("#words-limit", "25")
        page.wait_for_function("() => document.getElementById('words-page-label').textContent.includes('Page 1 /')")
        page.click("#words-next-page")
        page.wait_for_function("() => document.getElementById('words-page-label').textContent.includes('Page 2 /')")

        page.select_option("#words-filter", "known")
        page.wait_for_function(
            """
            () => {
              const words = Array.from(document.querySelectorAll('#words-list li small')).map((n) => n.textContent || '');
              return words.some((t) => t.includes('known'));
            }
            """
        )

        context.close()
        browser.close()
