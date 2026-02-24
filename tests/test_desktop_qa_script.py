from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_module():
    module_path = Path("scripts/run_desktop_browser_qa.py")
    spec = importlib.util.spec_from_file_location("run_desktop_browser_qa", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load run_desktop_browser_qa module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_render_report_marks_overall_pass_when_all_browsers_pass() -> None:
    mod = _load_module()
    results = [
        mod.BrowserQaResult(
            name="Desktop Chromium",
            version="1",
            matrix_result="PASS",
            tabs_result="PASS",
            aria_result="PASS",
            modal_open_result="PASS",
            escape_result="PASS",
            backdrop_result="PASS",
            close_button_result="PASS",
            focus_result="PASS",
            overflow_result="PASS",
            modal_fit_result="PASS",
            notes="ok",
            evidence_screenshot="docs/qa-reports/screenshots/desktop-chromium-20260224-reader.png",
        ),
        mod.BrowserQaResult(
            name="Desktop Firefox",
            version="1",
            matrix_result="PASS",
            tabs_result="PASS",
            aria_result="PASS",
            modal_open_result="PASS",
            escape_result="PASS",
            backdrop_result="PASS",
            close_button_result="PASS",
            focus_result="PASS",
            overflow_result="PASS",
            modal_fit_result="PASS",
            notes="ok",
            evidence_screenshot="docs/qa-reports/screenshots/desktop-firefox-20260224-reader.png",
        ),
        mod.BrowserQaResult(
            name="Desktop WebKit",
            version="1",
            matrix_result="PASS",
            tabs_result="PASS",
            aria_result="PASS",
            modal_open_result="PASS",
            escape_result="PASS",
            backdrop_result="PASS",
            close_button_result="PASS",
            focus_result="PASS",
            overflow_result="PASS",
            modal_fit_result="PASS",
            notes="ok",
            evidence_screenshot="docs/qa-reports/screenshots/desktop-webkit-20260224-reader.png",
        ),
    ]

    report = mod._render_report("2026-02-24", results, "20260224")
    assert "Overall result (`PASS`/`FAIL`): PASS" in report
    assert "Desktop Chromium" in report
    assert "Desktop Firefox" in report
    assert "Desktop WebKit" in report
    assert "Manual Verification Evidence" in report
    assert "Reader screenshot artifact" in report


def test_render_report_marks_overall_fail_when_any_browser_fails() -> None:
    mod = _load_module()
    results = [
        mod.BrowserQaResult(
            name="Desktop Chromium",
            version="1",
            matrix_result="PASS",
            tabs_result="PASS",
            aria_result="PASS",
            modal_open_result="PASS",
            escape_result="PASS",
            backdrop_result="PASS",
            close_button_result="PASS",
            focus_result="PASS",
            overflow_result="PASS",
            modal_fit_result="PASS",
            notes="ok",
            evidence_screenshot="docs/qa-reports/screenshots/desktop-chromium-20260224-reader.png",
        ),
        mod.BrowserQaResult(
            name="Desktop Firefox",
            version="1",
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
            notes="fail",
            evidence_screenshot="docs/qa-reports/screenshots/desktop-firefox-20260224-reader.png",
        ),
        mod.BrowserQaResult(
            name="Desktop WebKit",
            version="1",
            matrix_result="PASS",
            tabs_result="PASS",
            aria_result="PASS",
            modal_open_result="PASS",
            escape_result="PASS",
            backdrop_result="PASS",
            close_button_result="PASS",
            focus_result="PASS",
            overflow_result="PASS",
            modal_fit_result="PASS",
            notes="ok",
            evidence_screenshot="docs/qa-reports/screenshots/desktop-webkit-20260224-reader.png",
        ),
    ]

    report = mod._render_report("2026-02-24", results, "20260224")
    assert "Overall result (`PASS`/`FAIL`): FAIL" in report
    assert "- See failing rows/notes above." in report
