# Current-state assessment (Phase 1, deliverables 1–2)

Baseline `ab50e7f`. Evidence labels: **[L]** observed on a local run of the baseline in hosted-demo seed mode (synthetic catalogue, fictional seeds, throwaway SQLite); **[C]** read in code; **[D]** taken from existing docs, not re-verified; **[A]** assumption. Nothing was observed on the old Render URL: the build container cannot reach it.

## 1. What exists

Django 5.2.10 server-rendered app (one `core` app, 16 additive migrations, 36 models, 44 templates, one CSS file, five small JS files including HTMX). PostgreSQL via `DATABASE_URL` or SQLite locally. ReportLab PDFs, openpyxl XLSX. Gunicorn + WhiteNoise on Render free plan. 74 Django tests + 50 "source-free" CI tests [D]; **this run: source-free CI 50/50 passed; the full `manage.py test core` gives 1 failure + 9 errors because the private originals in `sources/original/` are absent** [L]. That is expected, but it means CI cannot prove catalogue fidelity.

Functional inventory (status per capability in 03-screens-and-journeys.md §Feature preservation): catalogue import with 15/150/494 counts, versioned site question wording, frozen assessment snapshots, Y/A/N with `draft-v1` and `advisory-v2` rules, cumulative C/B/A gates with lowest-section rule, evidence + clause coverage, planning sessions with manager availability, three conduct views, history PDF/XLSX, matrix, Kaizen with three input sizes and A4/A3/BPK types, 45 Lean methods, team/tasks/Gantt, sensei queue/review, A3/A4 PDF + XLSX, learning repository, best-practice validation, evidence library, reports.

## 2. Major defects and gaps (evidence-based)

| # | Finding | Evidence | Severity |
|---|---|---|---|
| D1 | **Official questions missing on the hosted demo.** `prepare_demo` loads the official catalogue only from an optional Render *secret file*; otherwise it seeds "SYNTHETIC demo requirement: official TCA wording is not loaded". The header shows "Baseline Not imported". The catalogue loads only into an empty database, so adding the file later needs a database rebuild. | [C] `prepare_demo.py`, `docs/DEPLOY_RENDER.md` step 5; [L] screenshot `baseline/auditor_demo-sites-…-assessment-1440.png` | P0 |
| D2 | **A Y or A answer cannot be saved in a draft** unless a conclusion and accepted evidence for every clause already exist. N saves. This blocks the auditor from recording answers live with site staff and contradicts "drafts are not completed records". | [L] POST Y/A without conclusion → form re-rendered with error (200), N → 302 | P0 |
| D3 | **New draft silently copies every prior answer and conclusion** (Y, N, A) from the previous version. Only A is marked "pending retest". Violates "never silently copy an old answer". | [C] `views.new_draft` lines 277–280; [L] draft v2 had 4 Y + 1 A immediately | P0 |
| D4 | **"Conduct assessment" opens the last approved, read-only version** when no draft exists. Starting a new assessment requires scrolling to the page bottom, typing a rationale and pressing "Create new version". | [L] auditor journey | P0 |
| D5 | **GET request can create an assessment**: `active_assessment()` creates version 1 when a site has none. Side effect on a read. | [C] `views.active_assessment` | P1 |
| D6 | **Single-question ("One question") view has no inline Y/A/N**; it links to a separate respond page with a radio list (Unanswered/Yes/No/Advisory), conclusion, follow-up, retest checkbox, Save / Save and next. | [L] | P0 (UX) |
| D7 | **Navigation is effectively the same for every role.** Team members see Site progress, TCA matrix, Prepare evidence, Plan assessment, Conduct assessment, Assessment history (12 items); auditor 13; manager/sensei 13. Only "Sensei review" and "Site question versions" differ. | [L] `baseline/crawl.json` | P1 |
| D8 | **Uploads are not durable on Render.** `FileSystemStorage` on the free plan's ephemeral disk; docs state files disappear on sleep/redeploy. | [C] settings; [D] DEPLOY_RENDER | P0 for production, P1 for pilot |
| D9 | **Free Render Postgres is deleted after its free period** [D]. Not acceptable for a pilot holding assessment history. | [D] | P1 |
| D10 | **Site managers hold `assessment_write` and `local_snapshot_approve`**, so the audited site's manager can answer and approve its own TCA assessment. Separation of duties is not enforced. | [C] `roles.RIGHTS`, `views.respond/approve` role lists | P1 — governance decision needed |
| D11 | **No administrator demo account; `/administration/` returns 404 for every demo role.** The admin experience cannot be demonstrated or tested. | [L] RBAC probe | P2 — fixed in phase 3 (`admin_demo`) |
| D12 | Evidence library overflows at 390 px for auditor/manager (document 587 px wide). | [L] crawl | P2 — fixed in phase 3 (absolute helpers escaped the scroll region) |
| D13 | Landing pages lead with a percentage/progress block rather than "what do I do next"; the auditor's next action ("Conduct assessment") lands on a locked record (see D4). | [L] screenshots | P1 |
| D14 | Prepare evidence screen shows ~1,060 words and 30 inputs at once; Lean toolbox ~700 words; matrix page ~565 words with 157 links. | [L] crawl metrics | P2 |
| D16 | **Every in-page `<nav>` is hidden below 760 px** (pagination, view tabs) by a leftover rule `body.js nav:not(.expanded){display:none}` written for the old top menu. Found while testing the 390 px Focus view. | [L] | P1 — fixed in phase 2 |
| D15 | Ordinary screens show technical metadata the master prompt asks to hide: "advisory-v2", "Assessment v1", "Baseline Not imported", "Code:" label, 64-character zero hash on the respond page. | [L] | P2 |

## 3. What works and must be preserved

Site isolation is solid: for all 5 single-role demo users, 15 site-scoped routes returned **404 on a site they are not a member of** and 200 on their own [L, `baseline/rbac_probe.json`]. Object routes (Kaizen detail, archive, Excel, PDF) on another site's object returned 404. Stale writes fail on revision checks [D, tests]. Approved snapshots are immutable [D, tests]. Scoring is versioned, cumulative per section with lowest-section aggregation [C `scoring.py`, `progress.py`]. Uploads are size/type checked (10 MB) and hashed [C `files.py`].

## 4. Architecture notes

- Business logic is partly in views (`views.py` 945 dense lines; role lists repeated per view). Permission model = `Membership(user, site, role)` + `roles.RIGHTS`, but most views check raw role lists rather than rights, so the two can drift.
- One stylesheet (`workspace.css`) and a design-token set already exist (docs/DESIGN_SYSTEM.md); the shell matches the v3 prototype.
- Recommended approach: **Option A/B** from the master prompt §20 — keep Django, models and tests; restructure templates and role navigation; move permission checks into one policy module; change the draft/answer rules in the domain layer. No rebuild is justified by the evidence.

## 5. Assumptions, missing information, blockers

| Type | Item |
|---|---|
| **Blocker** | New private GitHub repository does not exist and cannot be created from this session. |
| **Blocker** | New Render service, database and durable storage need the owner's Render account (and possibly a paid plan for a persistent disk or database). |
| Missing | Official assessment workbook and Kaizen template (`sources/original/`, not in Git). Needed for the official 150 questions on the new service. Expected on the owner's PC. |
| Missing | Demo password for the old service (only needed for live comparison; not needed for the new service, which gets its own). |
| Missing | The documents named in master prompt §4.1 that are not in Git: `software aanpassingen.docx`, governance PDF, Kaizen workbooks. Docs summarising them are in Git. |
| Assumption | `TCA_Demo` is the branch the old Render service deploys (from `render.yaml`; not confirmed in the dashboard). |
| Policy | See 07-open-decisions.md. |
