from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app
from app.meanings import MeaningGenerationError


class CountingGenerator:
    def __init__(self) -> None:
        self.calls = 0

    def generate(self, normalized_word: str, sentence_context: str | None) -> str:
        self.calls += 1
        return f"Meaning gloss {self.calls}"


class WhitespaceEnglishGenerator:
    def generate(self, normalized_word: str, sentence_context: str | None) -> str:
        return "  basic   meaning\n"


class HebrewOutputGenerator:
    def generate(self, normalized_word: str, sentence_context: str | None) -> str:
        return f"פירוש עבור {normalized_word}"


class TimeoutGenerator:
    def generate(self, normalized_word: str, sentence_context: str | None) -> str:
        raise MeaningGenerationError("meaning_generation_timeout")


def make_client(tmp_path: Path, generator: object | None = None) -> TestClient:
    app = create_app(db_path=str(tmp_path / "test.db"), meaning_generator=generator)
    return TestClient(app)


def create_user(client: TestClient, name: str = "User") -> str:
    resp = client.post("/v1/users", json={"display_name": name})
    assert resp.status_code == 200
    return resp.json()["user_id"]


def create_text(client: TestClient, user_id: str, title: str, content: str) -> str:
    resp = client.post(f"/v1/users/{user_id}/texts", json={"title": title, "content": content})
    assert resp.status_code == 200
    return resp.json()["text_id"]


def test_health_and_unknown_v1_route(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json() == {"status": "ok"}

        missing = client.get("/v1/does-not-exist")
        assert missing.status_code == 404
        assert missing.json()["error"]["code"] == "not_found"


def test_user_lifecycle_soft_delete_and_restore(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        user_id = create_user(client, "Dana")

        users = client.get("/v1/users").json()["items"]
        assert any(u["user_id"] == user_id for u in users)

        delete_resp = client.delete(f"/v1/users/{user_id}")
        assert delete_resp.status_code == 200
        assert delete_resp.json()["deleted_at"] is not None

        users_default = client.get("/v1/users").json()["items"]
        assert not any(u["user_id"] == user_id for u in users_default)

        users_incl = client.get("/v1/users?include_deleted=true").json()["items"]
        assert any(u["user_id"] == user_id for u in users_incl)

        restore_resp = client.post(f"/v1/users/{user_id}/restore")
        assert restore_resp.status_code == 200
        assert restore_resp.json()["deleted_at"] is None


def test_text_crud_sentence_splitting_and_privacy(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        user_a = create_user(client, "A")
        user_b = create_user(client, "B")

        content = "א.  ב\nשורה. ג."
        text_id = create_text(client, user_a, "כותרת", content)

        s0 = client.get(f"/v1/users/{user_a}/texts/{text_id}/sentences/0")
        assert s0.status_code == 200
        assert s0.json()["sentence_text"] == "א"

        s1 = client.get(f"/v1/users/{user_a}/texts/{text_id}/sentences/1")
        assert s1.status_code == 200
        assert s1.json()["sentence_text"] == "ב\nשורה"

        s2 = client.get(f"/v1/users/{user_a}/texts/{text_id}/sentences/2")
        assert s2.status_code == 200
        assert s2.json()["sentence_text"] == "ג"

        cross = client.get(f"/v1/users/{user_b}/texts/{text_id}")
        assert cross.status_code == 404

        renamed = client.patch(f"/v1/users/{user_a}/texts/{text_id}", json={"title": "חדש"})
        assert renamed.status_code == 200
        assert renamed.json()["title"] == "חדש"

        deleted = client.delete(f"/v1/users/{user_a}/texts/{text_id}")
        assert deleted.status_code == 200

        after_delete = client.get(f"/v1/users/{user_a}/texts/{text_id}/sentences/0")
        assert after_delete.status_code == 404


def test_sentence_load_populates_never_seen_idempotently_and_nav(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        user_id = create_user(client)
        text_id = create_text(client, user_id, "T", "שָׁלוֹם 2026. שָׁלוֹם־לָכֶם Hello.")

        first = client.get(f"/v1/users/{user_id}/texts/{text_id}/sentences/0")
        assert first.status_code == 200
        data = first.json()
        assert data["prev_sentence_index"] is None
        assert data["next_sentence_index"] == 1
        assert {t["normalized_word"] for t in data["tokens"]} == {"שלום"}

        words = client.get(f"/v1/users/{user_id}/words").json()["items"]
        assert len(words) == 1
        assert words[0]["state"] == "never_seen"

        second_load = client.get(f"/v1/users/{user_id}/texts/{text_id}/sentences/0")
        assert second_load.status_code == 200
        words_after = client.get(f"/v1/users/{user_id}/words").json()["items"]
        assert len(words_after) == 1

        out_of_range = client.get(f"/v1/users/{user_id}/texts/{text_id}/sentences/99")
        assert out_of_range.status_code == 404

        negative = client.get(f"/v1/users/{user_id}/texts/{text_id}/sentences/-1")
        assert negative.status_code == 404


def test_word_state_update_filters_pagination_and_sort(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        user_id = create_user(client)
        text_id = create_text(client, user_id, "T", "אֶחָד. בֵּית. גִּימֵל.")
        client.get(f"/v1/users/{user_id}/texts/{text_id}/sentences/0")
        client.get(f"/v1/users/{user_id}/texts/{text_id}/sentences/1")
        client.get(f"/v1/users/{user_id}/texts/{text_id}/sentences/2")

        up1 = client.put(f"/v1/users/{user_id}/words/אחד", json={"state": "unknown"})
        assert up1.status_code == 200
        up2 = client.put(f"/v1/users/{user_id}/words/בית", json={"state": "known"})
        assert up2.status_code == 200

        first_updated = up2.json()["updated_at"]
        up2_same = client.put(f"/v1/users/{user_id}/words/בית", json={"state": "known"})
        assert up2_same.status_code == 200
        assert up2_same.json()["updated_at"] == first_updated

        unknowns = client.get(f"/v1/users/{user_id}/words?state=unknown").json()["items"]
        assert all(w["state"] == "unknown" for w in unknowns)

        paged = client.get(f"/v1/users/{user_id}/words?page=1&limit=2")
        assert paged.status_code == 200
        assert len(paged.json()["items"]) == 2

        invalid_page = client.get(f"/v1/users/{user_id}/words?page=0&limit=2")
        assert invalid_page.status_code == 400

        ordered = client.get(f"/v1/users/{user_id}/words").json()["items"]
        states = [w["state"] for w in ordered]
        assert states.index("unknown") < states.index("known")
        assert states.index("known") < states.index("never_seen")


def test_invalid_ids_return_typed_400_errors(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        user_id = create_user(client)
        create_text(client, user_id, "T", "שָׁלוֹם.")

        bad_user = client.get("/v1/users/not-a-uuid/texts")
        assert bad_user.status_code == 400
        assert bad_user.json()["error"]["message"] == "invalid_user_id"

        bad_text = client.get(f"/v1/users/{user_id}/texts/not-a-uuid")
        assert bad_text.status_code == 400
        assert bad_text.json()["error"]["message"] == "invalid_text_id"

        bad_meaning_id = client.delete(
            f"/v1/users/{user_id}/words/שלום/meanings/not-a-uuid"
        )
        assert bad_meaning_id.status_code == 400
        assert bad_meaning_id.json()["error"]["message"] == "invalid_meaning_id"


def test_text_progress_and_list_embedded_progress(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        user_id = create_user(client)
        text_id = create_text(client, user_id, "T", "שָׁלוֹם. בַּיִת.")

        before = client.get(f"/v1/users/{user_id}/texts/{text_id}/progress")
        assert before.status_code == 200
        assert before.json()["never_seen_count"] == 2

        client.put(f"/v1/users/{user_id}/words/שלום", json={"state": "known"})
        client.put(f"/v1/users/{user_id}/words/בית", json={"state": "unknown"})

        after = client.get(f"/v1/users/{user_id}/texts/{text_id}/progress")
        assert after.status_code == 200
        assert after.json()["known_count"] == 1
        assert after.json()["unknown_count"] == 1
        assert after.json()["never_seen_count"] == 0
        assert after.json()["known_percent"] == 50.0

        listed = client.get(f"/v1/users/{user_id}/texts")
        assert listed.status_code == 200
        assert listed.json()["items"][0]["progress"] == after.json()


def test_meanings_generate_list_delete_and_timeout_error(tmp_path: Path) -> None:
    generator = CountingGenerator()
    with make_client(tmp_path, generator=generator) as client:
        user_id = create_user(client)

        g1 = client.post(
            f"/v1/users/{user_id}/words/שלום/meanings/generate",
            json={"sentence_context": "שלום לך"},
        )
        assert g1.status_code == 200
        meaning_id = g1.json()["meaning_id"]

        g2 = client.post(
            f"/v1/users/{user_id}/words/שלום/meanings/generate",
            json={"sentence_context": "שלום עולם"},
        )
        assert g2.status_code == 200
        assert generator.calls == 2

        listed = client.get(f"/v1/users/{user_id}/words/שלום/meanings")
        assert listed.status_code == 200
        assert len(listed.json()["items"]) == 2
        assert generator.calls == 2

        deleted = client.delete(f"/v1/users/{user_id}/words/שלום/meanings/{meaning_id}")
        assert deleted.status_code == 200

        listed2 = client.get(f"/v1/users/{user_id}/words/שלום/meanings")
        assert len(listed2.json()["items"]) == 1

    with make_client(tmp_path / "timeout", generator=TimeoutGenerator()) as timeout_client:
        user_id = create_user(timeout_client)
        timeout = timeout_client.post(
            f"/v1/users/{user_id}/words/שלום/meanings/generate",
            json={"sentence_context": "שלום"},
        )
        assert timeout.status_code == 504
        assert timeout.json()["error"]["message"] == "meaning_generation_timeout"


def test_meaning_generation_enforces_english_and_normalizes_whitespace(tmp_path: Path) -> None:
    with make_client(tmp_path / "english", generator=WhitespaceEnglishGenerator()) as client:
        user_id = create_user(client)
        generated = client.post(
            f"/v1/users/{user_id}/words/שלום/meanings/generate",
            json={"sentence_context": "שלום"},
        )
        assert generated.status_code == 200
        assert generated.json()["meaning_text"] == "basic meaning"

    with make_client(tmp_path / "hebrew", generator=HebrewOutputGenerator()) as client:
        user_id = create_user(client)
        rejected = client.post(
            f"/v1/users/{user_id}/words/שלום/meanings/generate",
            json={"sentence_context": "שלום"},
        )
        assert rejected.status_code == 502
        assert rejected.json()["error"]["message"] == "meaning_generation_non_english"


def test_frontend_assisted_journey_rename_jump_pagination_and_state_updates(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        user_id = create_user(client, "Journey")
        text_id = create_text(
            client,
            user_id,
            "טיוטה",
            "שָׁלוֹם לָכֶם. הַבַּיִת גָּדוֹל. הַיֶּלֶד קוֹרֵא.",
        )

        renamed = client.patch(f"/v1/users/{user_id}/texts/{text_id}", json={"title": "סיפור מעודכן"})
        assert renamed.status_code == 200
        assert renamed.json()["title"] == "סיפור מעודכן"

        first_sentence = client.get(f"/v1/users/{user_id}/texts/{text_id}/sentences/0")
        assert first_sentence.status_code == 200
        assert first_sentence.json()["sentence_index"] == 0
        assert first_sentence.json()["next_sentence_index"] == 1

        jumped_sentence = client.get(f"/v1/users/{user_id}/texts/{text_id}/sentences/2")
        assert jumped_sentence.status_code == 200
        assert jumped_sentence.json()["sentence_index"] == 2
        assert jumped_sentence.json()["prev_sentence_index"] == 1
        assert jumped_sentence.json()["next_sentence_index"] is None

        out_of_range = client.get(f"/v1/users/{user_id}/texts/{text_id}/sentences/3")
        assert out_of_range.status_code == 404
        assert out_of_range.json()["error"]["message"] == "sentence_not_found"

        page_1 = client.get(f"/v1/users/{user_id}/words?page=1&limit=2")
        assert page_1.status_code == 200
        assert page_1.json()["page"] == 1
        assert page_1.json()["limit"] == 2
        assert len(page_1.json()["items"]) == 2
        assert page_1.json()["total"] >= 4

        page_2 = client.get(f"/v1/users/{user_id}/words?page=2&limit=2")
        assert page_2.status_code == 200
        assert page_2.json()["page"] == 2
        assert len(page_2.json()["items"]) >= 1

        normalized = first_sentence.json()["tokens"][0]["normalized_word"]
        updated = client.put(f"/v1/users/{user_id}/words/{normalized}", json={"state": "known"})
        assert updated.status_code == 200
        assert updated.json()["state"] == "known"

        known_words = client.get(f"/v1/users/{user_id}/words?state=known")
        assert known_words.status_code == 200
        assert any(item["normalized_word"] == normalized for item in known_words.json()["items"])

        progress = client.get(f"/v1/users/{user_id}/texts/{text_id}/progress")
        assert progress.status_code == 200
        assert progress.json()["known_count"] >= 1


def test_end_to_end_core_flow(tmp_path: Path) -> None:
    with make_client(tmp_path, generator=CountingGenerator()) as client:
        user_id = create_user(client, "End2End")

        text_id = create_text(client, user_id, "סיפור", "שָׁלוֹם לָכֶם. הַבַּיִת שֶׁלִּי.")

        load = client.get(f"/v1/users/{user_id}/texts/{text_id}/sentences/0")
        assert load.status_code == 200

        words = client.get(f"/v1/users/{user_id}/words?state=never_seen")
        assert words.status_code == 200
        assert len(words.json()["items"]) >= 1

        update = client.put(f"/v1/users/{user_id}/words/שלום", json={"state": "known"})
        assert update.status_code == 200

        word_list = client.get(f"/v1/users/{user_id}/words")
        assert word_list.status_code == 200

        progress = client.get(f"/v1/users/{user_id}/texts/{text_id}/progress")
        assert progress.status_code == 200

        gen = client.post(
            f"/v1/users/{user_id}/words/שלום/meanings/generate",
            json={"sentence_context": "שלום לכם"},
        )
        assert gen.status_code == 200

        delete = client.delete(f"/v1/users/{user_id}/words/שלום/meanings/{gen.json()['meaning_id']}")
        assert delete.status_code == 200
