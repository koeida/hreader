#!/usr/bin/env python3
from __future__ import annotations

import argparse
import contextlib
import socket
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import uvicorn
from playwright.sync_api import Error, sync_playwright

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.main import create_app


@dataclass
class BrowserQaResult:
    name: str
    version: str
    matrix_result: str
    tabs_result: str
    aria_result: str
    modal_open_result: str
    escape_result: str
    backdrop_result: str
    close_button_result: str
    focus_result: str
    overflow_result: str
    modal_fit_result: str
    notes: str
    evidence_screenshot: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run automated desktop browser QA and write a filled report.",
    )
    parser.add_argument(
        "--date",
        default=datetime.now().strftime("%Y-%m-%d"),
        help="Report date in YYYY-MM-DD format (default: today).",
    )
    parser.add_argument(
        "--output-dir",
        default="docs/qa-reports",
        help="Directory to write the report into.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing report file for the same date.",
    )
    return parser.parse_args()


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


def _pass_fail(ok: bool) -> str:
    return "PASS" if ok else "FAIL"


def _failed_note(notes: list[str], label: str) -> None:
    notes.append(f"{label}=FAIL")


def _run_checks_for_browser(
    browser_name: str,
    playwright,
    base_url: str,
    screenshot_dir: Path,
    report_date: str,
) -> BrowserQaResult:
    browser_display_names = {
        "chromium": "Desktop Chromium",
        "firefox": "Desktop Firefox",
        "webkit": "Desktop WebKit",
    }
    display_name = browser_display_names[browser_name]
    browser_type = getattr(playwright, browser_name)
    browser = None
    version = ""
    notes: list[str] = []

    try:
        browser = browser_type.launch(headless=True)
        version = browser.version
        context = browser.new_context(base_url=base_url, viewport={"width": 1440, "height": 900})
        page = context.new_page()

        page.goto("/", wait_until="networkidle")
        page.fill("#new-user-name", f"{display_name} QA")
        page.click("#create-user-form button[type='submit']")
        page.wait_for_selector("#users-list li")

        text_body = "שָׁלוֹם לָכֶם. " + " ".join([f"מילה{i}" for i in range(1, 26)]) + "."
        page.fill("#new-text-title", f"{display_name} Text")
        page.fill("#new-text-content", text_body)
        page.click("#create-text-form button[type='submit']")
        page.wait_for_selector("#texts-list li button:has-text('Open in Reader')")
        page.click("#texts-list li button:has-text('Open in Reader')")
        page.wait_for_selector(".sentence-word")
        screenshot_name = f"desktop-{browser_name}-{report_date.replace('-', '')}-reader.png"
        screenshot_path = screenshot_dir / screenshot_name
        page.screenshot(path=str(screenshot_path), full_page=True)

        tabs_reachable = True
        aria_updates = True
        try:
            page.focus("#view-reader")
            page.keyboard.press("ArrowRight")
            page.wait_for_function(
                "() => document.querySelector('[data-view-target=\"words\"]').getAttribute('aria-selected') === 'true'"
            )
            page.keyboard.press("ArrowLeft")
            page.wait_for_function(
                "() => document.querySelector('[data-view-target=\"reader\"]').getAttribute('aria-selected') === 'true'"
            )
        except Error:
            tabs_reachable = False
            aria_updates = False

        page.click(".sentence-word")
        page.wait_for_selector("#word-modal.is-open")
        modal_open = page.eval_on_selector("#word-modal", "el => el.classList.contains('is-open')")
        escape_close = False
        backdrop_close = False
        close_button_close = False
        logical_focus = True

        page.keyboard.press("Escape")
        try:
            page.wait_for_function("() => !document.getElementById('word-modal').classList.contains('is-open')")
            escape_close = True
            page.wait_for_function("() => document.activeElement?.classList?.contains('sentence-word') === true")
        except Error:
            logical_focus = False

        page.click(".sentence-word")
        page.wait_for_selector("#word-modal.is-open")
        page.eval_on_selector("#word-modal-backdrop", "el => el.click()")
        try:
            page.wait_for_function("() => !document.getElementById('word-modal').classList.contains('is-open')")
            backdrop_close = True
            page.wait_for_function("() => document.activeElement?.classList?.contains('sentence-word') === true")
        except Error:
            logical_focus = False

        page.click(".sentence-word")
        page.wait_for_selector("#word-modal.is-open")
        page.click("#close-word-modal")
        try:
            page.wait_for_function("() => !document.getElementById('word-modal').classList.contains('is-open')")
            close_button_close = True
            page.wait_for_function("() => document.activeElement?.classList?.contains('sentence-word') === true")
        except Error:
            logical_focus = False

        no_overflow = page.eval_on_selector("#reader-sentence", "el => el.scrollWidth <= el.clientWidth + 1")
        page.click(".sentence-word")
        page.wait_for_selector("#word-modal.is-open")
        modal_fit = page.eval_on_selector(
            "#word-modal-surface",
            """
            (node) => {
              const rect = node.getBoundingClientRect();
              return rect.left >= 0 && rect.right <= window.innerWidth + 1;
            }
            """,
        )
        page.keyboard.press("Escape")
        page.wait_for_function("() => !document.getElementById('word-modal').classList.contains('is-open')")

        if not tabs_reachable:
            _failed_note(notes, "tabs")
        if not aria_updates:
            _failed_note(notes, "aria")
        if not modal_open:
            _failed_note(notes, "modal_open")
        if not escape_close:
            _failed_note(notes, "escape")
        if not backdrop_close:
            _failed_note(notes, "backdrop")
        if not close_button_close:
            _failed_note(notes, "close_button")
        if not logical_focus:
            _failed_note(notes, "focus")
        if not no_overflow:
            _failed_note(notes, "overflow")
        if not modal_fit:
            _failed_note(notes, "modal_fit")

        matrix_pass = all(
            [
                tabs_reachable,
                aria_updates,
                modal_open,
                escape_close,
                backdrop_close,
                close_button_close,
                logical_focus,
                no_overflow,
                modal_fit,
            ]
        )

        context.close()
        return BrowserQaResult(
            name=display_name,
            version=version,
            matrix_result=_pass_fail(matrix_pass),
            tabs_result=_pass_fail(tabs_reachable),
            aria_result=_pass_fail(aria_updates),
            modal_open_result=_pass_fail(bool(modal_open)),
            escape_result=_pass_fail(escape_close),
            backdrop_result=_pass_fail(backdrop_close),
            close_button_result=_pass_fail(close_button_close),
            focus_result=_pass_fail(logical_focus),
            overflow_result=_pass_fail(bool(no_overflow)),
            modal_fit_result=_pass_fail(bool(modal_fit)),
            notes="; ".join(notes) if notes else "Automated run passed.",
            evidence_screenshot=screenshot_path.as_posix(),
        )
    except Error as exc:
        return BrowserQaResult(
            name=display_name,
            version=version,
            matrix_result="FAIL",
            tabs_result="FAIL",
            aria_result="FAIL",
            modal_open_result="FAIL",
            escape_result="FAIL",
            backdrop_result="FAIL",
            close_button_result="FAIL",
            focus_result="FAIL",
            overflow_result="FAIL",
            modal_fit_result="FAIL",
            notes=f"Browser launch/check failed: {exc}",
            evidence_screenshot="",
        )
    finally:
        if browser is not None:
            browser.close()


def _render_report(report_date: str, results: list[BrowserQaResult], compact_date: str) -> str:
    overall_pass = all(result.matrix_result == "PASS" for result in results)
    overall = "PASS" if overall_pass else "FAIL"

    browser_rows = "\n".join(
        f"| {result.name} | {result.version} | {result.matrix_result} | {result.notes} |" for result in results
    )
    keyboard_rows = "\n".join(
        f"| {result.name} | {result.tabs_result} | {result.aria_result} | {result.notes} |" for result in results
    )
    modal_rows = "\n".join(
        f"| {result.name} | {result.modal_open_result} | {result.escape_result} | {result.backdrop_result} | "
        f"{result.close_button_result} | {result.focus_result} | {result.notes} |"
        for result in results
    )
    layout_rows = "\n".join(
        f"| {result.name} | {result.overflow_result} | {result.modal_fit_result} | {result.notes} |"
        for result in results
    )
    evidence_rows = "\n".join(
        f"| {result.name} | `{result.evidence_screenshot}` | {result.notes} |" for result in results
    )

    defects = "- None." if overall_pass else "- See failing rows/notes above."
    checklist_note = (
        "- All browser rows are PASS. Run `scripts/finalize_v1_checklist.py` with this report."
        if overall_pass
        else "- One or more rows failed. Keep checklist item 10 pending and track defects."
    )
    return f"""# Desktop Browser QA Report ({report_date})

- Date: {report_date}
- Tester: Automated Playwright desktop matrix (`scripts/run_desktop_browser_qa.py`)
- App commit:
- App URL: ephemeral local server
- Notes: Headless desktop run across Chromium + Firefox + WebKit.

## Browser Matrix

| Browser | Version | Result (`PASS`/`FAIL`) | Notes |
| --- | --- | --- | --- |
{browser_rows}

## Required Checks

Mark each check per browser with `PASS` or `FAIL` and include a short note.

### Keyboard-first tab navigation

| Browser | Tabs reachable | `aria-selected` updates | Notes |
| --- | --- | --- | --- |
{keyboard_rows}

### Reader interaction + modal close paths

| Browser | Open inline word modal | Escape close | Backdrop close | Close button | Logical focus retained | Notes |
| --- | --- | --- | --- | --- | --- | --- |
{modal_rows}

### Layout stability

| Browser | No horizontal overflow in reader panel | Word modal surface fits viewport | Notes |
| --- | --- | --- | --- |
{layout_rows}

## Evidence Artifacts

| Browser | Reader screenshot artifact | Notes |
| --- | --- | --- |
{evidence_rows}

## Manual Verification Evidence

Add reviewer-authored desktop notes here, including explicit Hebrew word-bubble RTL ordering confirmation per browser:
- Desktop Chromium:
- Desktop Firefox:
- Desktop WebKit:

## Defects

{defects}

## Sign-off

- Overall result (`PASS`/`FAIL`): {overall}
- Checklist update:
{checklist_note}

Generated by `scripts/run_desktop_browser_qa.py` on {compact_date}.
"""


def main() -> int:
    args = parse_args()
    report_date = args.date
    try:
        datetime.strptime(report_date, "%Y-%m-%d")
    except ValueError:
        raise SystemExit("Invalid --date format. Expected YYYY-MM-DD.")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    screenshot_dir = output_dir / "screenshots"
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / f"desktop-browser-qa-{report_date.replace('-', '')}.md"
    if report_path.exists() and not args.force:
        raise SystemExit(f"Report already exists: {report_path}")

    with tempfile.TemporaryDirectory(prefix="hreader-desktop-qa-") as tmp_dir:
        db_path = Path(tmp_dir) / "desktop-qa.db"
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
                results = [
                    _run_checks_for_browser("chromium", p, base_url, screenshot_dir, report_date),
                    _run_checks_for_browser("firefox", p, base_url, screenshot_dir, report_date),
                    _run_checks_for_browser("webkit", p, base_url, screenshot_dir, report_date),
                ]
        finally:
            server.should_exit = True
            thread.join(timeout=10)

    compact_date = report_date.replace("-", "")
    report_path.write_text(_render_report(report_date, results, compact_date), encoding="utf-8")
    print(report_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
