# TCA Progress 3.2 — isolation and baseline record

Recorded 20 October 2026 (Phase 0). No secrets in this file.

## Old environment (read-only reference — must stay unchanged)

| Item | Value | How verified |
|---|---|---|
| Old repository | `https://github.com/StashPlum/TCAassessment` (private) | `git ls-remote` on 20 Oct 2026 |
| Branches at baseline | `main` @ `a6af62675b7c15dd0f561608239581dc319031c5`, `TCA_Demo` @ `ab50e7f55b610e8c23eb2a58401654667a0a4dbb`, `codex/kaizen-toolbox` @ `50927b4102cab42c6124c703349ba217b690c4fb` | `git ls-remote` |
| Open/closed PR refs | `refs/pull/1` (head `50927b4`), `refs/pull/2` (head `ab50e7f`) | `git ls-remote` |
| Tags | none | `git ls-remote` |
| Render deploy branch | `TCA_Demo` (from `render.yaml`: service `tca-progress-demo`, database `tca-progress-demo-db`, Frankfurt, free plan) | file content at `ab50e7f` |
| Old live URL | `https://tca-progress-demo.onrender.com/` | **Not reachable from the build container** (egress proxy refuses the host). Live inspection therefore not performed; see 01-current-state.md |
| Local uncommitted work | Unknown. The user's Windows working copy (`C:\Users\stash\OneDrive\Documents\ChatGPT\tca`) was not reachable during Phase 0. It was not touched. | device bridge offline |

## Baseline chosen

`TCA_Demo` @ `ab50e7f` (19 Oct 2026 15:41 +0200), because it is what the old Render service deploys and it contains stages 1–5 plus the hosted-demo mode. Full history (19 commits, roots `a6af626` and `f3fbd8b`) was copied. Tag in the new workspace: `baseline-v3.1-ab50e7f`.

## New workspace

| Item | Value |
|---|---|
| Working directory | separate cloud workspace `tca-v3` (new `git init`, history fetched from a read-only clone) |
| Remotes | **none** until the new private repository exists; then `origin` = new repository only |
| Old clone | push URL set to `DISABLED-read-only-baseline`, so a push cannot target the old repository |
| Development branch | `development` |
| New GitHub repository | **BLOCKED — not yet created.** This session is not allowed to create repositories; the owner must create an empty private repository (proposed `StashPlum/tca-progress-v3-redesign`). |
| New Render service | **Not created.** Needs the owner's Render account; see 06-new-environment.md |

## Zero-impact checks to repeat before handover (AC-31…AC-34)

1. `git ls-remote https://github.com/StashPlum/TCAassessment` returns exactly the SHAs above.
2. Old Render service: owner confirms in the Render dashboard that `tca-progress-demo` still deploys `TCA_Demo` @ `ab50e7f`, with no new deploy, restart or setting change after 20 Oct 2026.
3. The new workspace has exactly one remote, pointing at the new repository.
4. No environment variable in the new Render service references the old database, old service or old domain.
