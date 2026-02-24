from pathlib import Path


def test_v1_checklist_covers_all_backend_and_frontend_features() -> None:
    checklist = Path("docs/v1-checklist.md").read_text(encoding="utf-8")

    for index in range(1, 12):
        assert f"{index}. " in checklist

    frontend_section = checklist.split("## Frontend V1", maxsplit=1)[1]
    for index in range(1, 11):
        assert f"{index}. " in frontend_section

    assert "Chromium" in checklist
    assert "Firefox" in checklist
    assert "WebKit" in checklist
    assert "mobile emulation" in checklist
    assert "WebKit" in checklist
    assert ("Pending" in checklist) or ("Complete" in checklist)
    assert "docs/qa-reports/desktop-browser-qa-" in checklist


def test_visual_qa_doc_mentions_real_device_report_workflow() -> None:
    visual_qa = Path("docs/visual-qa.md").read_text(encoding="utf-8")

    assert "scripts/new_desktop_qa_report.py" in visual_qa
    assert "scripts/run_desktop_browser_qa.py" in visual_qa
    assert "scripts/finalize_v1_checklist.py" in visual_qa
    assert "docs/qa-reports/desktop-browser-qa-YYYYMMDD.md" in visual_qa


def test_ui_beauty_spec_is_present_and_desktop_first() -> None:
    beauty_spec = Path("docs/ui-beauty-spec.md").read_text(encoding="utf-8")

    assert "Desktop UI Beauty Spec" in beauty_spec
    assert "desktop-first" in beauty_spec
    assert "Modern-Blue" in beauty_spec
    assert "Phase 1" in beauty_spec
    assert "Phase 2" in beauty_spec
    assert "Chromium/Firefox/WebKit" in beauty_spec


def test_latest_desktop_reports_include_manual_and_design_review_evidence() -> None:
    desktop_report = Path("docs/qa-reports/desktop-browser-qa-20260224.md").read_text(encoding="utf-8")
    design_review = Path("docs/qa-reports/ui-design-review-20260224.md").read_text(encoding="utf-8")

    assert "Manual Verification Evidence" in desktop_report
    assert "Reader screenshot artifact" in desktop_report
    assert "Independent agent pass" in design_review
    assert "Phase 2 Refinement Decisions" in design_review
