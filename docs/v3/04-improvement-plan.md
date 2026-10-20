# Prioritised improvement plan and architecture decision (deliverables 8–11)

## Architecture decision (ADR-v3-001)

**Decision:** Option B — keep Django 5.2, the `core` domain models, migrations and the existing test suites; restructure templates/navigation per role; extract permissions into one policy module; change the draft-answer domain rules. No new frontend framework.

**Why:** the baseline already enforces site isolation, immutable snapshots, revision checks and versioned scoring, with 124 automated tests. Every P0 defect (D1–D4, D6) is a rule or flow fault inside existing modules, not a framework limit. A rebuild would risk the audited rules for no measured gain.

**Migration implications:** additive migrations only; `advisory-v2` stays; a new answer state is added rather than redefining old codes. **Rollback:** each phase is a tagged commit in the new repository; database backup before every migration in the new environment.

## Improvement records (in execution order)

| ID | Problem → change | Roles / screens | Preserve | Security / data | Risk | Acceptance |
|---|---|---|---|---|---|---|
| P2.1 | D1: load the official catalogue on the new service from a private file, idempotently, with count/ID reconciliation (15/150/494, 75/45/30) and a visible failure if counts differ | Auditor; all | Exact wording, hashes, versions | Workbook never in Git; stored as a Render secret file | Medium: file size limits | AC-10 |
| P2.2 | D2: a draft accepts Y/A/N/Unanswered with one selection; the pass rule (conclusion + accepted evidence, Advisory follow-up) is checked at approval and shown as "evidence pending" | Auditor / Focus view | `advisory-v2` meaning of a pass; `draft-v1` history | Server-side validation at approve | Medium: counters must not count pending as pass | AC-07, AC-08, AC-11, AC-18 |
| P2.3 | D3: a new draft starts unanswered; the previous answer, comment and Advisory note show as read-only context; Advisory retest stays explicit | Auditor | Old snapshot unchanged | — | Low | AC-16 |
| P2.4 | D4/D5: "Start assessment" creates a draft in one click (POST); "Continue" opens the draft at the next unanswered question; no object creation on GET | Auditor landing, Conduct | Planned session link | CSRF POST | Low | AC-03, journey 1 |
| P2.5 | D6: Focus view (default) with inline Y/A/N, comment, evidence attach, Previous/Next, autosave and conflict message; Section and All views edit the same records | Auditor | Revision checks | Same endpoint, same validation | Medium | AC-12, AC-13, AC-15 |
| P2.6 | Matrix: 15×10 grouped C/B/A, text+colour cells, blockers for next level, cell drill-down | Auditor, Manager | Existing matrix logic | Site scope | Low | AC-17 |
| P3.1 | D7: role navigation and landing pages from the role-task matrix; one policy module drives both menu and server checks | All | Server checks stay authoritative | Route tests per role | Medium | AC-01, AC-02, AC-03 |
| P3.2 | D10: separation of duties for answering/approval — **only after decision O3** | Manager, Admin | — | — | Governance | AC-02 |
| P3.3 | D11: admin demo account and Administration landing | Admin | — | Least privilege | Low | AC-01 |
| P3.4 | D12–D15: shell, filters, tables at 1440/1024/768/390; remove technical metadata from operational screens | All | Design tokens | — | Low | AC-23, AC-24 |
| P4.x | Kaizen/PDCA, guided Lean tools, Sensei queue as landing, A3/A4 checks | Team, Sensei | Stage 4–5 work | Team-edit rules | Low–Medium | AC-19…AC-21 |
| P5.x | Prepare evidence (progressive disclosure), planning folded into start flow, history filters, learning, reports | Auditor, Manager | Exports | Restricted evidence | Low | AC-14, AC-25, AC-26 |
| P6 | Tests: negative POST/mutation matrix per role, autosave failure, conflict, visual + viewport checks, efficiency comparison | — | — | — | — | AC-02, AC-06, AC-09, AC-22, AC-24 |
| P7 | Deploy to the new Render service only; verify SHA, migrations, smoke tests, old environment unchanged | — | — | Isolation | Owner-dependent | AC-27, AC-30…AC-34 |

## Phase plan

| Phase | Content | Gate |
|---|---|---|
| 0 | Isolation + baseline (this document set) | New repository exists and holds the baseline |
| 1 | UX/product architecture (02, 03, this file) | Owner has seen the plan and open decisions |
| 2 | TCA vertical slice P2.1–P2.6 | All tests green; auditor journey 1 measured; screenshots |
| 3 | Shell + role experiences P3.x | Role crawl shows role-specific navigation; RBAC tests |
| 4 | Lean/Kaizen P4.x | Kaizen end-to-end test |
| 5 | Remaining modules P5.x | Export checks |
| 6 | Quality P6 | Acceptance register complete |
| 7 | Isolated deployment P7 | AC-27, AC-31…AC-34 verified |

## Phase status

| Phase | Status | Evidence |
|---|---|---|
| 0 | Done (with recorded deviation O7) | 00-isolation-baseline.md |
| 1 | Done | 01–03, 05 |
| 2 | P2.2–P2.5 done; P2.1 (official catalogue on Render) waits for the owner's secret file; P2.6 (matrix) done in phase 3 | `core/test_v32_assessment.py` (6 tests); source-free CI 56/56; `tools/v3_auditor_journey.py` → `docs/v3/phase2/` |
| 3 | P2.6, P3.1, P3.3 and part of P3.4 done: matrix marks next-level blockers (text `!` plus outline) and evidence-pending answers (`*`), shows the approved record to non-auditors with a version switch; role navigation from `core/policy.py`, role start pages with one next step, admin demo account, plain header, 390 px overflow fixed. P3.2 waits for decision O3 | `core/test_v32_roles.py` (3 tests), matrix test in `core/test_v32_assessment.py`; CI 60/60; `docs/v3/phase3/` |

Phase 2 journey 1 measured in the browser: menu → Start new assessment → Y = **3 deliberate clicks**, 0 mandatory inputs, 2 screens (baseline: 5 clicks, 1 mandatory input, 4 screens plus an evidence detour).
| 4 | P4.1 Kaizen workspace: one primary action ("Save and go to <next stage>", or "Submit for sensei review" only once every review gate is met, otherwise the missing count and the next item); status change and local closure moved into a disclosure, closure disabled with its reasons. P4.2 Lean toolbox for beginners: question-first chooser. P4.3 Sensei landing = review queue (done in phase 3). Kaizen table no longer widens the page at 390 px | `core/test_v32_roles.py`; CI 61/61; `docs/v3/phase4/` |
| 5 | Prepare evidence leads with "N of 150 requirements still need complete evidence" and a filter for incomplete evidence; filters, exports and the export selection are folded away. Planning opens the proposal form when nothing is planned. History: plain rule labels, single version preselected, role-correct header action. Reports and learning kept (no defects found in the crawl) | `core/test_v32_assessment.py`; CI 63/63; `docs/v3/phase5/` |
