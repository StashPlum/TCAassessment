# Handoff: TCA Progress — assessment and Kaizen UI (stages 4–5)

## Overview
TCA Progress helps CEVA sites assess 150 TCA requirements (15 sections, 494 clauses), see exact blockers, prepare evidence, run Kaizen PDCA events and share learnings. The working app is a Django 5.2 + HTMX pilot in `StashPlum/TCAassessment`, branch `codex/kaizen-toolbox` (stages 1–3 done). This package carries the visual and interaction target for the remaining stages 4 and 5 and for refinements of earlier screens.

Start with `CLAUDE_CODE_MASTER_PROMPT.md` (kickoff for Claude Code) and `CLAUDE.md` (put in the repo root).

## About the design files
The files in `prototype/` are **design references created in HTML**: a clickable prototype with synthetic data, showing intended look and behaviour. They are not production code. Recreate them in the existing Django templates, shared CSS from `docs/DESIGN_SYSTEM.md` and HTMX. Business rules, permissions and data live on the server, as the repo already does.

Open `prototype/TCA Progress Preview v3.dc.html` through a local web server (for example `python -m http.server` in `prototype/`); it loads `data/*.json` with fetch. The yellow demo bar switches role (team member, site manager, TCA auditor, sensei), navigation (sidebar/top bar) and data state (full, empty, loading, error). NL/EN switch is in the header.

## Fidelity
High-fidelity for layout, hierarchy, states and interactions. Colours and type are provisional CEVA-aligned values: no approved CEVA font or brand rules were supplied. Reconcile tokens with `docs/DESIGN_SYSTEM.md` and record the outcome there.

## Screens / views
Shell: 64 px white header (logo, app name "TCA Progress", site picker with search over authorized sites, assessment version "Assessment v2 · advisory-v2 · CAT-bevestiging open", user, NL/EN). Navy (#0B1A48) sidebar 256 px with groups Mijn werk, TCA, Kaizen, Kennis & bewijs, Rapporten, Beheer (hidden for team member); active item has a 3 px #E4002B left border. Below 900 px the sidebar becomes a drawer. Main content max-width 1240 px, padding 28/32 px desktop, 20/16 px mobile. Page header: 12 px uppercase kicker (#4B5265, letter-spacing .1em), H1 Barlow Condensed 600 36 px #0B1A48, 14 px context line.

1. **Home (per role)**: one "Volgende actie" card (blueprint frame with corner marks, red 8 px square marker, title 28 px, primary 48 px navy button + secondary outline). Site manager adds four readiness metrics, a 15-tile Certified gate grid and a blockers table. Panels per role below in an auto-fit grid (min 320 px).
2. **TCA matrix**: filters (section, level band, search, status chips Y/A/N/—, more filters: owner, linked Kaizen only), active filter chips, 15 rows × 10 cells of 40×40 px in bands Certified 1–5, Advanced 6–8, Showcase 9–10, section level column. Cell colours: Y #2F7D45/white, A #F0B43C/#2E1F00, N #B3261E/white, — #E3E6EC/#3E4556; always with letter. Non-matching cells drop to 18% opacity. Click opens requirement detail.
3. **Requirement detail**: all official clauses (ordered list), expected evidence, remote method, reasoning with source address, latest assessment with rule explanation and three facts (question version, clauses with accepted evidence, Advisory follow-up), evidence list, history with rule versions, linked Kaizens, "Kaizen starten", "Learnings voor <ID>".
4. **Bewijs voorbereiden**: four stat tiles (in scope, missing, outdated, present) acting as filters; section filter, search; table (Req, requirement + expected evidence + remote method, status tag + select, owner, request button); bulk request; CSV/XLSX export of the filtered set.
5. **Assessment plannen**: 6-week weekday calendar (5 columns, 68 px cells) showing manager unavailability (#FDF1F0), auditor busy, scheduled for this site, selected (navy). Auditor form: date, section chips 1–15, full/clear, auditor, validation messages, schedule button. Site manager clicks days to change availability and confirms or proposes the next free alternative date; auditor accepts it and the old date is kept. Frequency rules 186/368 days with status tags.
6. **Assessment uitvoeren**: scope switch (planned sections or full 15 sections / 150 questions), evidence-type filter (remote method), save indicator, view switch Overview / By section / Focus. Progress tiles per section. Overview: table with inline Y/A/N buttons (40×36), previous answer, "Hertest" tag, status. By section: 300 px side list + detail. Focus: detail with previous/next and Y/A/N/arrow shortcuts. Detail: one checkbox per clause "evidence accepted", conclusion (min 10 characters), three large answer buttons, gate text, Advisory note. Submit is disabled until every item is complete. Read-only banner for non-auditors.
7. **Assessmenthistorie**: filters year, site, version, auditor; table with select checkbox, Y/A/N stacked bar, CAT status; export selection or all.
8. **Siteversies van vragen**: section and requirement select; read-only source wording; version list (active, source v1); new version form (local note ≥10 characters, reason ≥5) for auditor and site manager; frozen-assessment note.
9. **Nieuwe Kaizen**: title only required (counter /75 with Excel warning), input view Small/Medium/Extensive with "Help mij kiezen", methodological type A4/A3/BP, owner, optional specific problem. Confirmation screen with PDCA strip.
10. **Kaizen-events**: cards with ID, status tag, title, requirement, four-segment PDCA bar (done navy, current red, final all green), gate count.
11. **PDCA-werkplek**: header with requirement link, chips, autosave revision, one primary "next missing item" button; four PDCA step buttons with gate counts; phase fields; actions as table or Gantt (same data, red today line); before/after comparison; "Nog nodig voor review" checklist (12 gates from `core/kaizen.py`); toolbox suggestions per phase; team; A3/archive card; sensei feedback banner when returned.
12. **Sensei-review**: queue with status filters, recent first, CSV export; detail as described in the master prompt.
13. **Learning repository**: filters requirement ID, section, method, search; cards with result and best-practice tag; detail with problem/cause/countermeasure/sustainment, before/after bars, best-practice validation (sensei only), adopt and A3.
14. **A3**: landscape sheet, header with logo, two columns of numbered blocks (1 problem, 2 cause, 3 countermeasure | 4 actions, 5 result with bars, 6 sustainment), footer with methods.
15. **Lean-toolbox**: PDCA stage filter with counts, kind, search; 45 method cards; sticky detail with purpose, steps, pitfall (amber), example, fields, source.
16. **Evidence-bibliotheek** (W38): three status tiles (accepted, to review, expired), filters requirement, section, type, status, owner, search, reset; table with ID, title/type/owner/date/validity/classification, requirement chips (open requirement detail), linked Kaizen, status, and "link without new upload" (requirement select + Link; linking an already linked requirement shows a no-duplicate message). CSV export of the filtered set.
17. **Rapporten en richtlijnen** (W39): content type switch Assessments / Kaizens / Richtlijnen; only relevant filters per type, first three visible and the rest behind "Meer filters"; reset; live export-scope line (rows + active filters); empty state with reset; CSV export.

Added in the PDCA workspace (W24–W26, W30): team list with "Lid toevoegen"; "Nieuwe taak" form (description, owner from team, phase, start, end; end ≥ start) that writes to the same action list used by the table and Gantt; progress select per action; team member home shows "Mijn taken" computed from those actions. A3 view and sensei review offer "PDF · A3 liggend" (print with @page A3 landscape, chrome hidden) and a real XLSX (sheets A3/Event, Acties, Gates).

## Interactions & behaviour
- Autosave: 700–800 ms after a change shows "Opslaan…" (amber), then "Opgeslagen · revisie n".
- Validation: errors are listed in a red alert with links to fields; inputs keep values.
- Site switch with an unsaved Kaizen draft opens a dialog: stay, switch without saving, save and switch.
- Empty, loading (skeleton blocks #E3E6EC) and error (red bordered card with retry) states exist for home and matrix.
- Toasts: navy, bottom centre, 4.5 s.
- Role rules shown in the UI must also be enforced on the server: only auditor writes answers; only sensei reviews and validates best practice; manager edits availability; team member has no administration.
- Tables scroll inside their own region at 390 px; no page-level horizontal scroll.

## State management
Server-side models already exist for most of this (see `core/models.py`). Prototype state that maps to new or changed server data: per-event team and task assignment, review comments per phase and decision, best-practice validation, schedule confirmation status and alternate date, answer per clause acceptance, assessment scope (planned vs full).

## Design tokens (prototype)
- Navy #0B1A48 (nav, headings, primary), hover #1C2F70; ink #14182B; muted #4B5265; accent marker #E4002B.
- Lines #D8DBE3, #C3C8D4, #E6E8EE, #EEF0F3; canvas #F3F4F7; tint #E8EBF4, #F3F5FA, #F7F8FA.
- Status Y #2F7D45 / soft #E2F1E6 / text #1D5A30; A #F0B43C / #FDF0D3 / #6B4300; N #B3261E / #F9E1DF / #8E1D17; unassessed #E3E6EC / #3E4556.
- Type: Barlow Condensed 600 for headings, numbers and buttons; Barlow 400/500 body 15 px, small 13/12 px.
- Spacing 4, 6, 8, 12, 16, 20, 24, 32 px. Square corners. Controls 40–48 px high. Shadow only on popovers/dialogs: 0 12px 32px rgba(11,26,72,.18).
- Focus: 2 px navy outline, 2 px offset (white on navy).

## Assets
- `prototype/assets/ceva-logo.png`: logo supplied by the user; confirm brand usage before production.
- Icons: thin-stroke inline SVG (1.5 px), Lucide style.
- `prototype/data/tca-catalog.json`: extracted from the user's assessment workbook (Sheet1!A4:E626); the repo's `import_catalog` remains the authority.
- `prototype/data/toolbox.json`: subset of the repo's `docs/toolbox-catalog.json`.

## Files
- `CLAUDE.md`: Claude Code project instructions for the repo root.
- `CLAUDE_CODE_MASTER_PROMPT.md`: kickoff, stage 4 and 5 scope, verification.
- `prototype/TCA Progress Preview v3.dc.html` + `support.js` + `_ds/` + `data/` + `assets/`: the reference prototype.
