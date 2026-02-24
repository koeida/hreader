# Mobile QA Reports

Use this folder for dated real-device sign-off reports.

Create a new report template:

```bash
.venv/bin/python scripts/new_desktop_qa_report.py
```

This creates `desktop-browser-qa-YYYYMMDD.md` with required checks for:
- Desktop Chromium
- Desktop Firefox
- Desktop WebKit

Or run the automated desktop matrix and write a filled report:

```bash
.venv/bin/python scripts/run_desktop_browser_qa.py --force
```

The automated pass also writes per-browser reader screenshots to:
- `docs/qa-reports/screenshots/desktop-chromium-YYYYMMDD-reader.png`
- `docs/qa-reports/screenshots/desktop-firefox-YYYYMMDD-reader.png`
- `docs/qa-reports/screenshots/desktop-webkit-YYYYMMDD-reader.png`

After filling the report and confirming PASS for all browsers, update the checklist automatically:

```bash
.venv/bin/python scripts/finalize_v1_checklist.py --report docs/qa-reports/desktop-browser-qa-YYYYMMDD.md
```
