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


def test_frontend_uses_inline_controls_instead_of_prompts(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        js = client.get("/static/app.js")
        html = client.get("/")

    assert js.status_code == 200
    assert "window.prompt" not in js.text
    assert "rename-form" in js.text
    assert "sentence-word" in js.text
    assert "modalWordState" in js.text
    assert "word-modal" in html.text
    assert "jumpSentenceForm" in js.text
    assert "wordsPrevPage" in js.text
    assert "setActiveView" in js.text
    assert "button.onkeydown" in js.text
    assert "VIEW_ORDER" in js.text
    assert "aria-selected" in js.text
    assert "Open in Reader" in js.text
    assert "Jump to Sentence" in html.text
    assert "Generate English Meaning" in html.text
    assert 'role="tablist"' in html.text
    assert 'role="tab"' in html.text
    assert "data-view-panel" in html.text
    assert "words?state=${state}&page=${page}&limit=${limit}" in js.text
    assert html.status_code == 200
    assert 'id="reader-state"' in html.text
    assert 'id="reader-sentence" class="sentence" lang="he" dir="rtl"' in html.text
    assert 'id="jump-sentence-form"' in html.text
    assert 'id="modal-word-state"' in html.text
    assert 'id="word-modal"' in html.text
    assert 'id="words-limit"' in html.text
    assert 'id="words-prev-page"' in html.text
    assert 'id="words-next-page"' in html.text
    assert 'id="view-library"' in html.text
    assert 'id="view-reader"' in html.text
    assert 'id="view-words"' in html.text


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
