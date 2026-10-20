# Acceptance register (deliverable 12)

Status vocabulary: Not started / Implemented-unverified / Verified / Failed / Blocked. "Verified" needs evidence named in the last column.

| ID | Check | Component | Status | Evidence |
|---|---|---|---|---|
| AC-01 | Role navigation | P3.1 | Failed (baseline) | crawl.json: same menu for all roles |
| AC-02 | Technical RBAC | policy module, tests | Implemented-unverified (baseline GET probe passed cross-site; POST matrix pending) | rbac_probe.json |
| AC-03 | Role landing | P2.4, P3.1 | Implemented-unverified (auditor start/continue only; other roles phase 3) | test_v32: start page per role |
| AC-04 | Screen purpose | all screens | Not started | |
| AC-05 | Progressive disclosure | P3.4, P5 | Not started | |
| AC-06 | Poka-Yoke | P2.2, P6 | Implemented-unverified (approval completeness, stale write 409, read-only roles) | test_v32_assessment |
| AC-07 | Draft preservation | P2.2 | Verified (assessment drafts; Kaizen drafts already autosave) | test_v32 `draft_saves_any_answer…`; browser: Y/A/N kept after reload and logout/login |
| AC-08 | Submission rules | P2.2 | Verified | test_v32 `approval_lists_what_is_missing…`: blocked with 4 actionable messages, then accepted |
| AC-09 | Error recovery | P2.5 | Implemented-unverified (409 and network failure keep the entry on screen; induced-failure browser test pending) | |
| AC-10 | Official catalogue | P2.1 | Blocked (originals not available to the build) | |
| AC-11 | Y/A/N | P2.2 | Verified | Y, A, N and clear each save with one selection (test + browser) |
| AC-12 | Input views | P2.5 | Verified | Focus/Section/All in test_v32 and browser journey (phase2/*.png) |
| AC-13 | Synchronisation | P2.5 | Verified | Focus and Section answers appear in All after logout/login (phase2/journey.json) |
| AC-14 | Evidence | P5, O1 | Durability blocked by decision O1 (free plan); linkage/access to be verified in P5 | |
| AC-15 | Autosave | P2.5 | Implemented-unverified (refresh, logout/login, conflict verified; induced save failure in browser pending) | phase2/journey.json |
| AC-16 | Advisory | P2.3 | Verified | test_v32 `new_draft_copies_nothing…`: no carry-over, prior Advisory shown, retest recorded, v1 snapshot unchanged |
| AC-17 | Matrix | P2.6 | Not started | |
| AC-18 | Maturity | scoring tests | Implemented-unverified (existing tests) | |
| AC-19 – AC-21 | Guided tools, diagrams, PDCA | P4 | Not started | |
| AC-22 | Efficiency | 03 §2 | Baseline measured | 03-screens-and-journeys.md |
| AC-23 – AC-24 | Visual system, responsive | P3.4 | Partly verified: Focus and Section 390 px wide at 390; in-page navs visible on mobile again (D16); evidence library overflow open | phase2/06,07 |
| AC-25 – AC-26 | Exports, history | P5 | Not started | |
| AC-27 | New deployment SHA | P7 | Blocked (owner creates the Render Blueprint, see 06) | |
| AC-28 | Regression / feature preservation | 03 §4 | Baseline register made | |
| AC-29 | First-use clarity | heuristic walkthrough | Not started (real-user test outstanding) | |
| AC-30 | Recovery / provenance | 00 | Implemented-unverified | baseline tag, history copied |
| AC-31 | Old repo protected | 00 | Deviation O7 (same repository). `TCA_Demo` and `main` unchanged, checked with ls-remote after each push | 00-isolation-baseline.md |
| AC-32 | Old Render protected | — | Implemented-unverified (no action taken; dashboard check by owner) | |
| AC-33 | Data isolation | P7 | Not started | |
| AC-34 | No cutover | — | Verified at Phase 0 (no action taken) | |
