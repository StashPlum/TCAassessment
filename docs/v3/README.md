# TCA Progress 3.2 — redesign record

This folder is the stage memory for the isolated 3.2 redesign. Read it before any 3.2 work.

| File | Content |
|---|---|
| [00-isolation-baseline.md](00-isolation-baseline.md) | Old repo/Render reference, baseline SHA, new workspace, zero-impact checks |
| [01-current-state.md](01-current-state.md) | Current state, defects D1–D15, assumptions and blockers |
| [02-roles-and-rbac.md](02-roles-and-rbac.md) | Role-task-information matrix, RBAC matrix, negative-access probe |
| [03-screens-and-journeys.md](03-screens-and-journeys.md) | Screen inventory, journey baselines, Lean waste, feature preservation |
| [04-improvement-plan.md](04-improvement-plan.md) | Architecture decision, improvement records, phase plan |
| [05-acceptance-register.md](05-acceptance-register.md) | AC-01…AC-34 status with evidence |
| [06-new-environment.md](06-new-environment.md) | New GitHub/Render setup steps (no secrets) |
| [07-open-decisions.md](07-open-decisions.md) | Decisions and policy conflicts |
| `baseline/` | Baseline screenshots and raw crawl/probe output |

Re-run the baseline evidence: start the app locally with `TCA_DEMO_PASSWORD` set and `manage.py prepare_demo`, then `python tools/v3_role_crawl.py` and `python tools/v3_rbac_probe.py`.
- `08-quality-report.md`: phase 6 authorization, recovery, responsive and efficiency results.
