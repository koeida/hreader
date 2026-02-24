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
