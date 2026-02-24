from __future__ import annotations

import contextlib
import socket
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

import uvicorn
from playwright.sync_api import sync_playwright

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.main import create_app

CANONICAL_SCREENSHOT_NAMES = (
    "01-empty-shell.png",
    "02-user-and-text-library.png",
    "03-reader-modal.png",
    "04-reader-and-words.png",
)


def find_free_port() -> int:
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("127.0.0.1", 0))
        sock.listen(1)
        return int(sock.getsockname()[1])


def wait_for_health(base_url: str, timeout_seconds: float = 20.0) -> None:
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


def main() -> int:
    output_dir = REPO_ROOT / "docs" / "visual-qa"
    output_dir.mkdir(parents=True, exist_ok=True)
    canonical_names = set(CANONICAL_SCREENSHOT_NAMES)
    for existing_file in output_dir.glob("*.png"):
        if existing_file.name not in canonical_names:
            existing_file.unlink()

    with tempfile.TemporaryDirectory(prefix="hreader-visual-qa-") as tmp_dir:
        db_path = Path(tmp_dir) / "visual-qa.db"
        app = create_app(db_path=str(db_path))

        port = find_free_port()
        base_url = f"http://127.0.0.1:{port}"
        config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error")
        server = uvicorn.Server(config)
        thread = threading.Thread(target=server.run, daemon=True)
        thread.start()

        try:
            wait_for_health(base_url)

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(base_url=base_url, viewport={"width": 1440, "height": 1080})
                page = context.new_page()

                page.goto("/", wait_until="networkidle")
                page.screenshot(path=str(output_dir / CANONICAL_SCREENSHOT_NAMES[0]), full_page=True)

                page.fill("#new-user-name", "QA Parent")
                page.click("#create-user-form button[type='submit']")
                page.wait_for_selector("#users-list li")

                text_body = "שָׁלוֹם לָכֶם. דָּנָה קוֹרֵאת סֵפֶר. הַבַּיִת גָּדוֹל וְנוֹרָא יָפֶה."
                page.fill("#new-text-title", "סיפור ביתי")
                page.fill("#new-text-content", text_body)
                page.click("#create-text-form button[type='submit']")
                page.wait_for_selector("#texts-list li button:has-text('Open in Reader')")
                page.screenshot(path=str(output_dir / CANONICAL_SCREENSHOT_NAMES[1]), full_page=True)

                page.click("#texts-list li button:has-text('Open in Reader')")
                page.wait_for_function(
                    "() => document.getElementById('reader-sentence').textContent.includes('שָׁלוֹם לָכֶם')"
                )
                page.click(".sentence-word")
                page.wait_for_selector("#word-modal.is-open")
                page.select_option("#modal-word-state", "known")
                page.wait_for_timeout(200)
                page.screenshot(path=str(output_dir / CANONICAL_SCREENSHOT_NAMES[2]), full_page=True)
                page.keyboard.press("Escape")
                page.wait_for_selector("#word-modal:not(.is-open)")

                page.click("#view-words")
                page.select_option("#words-filter", "known")
                page.wait_for_timeout(250)
                page.screenshot(path=str(output_dir / CANONICAL_SCREENSHOT_NAMES[3]), full_page=True)

                context.close()
                browser.close()
        finally:
            server.should_exit = True
            thread.join(timeout=10)

    print(f"Saved UI screenshots to: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
