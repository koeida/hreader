from pathlib import Path


def test_v1_checklist_covers_all_backend_and_frontend_features() -> None:
    checklist = Path("docs/v1-checklist.md").read_text(encoding="utf-8")

    for index in range(1, 12):
        assert f"{index}. " in checklist

    frontend_section = checklist.split("## Frontend V1", maxsplit=1)[1]
    for index in range(1, 11):
        assert f"{index}. " in frontend_section

    assert "iOS Safari" in checklist
    assert "Android Chrome" in checklist
    assert "mobile emulation" in checklist
    assert "WebKit" in checklist
    assert "Pending" in checklist
    assert "docs/qa-reports/mobile-real-device-YYYYMMDD.md" in checklist


def test_visual_qa_doc_mentions_real_device_report_workflow() -> None:
    visual_qa = Path("docs/visual-qa.md").read_text(encoding="utf-8")

    assert "scripts/new_mobile_qa_report.py" in visual_qa
    assert "docs/qa-reports/mobile-real-device-YYYYMMDD.md" in visual_qa
