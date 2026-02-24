from pathlib import Path
import re


def test_visual_qa_doc_screenshot_inventory_matches_files() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    visual_qa_dir = repo_root / "docs" / "visual-qa"
    visual_qa_doc = repo_root / "docs" / "visual-qa.md"

    actual_screenshots = sorted(path.name for path in visual_qa_dir.glob("*.png"))
    expected_screenshots = sorted(
        re.findall(r"`docs/visual-qa/([^`]+\.png)`", visual_qa_doc.read_text(encoding="utf-8"))
    )

    assert actual_screenshots == expected_screenshots
