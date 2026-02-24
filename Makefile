.PHONY: venv install run test seed smoke

venv:
	python3 -m venv .venv

install:
	.venv/bin/pip install -r requirements.txt

run:
	.venv/bin/uvicorn app.main:app --reload

test:
	.venv/bin/pytest -q

seed:
	.venv/bin/python scripts/seed_sample_story.py

smoke:
	bash scripts/smoke.sh
