# TCA Progress local pilot

This repository contains a local Django pilot. The immutable original workbooks, governance PDF and supplied Word brief belong in the ignored `sources/original/` directory; they are not distributed through Git. Older assessments retain unapproved `draft-v1` scoring; new assessments use the separately versioned, unapproved `advisory-v2` local rule. Local dated assessments are not official certification.

## Start the fictional demonstration on this Windows host

Open PowerShell in `C:\Users\stash\OneDrive\Documents\ChatGPT\tca` and run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_demo.ps1 -SkipInstall
```

The first run on another machine can omit `-SkipInstall` to install the pinned packages into `.vendor` from the standard Python registry. The script hashes and extracts the originals, migrates the local SQLite demo, imports the full catalog, creates fictional sites and accounts if absent, and binds the server to `127.0.0.1:8000`. Open `http://127.0.0.1:8000/login/` and sign in as `demo` with `LocalDemo2026!`. Stage 1 role views use `auditor_demo`, `manager_demo`, `sensei_demo`, and `team_demo` with the same local demonstration password. Select **Fictional Advisory Pilot** for the 5-response example with one amber Advisory. Change demonstration passwords before sharing a workstation. Seed commands do not reset existing passwords.

Optional configuration can go in an ignored `.env` file copied from `.env.example`. The startup script loads its `KEY=value` entries into the current process.

Suggested demonstration: **Fictional Toolbox Pilot** shows all three Kaizen input sizes, 45 structured Lean methods, a 34% (51/150) verified coverage example, six accepted evidence claims, versioned A3 reports and a controlled learning item. **Fictional Learning Recipient** shows a new draft adapted from that learning item without inherited measurements or approvals. The full official catalog remains searchable. All operational examples are fictional. On a fresh installation, run the command below once in a second PowerShell window after the initial seed, then reload the browser:

```powershell
$env:PYTHONPATH = (Resolve-Path '.vendor').Path
& $pythonExe manage.py seed_toolbox_demo
```

Set `$pythonExe` as shown under **Commands** below. The toolbox seed adds fictional records only and leaves existing records intact.

The UX upgrade uses four menu groups and an authorized country/site selector. The two fictional fixtures carry explicit NL/Benelux and UK metadata. The header shows the global baseline reference and local assessment version; governed template/profile assignment is the next upgrade milestone. [Governance interpretation](docs/GOVERNANCE_DELTA.md) and [current upgrade status](docs/STATUS.md) record the boundaries and checks.

The Kaizen workspace has participant drafts/autosave, four PDCA stages, sensei review, retained revisions, size suggestions, local closure and a searchable Lean toolbox. Open **Improvements → Kaizen events**, **Sensei review**, or a worksheet from an event. Original attachments are private and separate from a deliberate CSV/XLSX import preview. A3 PDFs, full archives and scoped learning are available locally. [Field/rule mapping](docs/KAIZEN_FIELD_RULES.md) keeps conditional source requirements explicit. [Final toolbox review](docs/TOOLBOX_REVIEW.md) records verified boundaries and deployment decisions.

The [19 October change register](docs/CHANGESET_2026-10-19.md) tracks every Word point and its stage. Stage 1 provides role-focused starts, site-question versions frozen into new assessments, and Y/A/N with traceable Advisory follow-up. Stage 2 adds the compact [design foundation](docs/DESIGN_SYSTEM.md), a clear Overview, Conduct filters and a clickable matrix. Select **Fictional Matrix Pilot** to inspect the complete 15×10 fictional answer set: 56 Y, 19 Advisory and 75 N. It shows 150/150 assessed and 75/150 accepted passes under the local `advisory-v2` rule, with CAT confirmation still pending. Click a cell for its frozen question, evidence, follow-up and linked work. Stage 3 adds versioned site documentation needs, selected/filter-wide evidence PDF/XLSX, staffing plans with manager availability and rescheduling history, three conduct views with autosave, and authorized historical PDF/XLSX exports. The fictional **Fictional Advisory Pilot** now has an additional draft v2 from browser verification; its approved v1 remains unchanged. Stage 4 adds title-only Kaizen start with input-view help, event teams and task assignment, a Gantt from the same actions, A3/BPK cause-analysis gates from the template, a compact sensei queue and review page with feedback per phase, and A3/A4 PDF plus Excel downloads. `team_demo`, `team_demo2` and `sensei_demo` see three fictional stage 4 events on **Fictional Advisory Pilot**. Stage 5 adds the learning repository by exact requirement ID with separate auditor best-practice validation, one evidence library with link-without-upload, reports and guidance with content-specific filters and export scope, and the prototype shell (header and navy sidebar). On **Fictional Matrix Pilot** the learning repository shows a fictional validated best practice for 4.C.3. All five stages are implemented locally; see `docs/STATUS.md` for checks and open decisions.

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
