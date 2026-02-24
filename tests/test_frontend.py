from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app


def make_client(tmp_path: Path) -> TestClient:
    app = create_app(db_path=str(tmp_path / "test.db"))
    return TestClient(app)


def test_root_serves_frontend_html(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        resp = client.get("/")

    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "data-testid=\"app-root\"" in resp.text
    assert "/static/app.js" in resp.text


def test_static_assets_are_served(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        js = client.get("/static/app.js")
        css = client.get("/static/styles.css")

    assert js.status_code == 200
    assert "class ApiClient" in js.text
    assert css.status_code == 200
    assert ":root" in css.text


def test_frontend_uses_inline_word_details_panel(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        js = client.get("/static/app.js")
        html = client.get("/")

    assert js.status_code == 200
    assert html.status_code == 200

    assert "word-modal" not in html.text
    assert "modal-word-state" not in html.text
    assert "jump-sentence-form" not in html.text
    assert "API Base URL" not in html.text
    assert "Check API" not in html.text

    assert 'id="word-details-panel"' in html.text
    assert 'id="word-details-word"' in html.text
    assert 'id="word-details-status"' in html.text
    assert 'id="word-details-state"' in html.text
    assert 'id="meanings-preview"' in html.text

    assert "onSentenceWordActivated" in js.text
    assert "cycleState" in js.text
    assert "clearWordDetailsPanel" in js.text
    assert "state.selectedWord !== word" in js.text
    assert "renderSentence();" in js.text
    assert "animateSelectionPulse" in js.text


def test_frontend_has_stale_request_guards_for_async_panels(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        js = client.get("/static/app.js")

    assert js.status_code == 200
    assert "requestVersion" in js.text
    assert "nextRequestVersion" in js.text
    assert "isCurrentRequest" in js.text
    assert '!isCurrentRequest("texts", requestVersion)' in js.text
    assert '!isCurrentRequest("words", requestVersion)' in js.text
    assert '!isCurrentRequest("sentence", requestVersion)' in js.text
    assert '!isCurrentRequest("meanings", requestVersion)' in js.text
    assert "word !== state.selectedWord" in js.text
    assert "state.selectedWord !== actionWord" in js.text


def test_frontend_styles_support_inline_panel_and_selected_word_pulse(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        css = client.get("/static/styles.css")

    assert css.status_code == 200
    assert ".word-details-panel" in css.text
    assert ".word-details-panel.is-hidden" in css.text
    assert ".sentence-word.active" in css.text
    assert ".sentence-word.pulse" in css.text
    assert "@keyframes word-pulse" in css.text
    assert ".app.view-reader" in css.text
    assert 'width: min(1500px, calc(100vw - 6rem));' in css.text
