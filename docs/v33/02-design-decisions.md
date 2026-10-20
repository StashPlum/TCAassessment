# 3.3 design decisions

## Architecture decisions

| # | Decision | Reason | Consequence |
|---|---|---|---|
| D1 | Extend the existing Django + HTMX app; no new frontend stack | Keeps 3.2 RBAC, autosave, revision checks and exports | All new screens are server-rendered templates |
| D2 | `CatalogueVersion` + `TCAGroup`; `Requirement` gains catalogue, question_id, master_order, section_label, groups, source_record | Group variants need their own rows. Legacy requirements keep `catalogue = null` | Additive migration `0017`. Legacy assessments are untouched |
| D3 | Variant key `QuestionID~n`, plus a version letter for later catalogues | `Requirement.code` is the primary key and the response/evidence foreign key. A separate row per variant keeps every existing join working | People only ever see the QuestionID |
| D4 | Scope is frozen at creation (`baseline_scope(site)` → `scope_snapshot.requirements`) | Activating a new version must not rewrite open or approved assessments | Each site page reads its scope through `catalogue.assessment_requirements` / `working_requirements` |
| D5 | An unmapped site raises a blocker; no default group | The group decides the official wording (master prompt hard rule) | An admin maps the site after a preview and a confirmation. The mapping is audited |
| D6 | Lettered parts are shown as clauses; the exact full text is always shown | The evidence policy needs units. The wording must not be paraphrased or split in a way that loses text | Plain-language help is never generated |
| D7 | Evidence is attached from the focus canvas (`attach_evidence`) | It was the largest context switch in the auditor journey | Same checks as the library: type/size/content, site and role, classification, expiry, and a reason for acceptance |

## Design system additions (`core/static/core/v33.css`)

- **Typography**
  - Inter (SIL Open Font License, served by Google Fonts) with a system fallback stack.
  - Scale: 12 / 13 / 14 / 16 / 18 / 22 / 28 px. Body text is 16 px, and long requirement text has a 1.55 line height.
- **Tokens**
  - Status colours for Y / Advisory / N / unanswered / blocked are reused from `workspace.css`.
  - Every coloured state also has a text label or letter, so colour is never the only signal.
- **Components**
  - Journey rail; page heading with status pill; view bar (Focus / Section / All); `qc-layout` focus canvas.
  - Answer segment (Y/A/N radio group); save-state line; evidence panel; section rail and map cells; next-action card; blocker panel.
  - Visual components: ladder table, timeline, pipeline, dumbbell, PDCA journey.
- **Responsive**
  - Single column below 900 px. The rail becomes a horizontal strip.
  - No page overflow at 1440 / 1024 / 768 / 390 px. The e2e test checks this for the focus view, and the role start pages were checked at 390 px.

## Visualisation decision matrix (VIS-35…38)

| Role | Decision it supports | Visual | Data source and denominator | Drill-down | Accessible alternative |
|---|---|---|---|---|---|
| Auditor | Where to continue; what is still open | Section heatmap (15 × 10 cells, Y/A/N/open) | Responses of the open draft, against its frozen 150-code scope | Cell opens that question in Focus | Each cell has text (QuestionID + state); counts are shown as text |
| Site manager | Which section holds the site back | Maturity ladder (C 1–5, B 6–8, A 9–10 gates per section) | Accepted passes from the latest assessment (`accepted_codes`, `category_result`); denominator = positions in scope | "See blockers in the matrix" | Table with n/total text per gate |
| Site manager | What is late | Action timeline (due dates, today line) | Open `Opportunity` with due date + unfinished `KaizenAction` | Each row links to the action or event | Ordered list with due dates under the chart |
| Sensei | What to review next | Review pipeline (draft → finalised) | Saved review state per Kaizen | Event links in each column | Counts and titles as text |
| Sensei | Did the result move | Before/after dumbbell per measure | `Observation` pairs with the same measure and unit | Event link | "Before 60 After 96" text; a missing "after" means the result is not yet verified |
| Team member | Where is my improvement in PDCA | PDCA journey | Saved Kaizen status | Opens the Kaizen | Step labels with done/current state |

The following are left out on purpose:
- No trend lines or targets, because none are stored.
- No comparison of sites that use different catalogue versions or groups.
- The "lowest section" flag is shown only when that section stands out. If most sections share the lowest level, the flag is noise.

Existing visuals are kept: the results matrix, section results and the Lean toolbox diagrams. The previous manager KPI tiles were replaced by the ladder, because the tiles did not show where the site is blocked.

## Journeys (UX-31, UX-34)

| Journey step | 3.2 | 3.3 |
|---|---|---|
| Answer Y/A/N | 1 selection (autosave) | 1 selection (autosave) — measured |
| Attach evidence to the open question | separate Evidence library page, then back to the assessment | in place, from the question's evidence panel. The answer is kept after attaching (measured) |
| Go to the next open question | scroll or use the section list | 1 click on "Next open question" (measured) |
| Resume after logout | not measured | the assessment opens on the next open question (measured) |
| Wrong group / unmapped site | no group concept; one global catalogue | blocker with the recovery action (measured) |

"Measured" means the step is checked in `tools/v33_auditor_e2e.py` (22/22). The 3.2 column describes the screens of the previous version. The 3.2 interaction counts were not re-measured in a browser, so UX-34 stays Implemented-unverified.
