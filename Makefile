.PHONY: venv install install-browser install-browser-desktop run test seed smoke smoke-local visual-qa desktop-qa

venv:
	python3 -m venv .venv

install:
	.venv/bin/pip install -r requirements.txt
	$(MAKE) install-browser

install-browser:
	.venv/bin/playwright install chromium

install-browser-desktop:
	.venv/bin/playwright install chromium firefox webkit

run:
	.venv/bin/uvicorn app.main:app --reload

test:
	.venv/bin/pytest -q

seed:
	.venv/bin/python scripts/seed_sample_story.py

smoke:
	bash scripts/smoke.sh

smoke-local:
	bash scripts/smoke_local.sh

visual-qa:
	.venv/bin/python scripts/capture_ui_screenshots.py

desktop-qa:
	.venv/bin/python scripts/run_desktop_browser_qa.py --force
