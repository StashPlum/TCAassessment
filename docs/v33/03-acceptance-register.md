# 3.3 acceptance register

Status values: Not started / Implemented-unverified / Verified / Failed / Blocked. An item is marked Verified only when the evidence column names something that actually ran on 20 Oct 2026. AC-01…AC-34 stay as recorded in `docs/v3/05-acceptance-register.md`, except for the changes listed at the end of this file.

The e2e test referred to below is `tools/v33_auditor_e2e.py`, run in Chromium against a fresh demo database with the real V3 source. The test file referred to below is `core/test_v33_catalogue.py`.

## V3.3 hard gates

| ID | Status | Evidence |
|---|---|---|
| V3-01 Source count | Verified | `import_v3_catalogue` gives 164 / 150 / 15 / 16 with 0 errors. The report is saved as `reconciliation-report.json`. See 01-reconciliation.md |
| V3-02 Group resolution | Verified | `per_group` in the report: 16 × (150 records, 150 IDs, positions 1–10 per section). The importer re-checks this in the database. Test `test_import_is_idempotent_and_variants_resolve_per_group` |
| V3-03 Variant correctness | Verified | e2e test: GROUP_02 and GROUP_12 sites each show their own 01.01.C variant exactly, and no other. `v33_export_check.py`: XLSX/PDF records, JSON archive and report have 150/150 exact variants for both sites |
| V3-04 Continuation fidelity | Verified | Test `test_parse_keeps_continuation_rows_exactly` (multi-row I with spacer and lettered parts, J continuation). The importer's verify pass compares the stored text with the source for all 164 records ("164 stored records unchanged") |
| V3-05 Evidence/explanation | Verified | Stored separately (`expected_evidence`, `reasoning`). e2e test "evidence statement on demand" passes for both sites |
| V3-06 Versioning | Verified | Test `test_new_version_keeps_earlier_records_and_assessments`: a second version gets new codes, the first is retired, and the old assessment scope is unchanged. Approved snapshots stay immutable (3.2 tests still pass) |
| V3-07 Safe import | Verified | Dry run, idempotency, rollback, checksum and anomaly tests; see 01-reconciliation.md §Safe import |
| V3-08 Site mapping | Verified | Test `test_unmapped_site_is_blocked_not_defaulted`; `test_group_mapping_needs_admin_preview_and_confirmation` (non-admin and other-site admin get 404, there is no save without confirmation, an audit event is written, and the next draft uses the mapped variants). Screenshot `after-blocker-1440-0.png` |
| UX-31 Guided auditor | Verified for answer, comment field (Advisory follow-up), evidence attach/accept, next open question, view switch, resume and export. Implemented-unverified for the free-text conclusion on Y in the browser | e2e test 22/22 checks; `v33_export_check.py`; test `test_attach_evidence_permissions_and_rules` (negative cases) |
| UX-32 Guided Kaizen | Implemented-unverified for 3.3 | Kaizen flow unchanged from 3.2 (AC-19/AC-21 evidence there); 3.3 adds the team PDCA journey on the start page only |
| UX-33 Typography | Implemented-unverified | Inter (OFL), one scale in `v33.css`. Contrast and 200 % text resize were not measured with a tool |
| UX-34 Interaction reduction | Implemented-unverified | After-counts measured (02-design-decisions.md §Journeys). 3.2 counts were not re-measured in a browser |
| VIS-35 Visual audit | Verified (inspection) | 02-design-decisions.md §Visualisation decision matrix: kept / replaced / omitted, with reasons |
| VIS-36 Dashboard fit | Implemented-unverified | Decision, source, denominator, drill-down and text alternative are specified per visual. Unit tests cover only the data functions indirectly (role start pages render in the CI tests) |
| VIS-37 Diversity | Verified (inspection) | Heatmap, maturity ladder, timeline, pipeline, dumbbell and PDCA journey. Screenshots `after-home-*` |
| VIS-38 Correctness | Verified for scope | Every figure is read from stored records (`core/insights.py`). Sections are scoped to the assessment's frozen catalogue (the report fix in commit 1dd5136). No trends or targets |
| SAFE-39 Isolation | Verified | Only `TCA-progress-v33` was pushed; `git ls-remote` after the push shows `main` a6af626 and `TCA_Demo` ab50e7f. No Render, database or webhook action. See 04-isolation-and-deployment.md |
| LIVE-40 New deployment | Blocked | Needs the owner to create the Render Blueprint `tca-progress-v33` and upload the secret file. Steps are in 04 |

## Changes to AC-01…AC-34

| ID | Change |
|---|---|
| AC-10 Official catalogue | Blocked → **Verified for V3** (V3-01…V3-04). The legacy workbook is still not available to the build |
| AC-11 Y/A/N, AC-12 Input views, AC-13 Synchronisation, AC-15 Autosave | Re-verified on the V3 focus canvas (e2e test) |
| AC-14 Evidence | Attach from the question is verified, including the negative cases (role, other site, missing reason, outside scope, unsafe redirect). Durability is still bound to decision O1 (free plan) |
| AC-18 Maturity | The ladder uses the same `category_result` gates; there are no new fixtures |
| AC-24 Responsive | Focus view at 1024/768/390 has no overflow (e2e). Role start pages at 390 have no overflow (screenshots) |
| AC-27 New deployment | Blocked, as LIVE-40 |
| AC-31…34 | Re-checked after the push; see SAFE-39 |

## Test runs

| Run | Result |
|---|---|
| `tools/run_source_free_ci.py` (synthetic data, including 9 new V3 tests) | 74 tests OK |
| `tools/v33_auditor_e2e.py` (fresh demo DB, real V3 source, Chromium) | 22/22 checks passed |
| `tools/v33_export_check.py` | 2 sites × (150/150 records, 150/150 archive, 15 sections) |
| `import_v3_catalogue --dry-run` from the JSON extract | Passed, nothing stored |
