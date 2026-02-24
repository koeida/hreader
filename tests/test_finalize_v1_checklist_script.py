from __future__ import annotations

import subprocess
from pathlib import Path


CHECKLIST_BASE = """# V1 Completion Checklist

## Frontend V1

10. UX Hardening + Basic QA Gates: `Pending`
Evidence complete: keyboard tab navigation, accessibility roles/labels, smoke + browser + visual QA artifacts, Playwright Chromium mobile emulation checks for iPhone 12 + Pixel 5 (tab reachability, modal close paths, narrow-width wrapping), and Playwright WebKit iPhone 12 emulation coverage for modal focus restoration + tab state changes.
Remaining: manual real-device pass on iOS Safari and Android Chrome per `docs/visual-qa.md`, documented in a dated report under `docs/qa-reports/mobile-real-device-YYYYMMDD.md`.

## Current Release Gate

Final sign-off still requires the real-device mobile checklist pass.
"""


def _write_report(path: Path, *, ios_result: str, android_result: str, overall: str) -> None:
    path.write_text(
        f"""# Mobile Real-Device QA Report (2026-02-24)

## Device Matrix

| Device | OS version | Browser version | Result (`PASS`/`FAIL`) | Notes |
| --- | --- | --- | --- | --- |
| iOS Safari | 17 | Safari | {ios_result} |  |
| Android Chrome | 14 | Chrome | {android_result} |  |

## Sign-off

- Overall result (`PASS`/`FAIL`): {overall}
""",
        encoding="utf-8",
    )


def test_finalize_v1_checklist_updates_item_10_when_report_passes(tmp_path: Path) -> None:
    checklist_path = tmp_path / "v1-checklist.md"
    report_path = tmp_path / "mobile-real-device-20260224.md"
    checklist_path.write_text(CHECKLIST_BASE, encoding="utf-8")
    _write_report(report_path, ios_result="PASS", android_result="PASS", overall="PASS")

    result = subprocess.run(
        [
            ".venv/bin/python",
            "scripts/finalize_v1_checklist.py",
            "--report",
            str(report_path),
            "--checklist",
            str(checklist_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert Path(result.stdout.strip()) == checklist_path
    updated = checklist_path.read_text(encoding="utf-8")
    assert "10. UX Hardening + Basic QA Gates: `Complete`" in updated
    assert f"Real-device QA PASS report: `{report_path.as_posix()}`." in updated
    assert "Remaining: manual real-device pass" not in updated


def test_finalize_v1_checklist_rejects_non_pass_report(tmp_path: Path) -> None:
    checklist_path = tmp_path / "v1-checklist.md"
    report_path = tmp_path / "mobile-real-device-20260224.md"
    checklist_path.write_text(CHECKLIST_BASE, encoding="utf-8")
    _write_report(report_path, ios_result="PASS", android_result="FAIL", overall="FAIL")

    result = subprocess.run(
        [
            ".venv/bin/python",
            "scripts/finalize_v1_checklist.py",
            "--report",
            str(report_path),
            "--checklist",
            str(checklist_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "Report overall result is not PASS." in result.stderr
    assert checklist_path.read_text(encoding="utf-8") == CHECKLIST_BASE
