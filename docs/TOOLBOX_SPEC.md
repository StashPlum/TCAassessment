# Kaizen toolbox implementation specification — 14 October 2026

The user's toolbox request authorizes the complete K1–K4 sequence and featurebranch push. Its archived development brief is not an approved CEVA policy. Existing U2/U3 program policy work remains separate; R2/R3 functionality is included here where requested.

## Architecture

Extend the existing Django application and one Kaizen record. Add input_profile and local_status without changing legacy profile/status/data/IDs. Legacy A4/A3/BP is methodological classification and cannot determine input complexity reliably. Existing events remain legacy until explicitly chosen. New profile/context fields use the existing partial autosave/revision contract. Local closure has its own source-visible checks; existing global verification and conditional stars remain intact.

A versioned method registry supplies schema, concise guidance, source, validation, calculations, SVG/table visualization and exports. Worksheets have stable row IDs, archived rows, structured payloads, worksheet/event revisions and restoration by creating a new revision. JSON is the complete archive, Excel is a safe secondary export, and diagrams use the same tested calculations. Statistical support is explicitly I–MR only for control charts; no other chart is advertised as implemented. DOE is planning only.

Private attachments retain bytes, hash, original name, stage, requirement and provenance. CSV/XLSX import has a persisted preview and explicit field mappings; confirmation validates all rows and event revision before writing. Adding a file never imports it automatically. No macro execution or formula evaluation.

Requirements coverage uses unique currently accepted Y under clause-level evidence checks. Baseline is a dated frozen snapshot. Pending claims do not increase coverage. Targeted assessor acceptance creates a dated traceable assessment version without marking a full section review. Frozen source/scope metadata accompanies new versions; historical legacy snapshots are untouched. Unknown exception arithmetic makes the denominator uncertain. Lowest-section local draft gates, CAT standing and frequency policy remain separate.

A3 preview and versioned PDFs reuse saved data. Report truncation points explicitly to the complete archive; report generation never changes methodological type or TCA. Learning entries require reviewed results, an authorized manager's explicit site sharing scope and transfer limits. Corporate sharing authority remains pending: this workflow is for the synthetic local pilot. Reuse copies approach/hypotheses only, never evidence, approvals, benefits or Y.

## Acceptance milestones

- K1: additive migration tested against an existing-record disposable backup; three suggested/selectable profiles; up/down switch preserves data; compact one-page and four-step/full guided paths; separate local/global/quality gates.
- K2: every catalog method has multiple meaningful structured fields, usable editor, save/reload/export; unlimited branching/categorization; autosave/conflicts/restore; calculations and diagrams independently checked.
- K3: 45/150 = 30%; events/pending/duplicates leave it unchanged; six unique reviewed approvals yield 51/150 = 34%; scoped access, immutable baseline, unknown/zero denominator, template comparison warning, no full-section clock reset; private files and import preview/confirmation.
- K4: versioned A3/complete archive, explicit learning sharing/adaptation, rendered desktop/mobile/PDF review, full regression and migration preservation, separate integrity/permission/classification audit, staged diff, featurebranch commit/push and remote verification when repository identity/credentials are available.

## Source and policy boundaries

Original workbooks remain byte-identical. Full source field register and ten criteria remain authoritative for wording. Missing User Guide, corporate sharing/RACI, response A, exceptions, frequency boundaries, CAT interface, approved template/brand and production SSO remain explicit. No money/time cutoff determines input size. Suggestions use process scope, recurrence and uncertainty and are advice only.
