# Project status — 4 October 2026

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

