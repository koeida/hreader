from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.main import create_app


if __name__ == "__main__":
    db_path = Path("data/hreader.db")
    app = create_app(str(db_path))

    sample_path = Path("data/sample_story_he_nikkud.txt")
    story = sample_path.read_text(encoding="utf-8")

    with TestClient(app) as client:
        user_resp = client.post("/v1/users", json={"display_name": "Demo User"})
        user_resp.raise_for_status()
        user_id = user_resp.json()["user_id"]

        text_resp = client.post(
            f"/v1/users/{user_id}/texts",
            json={"title": "סִיפּוּר קָצָר לְתַרְגּוּל", "content": story},
        )
        text_resp.raise_for_status()

    print(f"Seeded DB at {db_path}")
    print(f"User ID: {user_id}")
    print(f"Text ID: {text_resp.json()['text_id']}")
