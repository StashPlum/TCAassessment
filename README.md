# TCA Progress local pilot

This repository contains a local Django pilot. The immutable original workbooks and governance PDF belong in the ignored `sources/original/` directory; they are not distributed through Git. The current cumulative scoring policy is unapproved draft v1. Local dated assessments are not official certification.

## Start the fictional demonstration on this Windows host

Open PowerShell in `C:\Users\stash\OneDrive\Documents\ChatGPT\tca` and run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_demo.ps1 -SkipInstall
```

The first run on another machine can omit `-SkipInstall` to install the pinned packages into `.vendor` from the standard Python registry. The script hashes and extracts the originals, migrates the local SQLite demo, imports the full catalog, creates the fictional site and account if absent, and binds the server to `127.0.0.1:8000`. Open `http://127.0.0.1:8000/login/` and sign in as `demo` with `LocalDemo2026!`. Change the demonstration password before sharing a workstation. The seed command does not reset an existing password.

Optional configuration can go in an ignored `.env` file copied from `.env.example`. The startup script loads its `KEY=value` entries into the current process.

Suggested demonstration: **Fictional Toolbox Pilot** shows all three Kaizen input sizes, 45 structured Lean methods, a 34% (51/150) verified coverage example, six accepted evidence claims, versioned A3 reports and a controlled learning item. **Fictional Learning Recipient** shows a new draft adapted from that learning item without inherited measurements or approvals. The full official catalog remains searchable. All operational examples are fictional. On a fresh installation, run the command below once in a second PowerShell window after the initial seed, then reload the browser:

```powershell
$env:PYTHONPATH = (Resolve-Path '.vendor').Path
& $pythonExe manage.py seed_toolbox_demo
```

Set `$pythonExe` as shown under **Commands** below. The toolbox seed adds fictional records only and leaves existing records intact.

The UX upgrade uses four menu groups and an authorized country/site selector. The two fictional fixtures carry explicit NL/Benelux and UK metadata. The header shows the global baseline reference and local assessment version; governed template/profile assignment is the next upgrade milestone. [Governance interpretation](docs/GOVERNANCE_DELTA.md) and [current upgrade status](docs/STATUS.md) record the boundaries and checks.

The Kaizen workspace has participant drafts/autosave, four PDCA stages, sensei review, retained revisions, size suggestions, local closure and a searchable Lean toolbox. Open **Improvements → Kaizen events**, **Sensei review**, or a worksheet from an event. Original attachments are private and separate from a deliberate CSV/XLSX import preview. A3 PDFs, full archives and scoped learning are available locally. [Field/rule mapping](docs/KAIZEN_FIELD_RULES.md) keeps conditional source requirements explicit. [Final toolbox review](docs/TOOLBOX_REVIEW.md) records verified boundaries and deployment decisions.

## Commands

For commands below, set Python and project imports in PowerShell first:

```powershell
$pythonExe = 'C:\Users\stash\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$env:PYTHONPATH = (Resolve-Path '.vendor').Path
```

```powershell
& $pythonExe manage.py migrate --noinput
& $pythonExe manage.py import_catalog
& $pythonExe manage.py test core
& $pythonExe tools/run_source_free_ci.py
& $pythonExe tools/backup_restore.py backup backups/demo.sqlite3
& $pythonExe tools/backup_restore.py verify backups/demo.sqlite3
& $pythonExe tools/benchmark.py
```

The `verify` command restores into a **separate** SQLite file and checks integrity and catalog counts. It does not replace the live database. For a shared PostgreSQL installation, set `PGDATABASE`, `PGUSER`, `PGPASSWORD`, `PGHOST`, and `PGPORT` before migration. PostgreSQL 14+ is supported by the chosen Django version, but this host has no PostgreSQL server, so its connection, backup, and restore remain unverified. Planned PostgreSQL backup command: `pg_dump -Fc -f backup.dump tca_progress`; restore into a disposable database with `pg_restore --clean --if-exists -d tca_restore backup.dump`, then run source count and journey checks. Have IT review and test these commands in the approved environment.

## Boundaries

- Django 5.2.10, psycopg 3.2.10, and openpyxl 3.1.5 are pinned in `requirements.txt`. [Django 5.2 is an LTS release and supports PostgreSQL 14+](https://docs.djangoproject.com/en/5.2/releases/5.2/).
- The local demonstration uses SQLite because PostgreSQL is absent on this host. Shared development and pilot need PostgreSQL validation.
- Development login is confined to localhost. Startup with `TCA_DEBUG=0` is blocked until a corporate OIDC adapter and secure deployment settings are implemented.
- Exports are operational archives, not formula-compatible replacements for the Global Kaizen workbook. `AUTO_UPLOAD` is a legacy mapping, not an integration.
- See `docs/STATUS.md` for what is verified and what remains, `docs/SOURCE_MAP.md` for exact source mapping, and `docs/PRODUCT.md` for business rules.
