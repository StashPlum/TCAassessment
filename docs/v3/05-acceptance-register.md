# Acceptance register (deliverable 12)

Status vocabulary: Not started / Implemented-unverified / Verified / Failed / Blocked. "Verified" needs evidence named in the last column.

| ID | Check | Component | Status | Evidence |
|---|---|---|---|---|
| AC-01 | Role navigation | P3.1 | Verified | `core/policy.py`; test_v32_roles `navigation_is_role_specific`; phase3/crawl.json (team 5, sensei 6, auditor 11, manager 12 items; baseline 12–13 for all) |
| AC-02 | Technical RBAC | policy module, tests | Verified | test_v32_rbac: 52 site routes × GET/POST refused for a multi-role user of another site with no data change; role matrix for team, sensei and auditor; control run for members; 08-quality-report §1 |
| AC-03 | Role landing | P3.1 | Verified | test_v32_roles `each_role_start_page_names_one_next_step`; phase3/*-landing-1440.png |
| AC-04 | Screen purpose | all screens | Not started | |
| AC-05 | Progressive disclosure | P3.4, P5 | Verified for Prepare evidence, Kaizen workspace, toolbox, matrix and conduct filters: one next-step card first; filters, exports and export selection in disclosures (Prepare evidence: ~1,060 → 780 words, 25 selection checkboxes hidden until asked for) | test_v32 `prepare_evidence_leads_with_what_is_missing`; phase5/metrics.json |
| AC-06 | Poka-Yoke | P2.2, P4, P6 | Verified | approval lists what is missing; stale write 409; read-only roles refused (test_v32_rbac); Kaizen submit/closure disabled with reasons (test_v32_roles) |
| AC-07 | Draft preservation | P2.2 | Verified (assessment drafts; Kaizen drafts already autosave) | test_v32 `draft_saves_any_answer…`; browser: Y/A/N kept after reload and logout/login |
| AC-08 | Submission rules | P2.2 | Verified | test_v32 `approval_lists_what_is_missing…`: blocked with 4 actionable messages, then accepted |
| AC-09 | Error recovery | P2.5 | Verified | Induced connection loss: "Not saved", entry kept, saved after reconnect (phase6/quality.json) |
| AC-10 | Official catalogue | P2.1 | Blocked (originals not available to the build) | |
| AC-11 | Y/A/N | P2.2 | Verified | Y, A, N and clear each save with one selection (test + browser) |
| AC-12 | Input views | P2.5 | Verified | Focus/Section/All in test_v32 and browser journey (phase2/*.png) |
| AC-13 | Synchronisation | P2.5 | Verified | Focus and Section answers appear in All after logout/login (phase2/journey.json) |
| AC-14 | Evidence | P5, O1 | Durability blocked by decision O1 (free plan); linkage/access to be verified in P5 | |
| AC-15 | Autosave | P2.5 | Verified | refresh, logout/login, conflict (phase 2) and induced failure (phase 6) |
| AC-16 | Advisory | P2.3 | Verified | test_v32 `new_draft_copies_nothing…`: no carry-over, prior Advisory shown, retest recorded, v1 snapshot unchanged |
| AC-17 | Matrix | P2.6 | Verified | test_v32 `matrix_marks_next_level_blockers…` (blockers from accepted answers, evidence-pending marker, blocker/pending filters, approved version for managers and draft for auditors, same count on the manager start page); phase3/manager_demo-matrix-{1440,1024,768,390}.png, no horizontal page overflow |
| AC-18 | Maturity | scoring tests | Implemented-unverified (existing tests) | |
| AC-19 – AC-21 | Guided tools, diagrams, PDCA | P4 | AC-19 Verified for the chooser: 8 plain-language questions lead to 2–3 methods in order (`core/lean_guide.py`), on the site toolbox and the event toolbox; Kaizen workspace shows one primary action per stage and explains why sensei submission and local closure are not yet available. AC-20/21: existing diagrams and PDCA gates kept (stage 4 tests) | test_v32_roles `kaizen_offers_one_primary_action…`; phase4/*.png, kaizen_toolbox.json (no overflow at 390) |
| AC-22 | Efficiency | 08 §4 | Verified (measured comparison) | 08-quality-report.md §4 |
| AC-23 – AC-24 | Visual system, responsive | P3.4, P6 | Responsive verified: all menu targets for 5 roles at 1024/768/390, no page overflow (147 loads). Visual regression against the prototype not run | phase6/quality.json |
| AC-25 – AC-26 | Exports, history | P5 | Implemented-unverified: existing PDF/XLSX/CSV export tests (stage 3/5) pass; history shows the rule in plain words, preselects a single version, shows Conduct only to auditors. Export content check per role in phase 6 | test_v32 `history_and_planning_speak_plainly…` |
| AC-27 | New deployment SHA | P7 | Blocked (owner creates the Render Blueprint, see 06) | |
| AC-28 | Regression / feature preservation | 03 §4 | Baseline register made | |
| AC-29 | First-use clarity | heuristic walkthrough | Not started (real-user test outstanding) | |
| AC-30 | Recovery / provenance | 00 | Implemented-unverified | baseline tag, history copied |
| AC-31 | Old repo protected | 00 | Deviation O7 (same repository). `TCA_Demo` and `main` unchanged, checked with ls-remote after each push | 00-isolation-baseline.md |
| AC-32 | Old Render protected | — | Implemented-unverified (no action taken; dashboard check by owner) | |
| AC-33 | Data isolation | P7 | Not started | |
| AC-34 | No cutover | — | Verified at Phase 0 (no action taken) | |
