from __future__ import annotations

import subprocess
from pathlib import Path


def test_new_mobile_qa_report_script_writes_template(tmp_path: Path) -> None:
    output_dir = tmp_path / "reports"
    result = subprocess.run(
        [
            ".venv/bin/python",
            "scripts/new_mobile_qa_report.py",
            "--date",
            "2026-02-24",
            "--output-dir",
            str(output_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    report_path = Path(result.stdout.strip())
    assert report_path == output_dir / "mobile-real-device-20260224.md"
    assert report_path.exists()

    report = report_path.read_text(encoding="utf-8")
    assert "iOS Safari" in report
    assert "Android Chrome" in report
    assert "Overall result (`PASS`/`FAIL`):" in report
