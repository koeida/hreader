#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

EVIDENCE_COMPLETE = (
    "Evidence complete: keyboard tab navigation, accessibility roles/labels, smoke + "
    "browser + visual QA artifacts, Playwright Chromium mobile emulation checks for "
    "iPhone 12 + Pixel 5 (tab reachability, modal close paths, narrow-width wrapping), "
    "and Playwright WebKit iPhone 12 emulation coverage for modal focus restoration + "
    "tab state changes; desktop browser QA matrix pass for Chromium + Firefox + WebKit."
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Promote Frontend checklist item 10 to Complete from a PASS desktop browser QA report.",
    )
    parser.add_argument(
        "--report",
        required=True,
        help="Path to a completed docs/qa-reports/desktop-browser-qa-YYYYMMDD.md report.",
    )
    parser.add_argument(
        "--checklist",
        default="docs/v1-checklist.md",
        help="Path to the V1 checklist document.",
    )
    return parser.parse_args()


def _device_pass(report: str, device: str) -> bool:
    # Matrix rows are in markdown table format; require PASS in the Result column.
    pattern = rf"^\|\s*{re.escape(device)}\s*\|.*\|\s*PASS\s*\|"
    return re.search(pattern, report, flags=re.MULTILINE) is not None


def validate_report(report_text: str) -> None:
    if "Overall result (`PASS`/`FAIL`): PASS" not in report_text:
        raise SystemExit("Report overall result is not PASS.")
    if not _device_pass(report_text, "Desktop Chromium"):
        raise SystemExit("Report does not show PASS for Desktop Chromium in Browser Matrix.")
    if not _device_pass(report_text, "Desktop Firefox"):
        raise SystemExit("Report does not show PASS for Desktop Firefox in Browser Matrix.")
    if not _device_pass(report_text, "Desktop WebKit"):
        raise SystemExit("Report does not show PASS for Desktop WebKit in Browser Matrix.")


def update_checklist(checklist_text: str, report_path: Path) -> str:
    current_pattern = re.compile(
        r"10\. UX Hardening \+ Basic QA Gates: `(?:Pending|Complete)`\n.*?(?=\n## Current Release Gate)",
        flags=re.DOTALL,
    )

    match = current_pattern.search(checklist_text)
    if not match:
        raise SystemExit("Could not find Frontend item 10 block in checklist.")

    replacement = (
        "10. UX Hardening + Basic QA Gates: `Complete`\n"
        f"{EVIDENCE_COMPLETE}"
        f" Real-device QA PASS report: `{report_path.as_posix()}`.\n"
    )
    updated = checklist_text[: match.start()] + replacement + checklist_text[match.end() :]
    return updated.replace(
        "Final sign-off still requires the desktop browser QA checklist pass.",
        "All V1 checklist items are complete.",
    )


def main() -> int:
    args = parse_args()
    report_path = Path(args.report)
    checklist_path = Path(args.checklist)

    if not report_path.exists():
        raise SystemExit(f"Report file not found: {report_path}")
    if not checklist_path.exists():
        raise SystemExit(f"Checklist file not found: {checklist_path}")

    report_text = report_path.read_text(encoding="utf-8")
    validate_report(report_text)

    checklist_text = checklist_path.read_text(encoding="utf-8")
    updated = update_checklist(checklist_text, report_path)

    if updated != checklist_text:
        checklist_path.write_text(updated, encoding="utf-8")

    print(checklist_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
