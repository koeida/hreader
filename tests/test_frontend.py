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
    assert 'id="mnemonic-form"' in html.text
    assert 'id="word-mnemonic"' in html.text
    assert 'id="word-mnemonic-display"' in html.text
    assert 'id="mnemonic-reveal"' in html.text
    assert 'id="word-details-reveal-count"' in html.text
    assert 'id="add-meaning-form"' in html.text
    assert 'id="manual-meaning-display"' in html.text
    assert 'id="meanings-preview"' in html.text
    assert "Word Details" not in html.text
    assert "Status:" not in html.text
    assert "Generation context" not in html.text
    assert "Save Mnemonic" not in html.text
    assert "Add Meaning" not in html.text
    assert 'id="view-srs"' in html.text
    assert 'id="section-srs"' in html.text
    assert 'id="srs-front-word"' in html.text
    assert 'id="srs-reveal"' in html.text
    assert 'id="srs-mnemonic-input"' in html.text
    assert 'id="srs-delete-card"' in html.text
    assert 'id="srs-postpone-btn"' in html.text
    assert 'id="postpone-slider"' in html.text
    assert 'id="streak-header-chip"' in html.text
    assert 'id="streak-reader-chip"' in html.text
    assert 'id="streak-progress-card"' in html.text

    assert "onSentenceWordActivated" in js.text
    assert "cycleState" in js.text
    assert "clearWordDetailsPanel" in js.text
    assert "saveInlineMnemonic" in js.text
    assert "revealWordDetails" in js.text
    assert "saveInlineMeaning" in js.text
    assert "loadSrsSession" in js.text
    assert "submitSrsResult" in js.text
    assert "deleteCurrentSrsCard" in js.text
    assert "deleteSrsCard" in js.text
    assert "srsReinsertWrongCard" in js.text
    assert "startSrsMnemonicEdit" in js.text
    assert "el.srsMnemonicForm.requestSubmit()" in js.text
    assert "state.selectedWord !== word" in js.text
    assert "renderSentence();" in js.text
    assert "READER_RASHI_PRESENTATION_LAYER" in js.text
    assert "cycleReaderF3Mode" in js.text
    assert 'event.key === "F4"' in js.text
    assert "animateSelectionPulse" in js.text
    assert "getStreak" in js.text
    assert "loadStreak" in js.text
    assert "renderStreak" in js.text


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
    assert '!isCurrentRequest("wordDetails", requestVersion)' in js.text
    assert "word !== state.selectedWord" in js.text
    assert "state.selectedWord !== actionWord" in js.text
    assert "getTextPosition" in js.text
    assert "updateTextPosition" in js.text


def test_frontend_library_sort_and_feature_hooks_exist(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        js = client.get("/static/app.js")
        html = client.get("/")

    assert js.status_code == 200
    assert html.status_code == 200

    assert 'id="library-sort-switcher"' in html.text
    assert html.text.count("data-library-sort=") == 3
    assert 'data-library-sort="date-added"' in html.text
    assert 'data-library-sort="percent-read"' in html.text
    assert 'data-library-sort="percent-known"' in html.text
    assert "getLastReadText" in js.text
    assert "compareLibraryTexts" in js.text
    assert "libraryReadPercent" in js.text
    assert "text-widget--featured" in js.text


def test_frontend_styles_support_inline_panel_and_selected_word_pulse(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        css = client.get("/static/styles.css")

    assert css.status_code == 200
    assert ".word-details-panel" in css.text
    assert ".word-details-panel.is-hidden" in css.text
    assert ".word-details-panel.status-unknown" in css.text
    assert ".word-details-panel.status-known" in css.text
    assert ".inline-edit-display" in css.text
    assert ".sentence-word.active" in css.text
    assert ".sentence-word.pulse" in css.text
    assert "@keyframes word-pulse" in css.text
    assert "--motion-duration-fast" in css.text
    assert "--motion-ease-standard" in css.text
    assert "@media (prefers-reduced-motion: reduce)" in css.text
    assert "scroll-behavior: auto !important" in css.text
    assert ".srs-card-flip.flipped .srs-card-front" in css.text
    assert ".app.view-reader" in css.text
    assert 'width: min(1500px, calc(100vw - 6rem));' in css.text
    assert ".app.view-srs" in css.text
    assert ".srs-front-word" in css.text
    assert ".streak-chip:focus-visible" in css.text
    assert ".streak-chip--reader.active" in css.text
    assert ".streak-card" in css.text
    assert ".streak-day-strip" in css.text
