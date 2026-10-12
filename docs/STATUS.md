# Project status — updated 12 October 2026

## Current refinement: R1 complete; R2 next

The user's refinement brief selected a separate bounded sequence. R1 was completed in this run; upgrade U2/U3 remain pending. The source brief is archived unchanged under `sources/original/`. No production records, external connection, push or publication was used.

### R1 delivered

- Shared label/control/help/error field groups and responsive filter/action panels, applied to evidence preparation, assessment filters, Kaizen, actions, sessions, evidence/audit forms and supporting template fields. Native selectors retained; menu popovers constrained to the viewport. Evidence preparation has separate Apply/Clear/secondary Export actions, active filters, explicit empty results and per-site filter memory.
- Quick participant draft creation from problem/title, with visible owner/site-context defaults and editable A4/A3/Business Process profile. The entered problem is reused in Plan. Four PDCA stages, useful next-action text, an editable action list, reused observation defaults and calculated empty before/after summaries. Explicit manual averages are retained and discrepancies flagged.
- Debounced autosave of changed fields only, visible saved/failed state, inline accessible errors, resume, CSRF and revision protection. Partial date edits validate against the saved date pair. Invalid action/observation forms and stale coaching advice/replies retain entered text.
- Site-scoped sensei queue with scope/stage/due/readiness filters, saved-data PDCA preview, missing checks and changed-content display. Existing coach role reused for advice, clarification/return, request resolution and verification; team replies do not resolve or approve requests automatically.
- Immutable event/revision checkpoints and complete review conversation in the archive. Changes to verified/sustained/reassessment content require re-review; original assessment responses/snapshots stay separate. Existing source gates remain; Star 8 type counting normalizes case/whitespace and new document types validate against source choices. Excel rejects oversized action/text fields; full JSON retains them.
- `KAIZEN_FIELD_RULES.md` and the 75-row `kaizen-field-rules.csv` distinguish source content, mandatory local gates, conditional quality, derived values and optional context. Exact ten-star text and the additional template/5W2H fields remain available. Guide-dependent profile completeness is not claimed as resolved. A3 PDFs/attachments/import/sharing were not added early.

### R1 checks actually run

- Full Django suite: **24 tests passed** (2.972 seconds). The nine refinement tests were rerun after the final stale-message fix and passed. Coverage includes source preservation, original assessment-to-Kaizen rules, quick drafts, autosave/CSRF/conflicts, partial dates, advice/reply/resolve gates, reviewed revision retention, editable actions, private history, observation reuse/manual overrides, oversized export rejection and true distinct-type Star 8 behavior.
- Migration 0007 applied locally; `makemigrations --check --dry-run` reported no changes. Both JavaScript files passed `node --check`.
- Compared against `backups/pre-refinement.sqlite3`: **856 pre-existing rows across 23 tables unchanged**. Original workbook hashes still match the recorded values. Browser testing used new fictional baseline/after events; earlier site, evidence, event and assessment records were preserved.
- Actual browser pass: desktop (1280 px and default desktop size) and **390×844** narrow layouts, long filter labels/values, empty results, header selectors, keyboard menu navigation, modal layering/Keep editing, autosave error/retry/resume, action add/edit, comparable observations, prepared submission, sensei clarification, reply/resolution/local verification, and an approved-content edit returning to review with a changed Countermeasure flag.
- Narrow page-width checks: 375 CSS px content within a 390 px viewport on evidence preparation and workspace. Date autosave errors retained the entered dates and set `aria-invalid=true`. No dropdown-bearing modal exists in R1; the existing unsaved-work modal was inspected above the header and closed by keyboard.
- SQLite backup/restore after the new history model: integrity `ok`, catalog 15/150/494; live and restored databases each had **17 revision snapshots and 2 review notes**. Shared PostgreSQL recovery remains unverified.
- Before/after screenshots saved in `docs/verification/refinement-preparation-{before,after}.jpg` and corresponding narrow files, plus sensei queue desktop/narrow captures. Local server remains at `127.0.0.1:8000` with the README startup command.

### Practical sample measurements

One local browser automation sample for **create an event and store its overall problem**: baseline **5 interactions / 338 ms**, refinement **2 interactions / 229 ms**. Before required title/profile/create, repeated problem entry, and save; after reused the creation problem and known context. Resume after refinement: **1 reload / 140 ms**, with the saved specific problem retained. These timings exclude human reading/typing and are not human productivity estimates. No comparable pre-refinement resume/coaching timing was collected; no percentage gain is claimed. Attachment/import/repository tasks belong to R2/R3 and were not timed.

### Remaining items and next milestone

**R2: event attachments, existing-evidence links, and deliberate Excel/CSV measurement import.** R3 follows with versioned A3 PDFs and the approved cross-site learning repository. Upgrade U2 template control and U3 governance controls remain unfinished in their separate sequence.

Unresolved: missing Kaizen User Guide/profile completeness and source-template approval; corporate authority and sharing policy; attachment scanning/storage limits; corporate SSO/PostgreSQL/CAT integration and the existing governance policies. Local sensei verification is not official TCA classification or certification. No paid AI dependency was introduced.

## Focused upgrade: U1 complete; U2 next

Only the first unfinished upgrade milestone was executed. Governance was read in full and recorded with page references in `GOVERNANCE_DELTA.md`. The master prompt and originals retain their hashes. The PDF control/footer approval conflict and missing supporting policies remain unresolved.

### U1 changes

- Provisional navy/blue/white design tokens, readable spacing and focus indicators, four grouped navigation areas, mobile menu and breadcrumbs. No official brand assets were present; no CEVA logo was fabricated.
- Persistent authorized country/site selection, organization separate from site, configurable region/grouping, and visible global source-baseline hash, assessment version/status and draft rule version. NL/BE/LU/GB are supported; only existing fictional fixture metadata is set (Harbor NL/Benelux, Maturity Examples GB/UK).
- Task-oriented My work with assigned/site priorities, a short target-blocker list, planned sessions and active improvements. CAT-confirmed standing, local section readiness and target are separate. Frequency and overall site-classification controls are not implemented early.
- Progressive requirement/evidence/source/history disclosure, clear response controls, Save and next; PDCA phase disclosures with saved revision and all original captured fields retained. Distinct field IDs fix ambiguous accessible labels. Staff can read blocker requirements and internal evidence; server authorization still denies response writes and restricted evidence.
- Visible unsaved/failed-save states and an accessible Keep editing / Discard and leave dialog. Invalid Kaizen child forms retain entries and expand their error section rather than discarding input.
- Read-only authorized-location and reports/guidance destinations; technical-admin entry restricted on the server. No program approval/publication UI. Governed templates/profiles/assignments remain U2.

### U1 verification actually run

- Final Django suite: **15 tests passed** (2.182 seconds), including all 11 original source/domain tests and four upgrade tests for location/admin isolation, progressive field preservation/Save and next/invalid child input, empty states, and staff read/write boundaries. `makemigrations --check --dry-run`: no changes detected. `node --check core/static/core/workspace.js`: passed.
- Pre-upgrade backup saved as `backups/pre-ux-upgrade.sqlite3`. `tools/verify_ux_preservation.py`: **849 pre-existing rows across 23 domain tables unchanged**, including all answers, approved snapshots, evidence and Kaizen records; added site metadata columns and new fictional verification records excluded. Workbook, master-prompt and governance-PDF SHA-256 values remain unchanged.
- Actual loopback browser inspection: Overview, assessment filters/full catalog, no-result search, keyboard menu expansion, Netherlands/UK switching, PDCA phase controls, preserved saved entries after reload, and rejected premature coach verification. A new fictional A3 event was used; the original closed event and dated assessments were not edited.
- Desktop layouts and 390×844 narrow layout inspected. Compact menu expanded with keyboard, mobile site switching worked, and assessment requirements use readable mobile rows with visible response/Review links. Read-only page-width check found no document overflow (375 CSS px content at 390 px viewport).
- Browser save feedback and validation errors inspected. Keep editing retained unsaved entries; Save draft persisted them and increased only the new fixture's revision. Discard and leave navigated successfully; reopening the fixture confirmed the unsaved root-cause text was never stored. Initial native confirmation dialog stalled browser automation; replaced it with an accessible in-page dialog and verified it successfully. A stale template cache required a development-server restart; the final screens were checked after restart.
- Captured `docs/verification/ux-overview-desktop.jpg` and `ux-assessment-narrow.jpg`. The local server is running on `127.0.0.1:8000`; startup command remains in README.

### Next milestone and unresolved decisions

**U2: Template control** — immutable baseline/template/requirement versions; profiles and scope assignments; draft change comparisons, reasons, governed review and release; frozen assessment configurations and impact/reassessment handling. Confirm program approval authority with the full working RACI before official publication. Do not equate technical admin or local snapshot approval with governing authority.

Policy gaps: governance approval conflict; current CAT/TCA v3 versus supplied catalog; response A and exception arithmetic; profile applicability; Classification Assessment Policy, TCA Guide, CAT user guide and working RACI. U3 additionally needs exact 186/368-day boundary/counting/grace/recovery rules and CAT reconciliation. Corporate SSO/PostgreSQL/CAT integration remain unverified as before. No push, publication, corporate connection or production data was used.

## Original build checkpoint — 4 October 2026

## Local demonstration delivered

Milestones 1–6 in `PLAN.md` are implemented for a **fictional local SQLite demonstration**. The app has an end-to-end assessment, evidence, opportunity, Kaizen, and reassessment journey. The cumulative maturity calculation is explicitly **draft v1**, and a locally approved snapshot is not corporate certification. Shared PostgreSQL deployment, corporate identity, and exact workbook formula compatibility are outside the verified demo.

### Sources and traceability

- Original files remain unmodified in `sources/original/`. SHA-256: assessment `3c0a8616b3d81d574f7460942a3e16bab61565e593ef8d25a53cca89d4d8c77a`; Kaizen `9bfcfd6258ec108489b2594b19f053a1f2d7f59eac73730217be94948bae3bce`.
- The import has 15 categories, 150 requirements (75 C, 45 B, 30 A), and 494 ordered clauses. Every nonblank assessment B-column cell is assigned to a category, requirement clause, or the sheet header. Repeated source wording retains distinct IDs.
- The Kaizen extraction covers 15 sheets, 46,179 populated cells, 10,885 formula cells, comments, validations, defined names, merged ranges, hidden sheets, and embedded ZIP part names. The original archive remains the authority for features the parser cannot reproduce.

### Application journeys

- Site-scoped login and roles; My Work, Site Progress, searchable assessment, evidence register/preparation, shared sessions, opportunities, Kaizen workspace, and reports.
- Clause-specific accepted evidence and assessor conclusions gate a Yes response. Coverage requires reviewer and time; other-audit coverage requires recorded audit details. Dated approval freezes responses, evidence references, and scoring in a snapshot. New drafts retain history.
- Separate A4, A3, and Business Process Kaizen profiles, PDCA stages, participants, actions, observations, document updates, benefits, ten-star review, and a new-assessment gate before reassessment acceptance. Kaizen closure never changes a TCA response.
- Full JSON archives, a generated Excel operational archive, concise status report, and a filtered evidence-preparation CSV. Known external-template text limits return an explicit error. Formula-compatible export to the source template is not established.

## Checks actually performed

- Automated Django suite: **11 tests passed**, including exact catalog text, scoring boundaries, star boundaries, full assessment history, site isolation, Kaizen closure, accepted coverage, benefit restriction, and Excel archive limits.
- Browser journey on `127.0.0.1:8000`: logged in as the fictional user; saved N for 1.C.1; created an opportunity and A4 event; entered Plan/Do/Check/Act and before/after results; added document updates; moved through coach review; requested reassessment; accepted three individual clause links; saved Y with a conclusion; approved version 2; accepted the reassessment. Version 1 retained N. The second fictional site displayed Certified, Advanced, and Showcase category examples under draft v1.
- SQLite backup and disposable restore: `PRAGMA integrity_check = ok`; restored catalog counts 15/150/494. This is a **local demo recovery check**, not PostgreSQL recovery validation.
- Read workload against the seeded demo (12 GETs each, concurrency 1 and 4): site progress p95 235/227 ms; assessment p95 9/81 ms; evidence preparation p95 16/153 ms. Working set 76.2 MB. This is a small local workload, not a production capacity claim.
- Startup script executed successfully with `-SkipInstall`. No PostgreSQL server or Docker executable exists on this host.

## Business decisions required

1. Define response **A**, its approval path, and effect on gates. Approve or replace cumulative draft v1 scoring, lower-tier awards, exception rules, and who issues official certification.
2. Resolve the assessment workbook's meeting-duration conflict, Environment evidence-period conflict, and dated qualifiers. Supply the referenced FAQ/User Guide or approve explicit interpretations.
3. Confirm required fields, conditional A4/A3/Business Process rules, exact ten-star interpretation, coach authority, and financial validation rules. Confirm the current Global Kaizen template version and reference lists; several defined names contain `#REF!`.
4. Set evidence retention, expiry, classification, attachment size/type and malware scanning policy, audit reuse scope, and permitted remote-assessment methods.

## Corporate integration details required

- OIDC issuer, client ID/secret handling, redirect URLs, claim mapping, group-to-site/role provisioning, session policy, and offboarding; remove local demo credentials for shared use.
- PostgreSQL host/version, database credentials, network/TLS and migration owner; tested `pg_dump`/`pg_restore` routine with retention and restore objectives.
- Private object/file storage, encryption/key ownership, download controls, retention and backup; SMTP/notification sender if notifications are wanted.
- Approved hosting URL/TLS, secret store, operational owner, logging/audit retention, monitoring, support route, and security review.
- Decide whether an enterprise workbook-compatible export and any `DL_UPLOAD`/`AUTO_UPLOAD` integration are required. Those sheets alone do not specify an API.

## Verification limits and next deployment gate

The source workbook parser reports unsupported extension validation/conditional-formatting elements and drawings; the originals preserve them. The app has not been run against PostgreSQL or corporate SSO, nor validated with real customer data or an owner-approved policy. A shared pilot requires those integrations and owner sign-off on the decisions above, followed by end-to-end role, backup/restore, and workload checks in that environment.
