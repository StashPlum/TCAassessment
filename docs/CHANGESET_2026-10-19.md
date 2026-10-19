# Word change register — 19 October 2026

Source: `sources/original/software aanpassingen.docx` (byte-for-byte local copy of the supplied Word file; SHA-256 `0CA93898C063F6BCE998051121B5D97593F517613A06E391FAD0A34DD7B8D59B`). The original is intentionally Git-ignored. Page references are to the five-page Word document; **image** means its embedded `word/media/image1.png`, the Site DIY Plan Summary matrix. Stage ownership and W IDs are checked against all 39 rows of `TCA_Verbeterplan_5_Etappes.md`. The plan has 39/39 Word points; no missing point was found. The incomplete sensei sentence on page 1 has no inferred authority. Criteria here are testable project interpretations, not new official CEVA obligations.

Status vocabulary: **Done E1** = implemented and checked in stage 1; **Part E1** = stage 1 foundation implemented, remaining criterion assigned to a later stage; **Pending** = later stage. Evidence for E1: 47 Django tests, 23 source-free CI tests, additive migration/record comparison, and browser captures in `docs/verification/`; see `STATUS.md` for commands and limits.

| ID | Word source | Change point and acceptance criterion | Stage | Status |
|---|---|---|---|---|
| W01 | p.1, roles | Four named roles each open a task-focused start page; server site rights match their duties. | 1, 2 | Done E1; visual refinement E2 |
| W02 | p.1, roles | Authorized users reach needed source/detail/history through role-appropriate links; restricted objects/downloads deny direct requests. | 1, 2, 5 | Part E1; final journey E5 |
| W03 | p.1, presentation | Approved CEVA tokens/assets where available, coherent business UI, no generic decoration. | 2, 5 | Pending E2 |
| W04 | p.1, presentation | Short header, consistent type/spacing/dropdowns and working click-throughs at all breakpoints. | 2, 5 | Pending E2 |
| W05 | p.1, Overview | Separate assessed/pass counters, local level, compact percentage with honest denominator and expandable explanation. | 1, 2, 5 | Part E1: semantics; compact visual E2 |
| W06 | p.2, Overview | Authorized locations block hidden while site selection and server authorization still work. | 2 | Pending E2 |
| W07 | p.2, Prepare evidence | Real selected-record XLSX and readable CEVA PDF include ID, obligation, evidence, owner and period. | 3 | Pending E3 |
| W08 | p.2, Prepare evidence | Auditor versions site documentation needs with provenance without changing the official requirement. | 1, 3 | Part E1: site evidence guidance; prep-list workflow E3 |
| W09 | p.2, Plan assessment | Manager confirms availability or proposes alternate/backup; conflicts, owner and late-change impact remain visible. | 3 | Pending E3 |
| W10 | p.2, Plan assessment | Low-friction scheduling with useful in-app prompts and traceable rescheduling. | 3, 4 | Pending E3 |
| W11 | p.2, Plan assessment | Auditor selects site and versions wording/evidence needs before starting; assessment freezes effective version. | 1, 3 | Part E1: editor/snapshot; integrated prep workspace E3 |
| W12 | p.2, Plan assessment | Actor, reason, diff and prior wording/assessment versions can be read after a change. | 1, 3 | Part E1: append-only versions; full history journey E3 |
| W13 | p.2, Plan assessment | New A is amber Advisory-pass only with evidence, note and follow-up; previous A highlighted and explicitly retested; old approvals unchanged. | 1, 3, 5 | Part E1: rule/retest/history; richer conduct UI E3 and final counts E5 |
| W14 | p.3, Conduct | Relevant latest assessment selected by default; started snapshot never silently changes. | 3 | Pending E3 |
| W15 | p.3, Conduct | Filter questions by section and evidence type without dropping saved responses. | 3 | Pending E3 |
| W16 | p.3, Conduct | All, section and single-question views show the same current data and preserve edits. | 3 | Pending E3 |
| W17 | p.3, Conduct | Auditor can save Y/A/N, conclusion, Advisory follow-up and evidence; stale writes fail. | 1, 3 | Part E1: rule and form; richer conduct journey E3 |
| W18 | p.3, History | Single or selected assessment PDF/XLSX contains frozen questions, answers, comments, evidence and follow-up. | 3 | Pending E3 |
| W19 | p.3, History | Year, site, version and auditor filters operate on authorized history. | 3 | Pending E3 |
| W20 | p.3, image | Clickable 15×10 standard matrix (or approved alternate scope), C/B/A bands, Y green/A amber/N red/blank neutral; cell links to full detail. | 2 | Pending E2 |
| W21 | pp.3–4, Kaizen | Small/Medium/Extensive choices keep source gates and use short optional guidance. | 4 | Pending E4 refinement |
| W22 | p.4, toolbox | Each Lean method has purpose, steps, inputs and a short logistics example from its working editor. | 4 | Pending E4 refinement |
| W23 | p.4, toolbox | Tool diagrams and exported labels remain legible for long and dynamic data. | 4 | Pending E4 refinement |
| W24 | p.4, Kaizen | Authorized team members collaborate on the same versioned event with visible ownership. | 4 | Pending E4 |
| W25 | p.4, Kaizen | Assign tasks to team members; each sees own work and edits without stale overwrite. | 4 | Pending E4 |
| W26 | p.4, Plan | Gantt uses the existing action dates/owners/progress and matches an accessible table. | 4 | Pending E4 |
| W27 | p.4, workflow | Routine journeys minimize duplicate administration while retaining mandatory source information. | 1–5 | Part E1: role-focused entry; full journey E5 |
| W28 | p.4, A3/A4 | Functional A3/A4 event difference follows approved source rules, independent of input size/report paper. | 4 | Pending E4; CEVA mapping open |
| W29 | p.4, Kaizen | Event, analyses, files, measures, tasks, revisions and review survive save/archive. | 4 | Pending E4 completion |
| W30 | p.4, reports | Authorized user downloads approved A3/A4 PDF and true XLSX from event/review for manual Teams storage. | 4 | Pending E4 |
| W31 | p.4, sensei | Compact queue and filters display status/result and link to complete review. | 4 | Pending E4 refinement |
| W32 | p.4, sensei | Most recent relevant submitted Kaizens appear first by default. | 4 | Pending E4 |
| W33 | p.4, sensei | Export one or selected queue events to PDF/XLSX with honest review state. | 4 | Pending E4 |
| W34 | p.4, Learning | Exact TCA requirement ID is the main content filter. | 5 | Pending E5 |
| W35 | p.4, Learning | Authorized cross-site lesson shows problem, method, outcome, sustainment and linked Kaizen. | 5 | Pending E5 |
| W36 | p.5, Learning | Best practice is separately validated and shows approver and route to result. | 5 | Pending E5 |
| W37 | p.5, Learning | Compact filters and spacing support overview and drill-down on narrow screens. | 5 | Pending E5 |
| W38 | p.5, Evidence | Same authorized evidence objects and provenance link across assessment, prep, Kaizen and reports. | 5 | Pending E5 |
| W39 | p.5, Reports/guidance | Content-relevant compact filters, reset, empty state and explicit export scope work together. | 5 | Pending E5 |

## Image and policy reconciliation

The embedded matrix shows 15 sections × 10 requirements, C(1–5)/B(6–8)/A(9–10) bands, red/amber/green cells, and 56 Y + 19 Advisory + 75 N. Its older Advisory legend describes work toward the standard. The **new Word text and direct user instruction** govern the new `advisory-v2` rule: 150 assessed, 75 pass if all acceptance gates hold, 19 open Advisory follow-ups. The screenshot's planned/confirmed site update markers are local actions, not official auditor answers. Prior `draft-v1` A remains unresolved and its approved score immutable. Corporate adoption of the new draft, CAT classification, exceptions, frequency and site-template authority remain separate decisions.

## Stage 1 permission and version decisions

All site objects and downloads continue through server-side site membership checks. The primary start-page priority for a multi-role user is auditor, manager, sensei, team member, administrator; actual grants are the union of assigned site roles. An auditor can write assessment answers and local site guidance, review claims, and read restricted site evidence/financial and participant details. A manager sees results and blockers, can approve a local snapshot and review claims. A sensei works in coaching/review. A team member works in Kaizens, tasks and finding-led starts. These are **local application rights**, never CAT authority. Existing manager/technical-admin assessment write rights remain for compatibility; the product must not call them official auditor certification rights. `core/roles.py` names the rights, while views, exports and downloads enforce their own role/site checks.

Local site question/evidence guidance is append-only, records actor/reason/diff, and overlays immutable global source clauses only in future assessment snapshots. Proposed official-obligation edits are stored inactive for a governed decision. Existing approved assessments retain their exact snapshots, rule versions, response decisions, and audit trail. A new assessment carries a frozen 150-item configuration and makes prior A due for explicit retest. Passing Advisory does not close its improvement or confer official classification.
