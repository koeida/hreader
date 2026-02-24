# Mobile QA Reports

Use this folder for dated real-device sign-off reports.

Create a new report template:

```bash
.venv/bin/python scripts/new_mobile_qa_report.py
```

This creates `mobile-real-device-YYYYMMDD.md` with required checks for:
- iOS Safari
- Android Chrome

After filling the report and confirming PASS for both devices, update the checklist automatically:

```bash
.venv/bin/python scripts/finalize_v1_checklist.py --report docs/qa-reports/mobile-real-device-YYYYMMDD.md
```
