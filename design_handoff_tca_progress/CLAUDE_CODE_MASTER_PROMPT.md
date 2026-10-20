# TCA Progress — Claude Code master prompt

This replaces `TCA_Progress_Codex_Master_Prompt.md` for work done with Claude Code. The product rules in that file, `docs/PRODUCT.md` and `TCA_Verbeterplan_5_Etappes.md` still apply; only the tool and the remaining scope change.

## Setup
1. Clone `StashPlum/TCAassessment` and check out `codex/kaizen-toolbox` (stages 1–3, K1–K4 and R1 are implemented there; `main` only contains `.gitattributes`).
2. Create a branch: `git switch -c claude/stage-4-5`.
3. Copy `CLAUDE.md` from this package to the repository root and copy the folder `design_handoff_tca_progress/` into the repository (it is a design reference, not app code).
4. Put the originals in the ignored `sources/original/`: `TCA assessment work categorisation.xlsx`, `Global_Kaizen_Template_20241219.xlsx`, `software aanpassingen.docx`, the governance PDF.
5. Start Claude Code in the repository root and give the kickoff instruction.

Kickoff:
> Read CLAUDE.md and design_handoff_tca_progress/CLAUDE_CODE_MASTER_PROMPT.md. Execute stage 4, verify, update docs/CHANGESET_2026-10-19.md and docs/STATUS.md, commit and push the feature branch. Then execute stage 5 the same way. Use the prototype in design_handoff_tca_progress/prototype as the visual and interaction reference for every screen you touch. Do not stop after a plan.

Resume:
> Read CLAUDE.md, docs/STATUS.md and docs/CHANGESET_2026-10-19.md. Check the real repository state, continue the first unfinished W item of the current stage, repair failures, and update the status.

## Role
Act as lead developer and product designer for TCA Progress, a Django 5.2 + HTMX app (server-rendered, PostgreSQL target, SQLite local demo). Assessment integrity is more important than visual polish or feature count.

## Stage 4 — Kaizen, team, Gantt, A3/A4, sensei review (W21–W33)
Follow "Prompt 4" in `TCA_Verbeterplan_5_Etappes.md`. Acceptance per W item is in `docs/CHANGESET_2026-10-19.md`. Prototype screens to follow: **Nieuwe Kaizen**, **Kaizen-events**, **PDCA-werkplek**, **Lean-toolbox**, **Sensei-review**, **A3**.
- W21: Small/Medium/Extensive as three compact choices with one help line, plus an optional "Help mij kiezen" panel (process scope, recurrence, known cause → suggestion). Input view stays separate from methodological type (A4/A3/BP) and report format. No Small=A4 mapping.
- W22/W23: every Lean method opens a help panel with purpose, steps, pitfall, logistics example and fields (data from `docs/toolbox-catalog.json`). Diagrams keep legible labels for long and dynamic data.
- W24/W25: team members per event with roles; assign actions/tasks to members; each member sees their own tasks on the home page; stale edits fail.
- W26: Gantt in Plan/Do built from the same action records (owner, start, end, progress, today line), with an equivalent accessible table toggle. No second plan store.
- W28: A3 vs A4 differ functionally per the Kaizen source rules; record open CEVA interpretations instead of guessing.
- W29/W30: the full event (analyses, files, measures, tasks, revisions, review) survives save and archive. Download A3/A4 PDF and a real XLSX from the event and from sensei review.
- W31–W33: compact queue with small status filters, most recently submitted first, visible review status and gate count, links to detail; PDF/XLSX export of one or selected events. The prototype shows the review layout: changes since previous review, gate checklist, before/after comparison, feedback per PDCA phase, "Terugsturen met feedback" (requires at least one comment) and "Finaliseren en A3 maken" (requires all gates). Returned feedback shows in the team workspace.

## Stage 5 — Learning, evidence, reports, full journey (W34–W39, plus W02–W05, W13, W27 final)
Follow "Prompt 5" in `TCA_Verbeterplan_5_Etappes.md`.
- W34: exact TCA requirement ID is the first learning filter; the requirement detail page links to "Learnings voor <ID>".
- W35/W36: lesson cards show problem, approach, result (before → after), sustainment, methods and linked Kaizen. Best practice is a separate validation with approver, date and how it was achieved; a closed event never gets it automatically. Adopting creates a new linked draft without copied approvals, evidence, measures or TCA answers.
- W37: compact filters and spacing at 390 px.
- W38: one evidence library using the same evidence objects as assessment, preparation, Kaizen and reports; filters by requirement, section, site, type, period, owner, status; no duplicate uploads when linking.
- W39: reports and guidance with content-relevant compact filters, reset, empty state and explicit export scope.
- Full journey for auditor, site manager, sensei and team member, then the counter check: 56 Y + 19 A + 75 N → 150/150 assessed, 75/150 pass, 19 open Advisory.

## Prototype behaviours to keep while touching earlier screens
These are in the prototype and must keep working, or be added where the repo lacks them:
- Conduct assessment offers the planned scope and a full 150-question / 494-clause scope; filters by section, status (open, Advisory retest, complete) and evidence type (remote method); three synchronized views; Y/A/N keys and arrow keys in focus view.
- Each clause has its own "evidence accepted" control; Y/A gate text states what is missing.
- Planning: site manager confirms or proposes the next free alternative date; auditor accepts the alternative and the old date is retained; 186/368-day rule status.
- Requirement detail shows all clauses, expected evidence, remote method, reasoning and source address.

## Verification (mandatory)
Run the Django suite and source-free CI; add tests for team/task rights, Gantt/table parity, profile and type switches without data loss, A3/A4 rules, attachments, queue sort, every download route, learning adoption without inherited data, evidence de-duplication and cross-site denial. Inspect rendered pages at 1440, 1024 and 390 px next to the prototype for hierarchy, alignment, density and focus states. Open generated PDFs and XLSX and compare with the event. Record actual results only.

## Finish
Report what works, checks run with results, open business decisions (CAT, advisory-v2 adoption, A3/A4 mapping, sharing authority, SSO/PostgreSQL/storage), branch, commit SHA and CI link. No main merge or deployment.
