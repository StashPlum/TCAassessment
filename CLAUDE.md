# TCA Progress — Claude Code project instructions

Place this file in the repository root (next to `AGENTS.md`). Claude Code reads it at the start of every session. `AGENTS.md` stays as the historical Codex record; where they differ, this file governs work done with Claude Code.

## Source and integrity invariants
- Preserve `sources/original/` byte for byte. Regenerate inspectable records with `tools/extract_sources.py`; never save a workbook through openpyxl.
- Official requirement wording and IDs come from the assessment workbook: 15 sections, 150 requirements (75 C, 45 B, 30 A), 494 clauses. Keep supplemental explanations separate from official text.
- Response codes Y/A/N are separate from maturity codes C/B/A. Under `advisory-v2`, Y and Advisory A pass only with an assessor conclusion and accepted current evidence for every clause; A also needs an open follow-up and explicit retest at the next assessment. N fails. Historical `draft-v1` stays Y-only. Maturity A means Showcase.
- Approved assessment snapshots are immutable. Kaizen completion, a sensei review, a claim or another audit never sets a requirement to Y.
- Assessed, pass, open Advisory, local readiness and CAT standing are separate numbers. No local score implies CAT confirmation.
- Enforce site and role permissions on the server for every page, query, object, export and download. Hidden buttons are not authorization.
- Stale writes fail (revision check). Autosave shows success and failure.

## Working agreement
- Read `docs/PRODUCT.md`, `docs/CHANGESET_2026-10-19.md`, `docs/STATUS.md` and `docs/DESIGN_SYSTEM.md` before a stage. Read only what the current task needs.
- Stages 1–3 of `TCA_Verbeterplan_5_Etappes.md` are done. Continue with stage 4, then stage 5, as described in `CLAUDE_CODE_MASTER_PROMPT.md`.
- Use additive migrations. Use fictional fixtures only.
- Run `manage.py test core` and `tools/run_source_free_ci.py` after meaningful changes. Record only checks that actually ran in `docs/STATUS.md`.
- Visual reference: `design_handoff_tca_progress/prototype/TCA Progress Preview v3.dc.html`. Recreate it in the existing Django templates and HTMX. Do not ship the prototype HTML.

## Authorization boundaries
- Allowed: local code edits, pinned dependency installs, disposable migrations, tests, loopback demo, commits and a normal push to a feature branch of `StashPlum/TCAassessment` (for example `claude/stage-4-5`, branched from `codex/kaizen-toolbox`).
- Not allowed: force push, merge to `main`, deployment, publication, external messages, production data or credentials, committing originals, databases, uploads or secrets.

## Commands (from README)
```
python manage.py migrate --noinput
python manage.py import_catalog
python manage.py test core
python tools/run_source_free_ci.py
python tools/backup_restore.py backup backups/demo.sqlite3
python tools/backup_restore.py verify backups/demo.sqlite3
```
Use a Python supported by Django 5.2 (3.10–3.13). The Windows demo script is `scripts/start_demo.ps1`; the server binds to `127.0.0.1:8000`.
