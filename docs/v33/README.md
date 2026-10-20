# TCA Progress 3.3: V3 catalogue and guided workspace

Stage memory for 3.3. It builds on 3.2 (`docs/v3/`). Read this file before doing any 3.3 work.

| File | Content |
|---|---|
| [01-reconciliation.md](01-reconciliation.md) | V3 source facts, import procedure, reconciliation result (no official wording) |
| [reconciliation-report.json](reconciliation-report.json) | Machine report: counts, QuestionIDs, row numbers, groups, observations. Contains no requirement text |
| [02-design-decisions.md](02-design-decisions.md) | Architecture decisions, data model, design system, visualisation matrix, journeys |
| [03-acceptance-register.md](03-acceptance-register.md) | AC-01…AC-34 deltas and V3-01…LIVE-40 with evidence |
| [04-isolation-and-deployment.md](04-isolation-and-deployment.md) | Branch deviation, protected refs, Render Blueprint and secret-file steps, handover |

## What changed in 3.3

- **Source**
  - The importer reads the private V3 workbook, or its JSON extract, read-only.
  - The first numbered row of a record starts it. Each following row continues columns I/J/K.
  - The importer checks counts, groups and positions. Every check must pass before it stores anything.
- **Versioning**
  - Each import is a `CatalogueVersion`, keyed by the source's SHA-256.
  - Only one version is active at a time.
  - An assessment freezes its resolved requirement codes when it is created. Activating a later version never changes an existing assessment.
- **Groups**
  - Each site is mapped to one `TCAGroup` of the active version. Only an administrator can map it, after a preview and a confirmation, and the mapping is audited.
  - An unmapped site cannot start an assessment and gets a blocker with a recovery message. The app never falls back to a default group.
- **Exact wording**
  - The text of each variant is stored exactly as it appears in the source.
  - Lettered parts (`A.)`, `B.)`…) are shown as evidence units, but the full text stays intact in `detail_text`.
  - The evidence statement and the explanation are stored and shown as separate fields.
- **Guided workspace**
  - Journey rail (prepare, plan, conduct, review, results).
  - Question focus canvas, with Y/A/N in one selection.
  - Evidence can be attached and accepted from the question itself.
  - "Next open question" control, and a section map/rail that stays in sync across the Focus, Section and All views.
- **Role start pages**
  - Auditor: section heatmap.
  - Manager: maturity ladder and action timeline.
  - Sensei: review pipeline and before/after outcome checks.
  - Team member: PDCA journey and their own timeline.
  - All role pages keep the separate "Assessed / Meets local rule / Open Advisory / CAT" panel.

## Commands

```
python manage.py import_v3_catalogue --source "V3assessment .xlsx" --dry-run --report /tmp/v3-report.json
python manage.py import_v3_catalogue --source "V3assessment .xlsx" --activate --operator "<name>"
python tools/extract_v3_source.py "V3assessment .xlsx" /outside/the/repo/tca-v3-source.json
TCA_V3_SOURCE="V3assessment .xlsx" python manage.py prepare_demo
python tools/run_source_free_ci.py                      # 74 tests, synthetic data only
TCA_V3_SOURCE="V3assessment .xlsx" python tools/v33_auditor_e2e.py     # needs a fresh demo DB and a running server
TCA_V3_SOURCE="V3assessment .xlsx" python manage.py shell < tools/v33_export_check.py
```

Never commit the following:
- the workbook or its JSON extract
- screenshots of the focus canvas, because they show official wording
- databases or uploads

Screenshots are kept in the project files folder `tca-v33/screenshots/`, not in git.
