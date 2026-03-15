#!/usr/bin/env python3
"""
Usage: python scripts/seed_latin_texts.py <user_id>
Seeds the given user's account with sample Latin texts.
"""
import sys
import httpx

TEXTS = [
    {
        "title": "Caesar — De Bello Gallico I.1",
        "language": "latin",
        "content": (
            "Gallia est omnis divisa in partes tres, quarum unam incolunt Belgae, aliam Aquitani, "
            "tertiam qui ipsorum lingua Celtae, nostra Galli appellantur. "
            "Hi omnes lingua, institutis, legibus inter se differunt. "
            "Gallos ab Aquitanis Garumna flumen, a Belgis Matrona et Sequana dividit."
        ),
    },
    {
        "title": "Cicero — In Catilinam I.1",
        "language": "latin",
        "content": (
            "Quo usque tandem abutere, Catilina, patientia nostra. "
            "Quam diu etiam furor iste tuus nos eludet. "
            "Quem ad finem sese effrenata iactabit audacia."
        ),
    },
    {
        "title": "Phaedrus — Lupus et Agnus",
        "language": "latin",
        "content": (
            "Ad rivum eundem lupus et agnus venerant, siti compulsi. "
            "Superior stabat lupus, longeque inferior agnus. "
            "Tunc fauce improba latro incitatus iurgii causam intulit."
        ),
    },
    {
        "title": "Vulgate — Ioannes 1:1-3",
        "language": "latin",
        "content": (
            "In principio erat Verbum, et Verbum erat apud Deum, et Deus erat Verbum. "
            "Hoc erat in principio apud Deum. "
            "Omnia per ipsum facta sunt, et sine ipso factum est nihil quod factum est."
        ),
    },
]

BASE = "http://127.0.0.1:8000"


def seed(user_id: str) -> None:
    for text in TEXTS:
        r = httpx.post(f"{BASE}/v1/users/{user_id}/texts", json=text)
        r.raise_for_status()
        print(f"Seeded: {text['title']}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/seed_latin_texts.py <user_id>")
        sys.exit(1)
    seed(sys.argv[1])
