from __future__ import annotations

import contextlib
import socket
import sys
import tempfile
import threading
import time
import json
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
    "03-reader-word-details.png",
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


def post_json(url: str, payload: dict) -> dict:
    request = urllib.request.Request(
        url,
        method="POST",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=5.0) as resp:
        return json.loads(resp.read().decode("utf-8"))


def put_json(url: str, payload: dict) -> dict:
    request = urllib.request.Request(
        url,
        method="PUT",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=5.0) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=5.0) as resp:
        return json.loads(resp.read().decode("utf-8"))


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

                user_data = post_json(f"{base_url}/v1/users", {"display_name": "QA Parent"})
                user_id = user_data["user_id"]
                text_body = "שָׁלוֹם לָכֶם. דָּנָה קוֹרֵאת סֵפֶר. הַבַּיִת גָּדוֹל וְנוֹרָא יָפֶה."
                text_data = post_json(
                    f"{base_url}/v1/users/{user_id}/texts",
                    {"title": "סיפור ביתי", "content": text_body, "language": "hebrew"},
                )
                post_json(
                    f"{base_url}/v1/users/{user_id}/texts",
                    {"title": "מילים חדשות", "content": "אָבָא אִמָא. יֶלֶד קוֹרֵא.", "language": "hebrew"},
                )
                get_json(f"{base_url}/v1/users/{user_id}/texts/{text_data['text_id']}/sentences/0")
                put_json(f"{base_url}/v1/users/{user_id}/texts/{text_data['text_id']}/position", {"sentence_index": 0})
                page.evaluate("(userId) => localStorage.setItem('active_user_id', userId)", user_id)
                page.goto("/", wait_until="networkidle")
                page.wait_for_selector(".text-widget")
                page.screenshot(path=str(output_dir / CANONICAL_SCREENSHOT_NAMES[1]), full_page=True)

                page.click(".text-widget")
                page.wait_for_selector(".sentence-word")
                page.click(".sentence-word")
                page.wait_for_function("() => !document.getElementById('word-details-panel').classList.contains('is-hidden')")
                page.locator(".sentence-word").first.click()
                page.wait_for_function("() => document.getElementById('word-details-status').textContent.trim() === 'Unknown'")
                page.screenshot(path=str(output_dir / CANONICAL_SCREENSHOT_NAMES[2]), full_page=True)

                page.click("#reader-exit-btn")
                page.wait_for_selector("#app-header:not(.is-hidden)")
                page.click("#nav-progress")
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
