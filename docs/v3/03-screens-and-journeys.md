# Screens, journeys and waste (Phase 1, deliverables 4, 5 and 7)

## 1. Screen inventory (baseline, measured)

Measured with `tools/v3_role_crawl.py` at 1440×900 as `auditor_demo` on Fictional Advisory Pilot [L]. Words = visible words in `<main>`. Full per-role data: `docs/v3/baseline/crawl.json`.

| Screen | Route | Words | Inputs | Links | 390 px fits | Primary purpose | Main problem | Target |
|---|---|---|---|---|---|---|---|---|
| Overview (role home) | `/` | 97–234 | 0–4 | 15–21 | ✓ | Role start | Leads with % block; next action unclear (D13) | One "next action" card + exception list per role |
| Site progress | `/sites/x/` | 579 | 0 | 145 | ✓ | Section results | Duplicates matrix; 145 links | Merge into Assessment results |
| TCA matrix | `/sites/x/opportunities/` | 565 | 12 | 157 | ✓ | 15×10 matrix + local work | Matrix and opportunity form on one page | Matrix only; opportunities on drill-down |
| Prepare evidence | `/evidence/preparation/` | 1,062 | 30 | 56 | ✓ | Checklist + export | Densest screen; everything visible | Section accordion; export in toolbar |
| Plan assessment | `/sessions/` | 81 | 9 | 5 | ✓ | Sessions | OK; separate from start | Fold into "Start assessment" flow |
| Conduct assessment | `/assessment/` | 607 | 6 | 33 | ✓ | Answer questions | Opens approved locked version (D4); no inline answer in one-question view (D6) | Focus view default with inline Y/A/N |
| Respond | `/assessment/respond/<id>/` | ~400 | 4 | ~15 | ✓ | One answer | Y/A blocked without evidence (D2); hash and "Code:" shown (D15) | Merged into Focus view |
| Assessment history | `/assessment/history/` | 128 | 5 | 4 | ✓ | Versions + export | OK | Keep; filters per §16 |
| Site question versions | `/assessment/configuration/` | 589 | 1 | 33 | ✓ | Local wording | Fine for auditor; should not be in main nav | Under Assessment → Settings |
| Kaizen events | `/kaizen/` | 171–176 | 0 | 11–13 | ✓ | List | OK | "My Kaizens" first for team |
| Sensei review | `/kaizen/review/` | 112 | 4 | 8 | ✓ | Queue | OK, compact | Sensei landing |
| Learning repository | `/learning/` | 283 | 6 | 6 | ✓ | Search by requirement | OK | Keep |
| Evidence library | `/evidence/` | 162–176 | 7–21 | 14 | **✗ 587 px** | Archive | Overflow at 390 (D12) | Fix table wrapper |
| Lean toolbox | `/toolbox/` | 702 | 2 | 53 | ✓ | 45 method help | Long list | Search-first, collapsed |
| Reports and guidance | `/resources/` | 184 | 5 | 10 | ✓ | Reports | OK | Keep |

The 20-point per-screen record (§10 of the master prompt) is completed screen by screen during Phases 2–5 as each screen is rebuilt, so it describes the new screen and its acceptance test rather than the old one.

## 2. Journey baselines and targets

Counts are from the local baseline walkthrough [L]; "nav" = page navigations the user starts, "sel" = deliberate clicks/selections excluding typing, "in" = mandatory text inputs.

| # | Journey | Baseline | Target | Main waste |
|---|---|---|---|---|
| 1 | Auditor: start a new assessment and answer first question Y | nav 4 · sel 5 · in 1 (conclusion) · screens 4 · **plus** a detour to the evidence screen to accept clause evidence before Y can save | nav 1 · sel 2 (Start, Y) · in 0 · screens 2 | Locked version opens first; hidden create button; Y gated at draft time |
| 1b | Auditor: resume draft at next unanswered | nav 2 · sel 3 (Conduct, One question, Answer) | nav 1 (Continue card) · sel 0 | No "next unanswered" pointer |
| 4 | Answer next question | sel 2 (Save and next, then pick answer on new page) + page reload | sel 1 (answer) + 1 (Next), no reload | Separate respond page |
| 6 | Reassess a previous Advisory | Old answer pre-copied into new draft (D3) — the auditor may never notice | Previous answer shown as context; new answer required | Silent copy = error opportunity |
| 7 | Kaizen from a finding | matrix cell → detail → Start Kaizen: nav 3 | nav 2 | Acceptable |
| 11 | Team member submits Kaizen | [D] stage 4 workspace, title-only start | keep | — |
| 12 | Sensei review | landing → queue → review: nav 2 | landing is the queue: nav 1 | Extra hop |

Targets meet the "start/resume within three deliberate navigation actions" and "one selection per Y/A/N answer" goals. Remaining journeys (2, 3, 5, 8–10, 13–15) are measured when their screens are rebuilt.

## 3. Lean waste summary

| Waste | Where | Cause | Remedy | Verification |
|---|---|---|---|---|
| Motion | Conduct → respond → back | One answer per page | Focus view with inline answer + autosave | Journey 4 count |
| Over-processing | Y needs evidence before draft save | Pass rule enforced at save time | Record answer in draft; enforce evidence at approval; show "evidence pending" | AC-07/AC-08 tests |
| Defects | Copied prior answers | Draft cloning | No copy; prior answer as context | AC-16 test |
| Searching | Same 12–13 nav items for all roles | Shared menu | Role navigation from §1 of 02-roles-and-rbac.md | AC-01 crawl |
| Waiting | Official questions missing until DB rebuild | Secret-file-only catalogue load | Load official catalogue at deploy from private storage; reconcile counts | AC-10 |
| Inventory | Prepare evidence 1,062 words | No progressive disclosure | Section accordion, summary counts | Word count drop |

## 4. Feature preservation register (for AC-28)

All capabilities listed in master prompt §2 exist in code at `ab50e7f` [C]. Status per capability: **working** — catalogue import, site question versions, Y/A/N storage, scoring rules, frozen snapshots, history export, evidence/coverage, planning sessions, matrix, Kaizen profiles, PDCA, 45 Lean tools, team/tasks/Gantt, sensei review, A3/A4 PDF/XLSX, learning, best practice, reports, site permissions, exports, uploads (local). **Defective** — draft answer recording (D2), reassessment copying (D3), conduct entry point (D4), durable uploads on Render (D8), official catalogue on Render (D1). **Missing** — administrator demo/experience (D11), role-specific navigation (D7).
