# V3 source reconciliation

Recorded on 20 Oct 2026. This file holds identifiers and counts only. The requirement wording stays in the private workbook.

## Source

| Item | Value |
|---|---|
| File | `V3assessment .xlsx`, sheet `Blad1`, columns A–K |
| SHA-256 | `2f09c1217f052943c61b241a26c1cdb010d1c28c23be2285c48eb29cf5c04a1f` |
| Release row | "TCA v3_release date: Sept. 25, 2025" |
| Opened | read-only (`openpyxl.load_workbook(read_only=True)`); never saved |
| Catalogue key | `tca-v3-2f09c1217f05` |

## Counts (V3-01)

| Check | Expected | Found |
|---|---|---|
| Numbered source records (Master Order) | 164 | 164, continuous 1..164 |
| Distinct QuestionIDs | 150 | 150 |
| Sections | 15 | 15 |
| TCA groups | 16 (02–18, no 06) | 16 (`TCA_v3_GROUP_02`…`_18`, no `_06`) |
| Levels (records) | — | Certified 85, Advanced 47, Showcase 32 |
| Language / product line | — | English 164 / Ground & Rail 164 |
| Errors / anomalies | 0 | 0 / 0 |

## Group resolution (V3-02)

Each of the 16 groups resolves to:
- 150 records with 150 distinct QuestionIDs
- no overlap and no missing QuestionID
- exactly positions 1–10 in every section

This is checked in two places:
- **Reconciliation** (`per_group` in the report).
- **Importer, after storing.** For each group it checks that the database query returns 150 rows and 150 distinct IDs. If not, it rolls back.

## Variants (V3-03)

14 extra records give 12 QuestionIDs more than one wording. The table shows each Master Order with the number of groups it applies to.

| QuestionID | Variants (Master Order : groups) |
|---|---|
| 01.01.C | 1:6, 2:6, 3:2, 4:2 |
| 01.02.C | 5:12, 6:4 |
| 01.05.C | 9:8, 10:8 |
| 04.01.C | 36:8, 37:8 |
| 06.06.B | 62:8, 63:8 |
| 07.05.C | 72:8, 73:8 |
| 07.10.A | 78:8, 79:8 |
| 08.02.C | 81:8, 82:8 |
| 10.08.B | 108:8, 109:8 |
| 10.09.A | 110:8, 111:8 |
| 13.03.C | 135:8, 136:8 |
| 13.04.C | 137:8, 138:8 |

How variant codes are stored and shown:
- The internal key is `QuestionID` for a unique question, or `QuestionID~n` for a variant (n follows the Master Order).
- A later catalogue version adds a letter, for example `QuestionID~b` or `QuestionID~b2`. Earlier records and assessments are then never touched.
- Screens and exports show the QuestionID only. The `|qid` filter and `Requirement.label` take care of this.

Verification:
- `tools/v33_auditor_e2e.py` compares the on-screen text with the source at run time. It uses two sites in different groups (GROUP_02 shows record 1, GROUP_12 shows record 4).
- `tools/v33_export_check.py` confirms that the XLSX/PDF records, the JSON archive and the report contain 150 rows. All 150 hold the exact variant for both sites.

## Continuation rows (V3-04, V3-05)

| Item | Count |
|---|---|
| Records spanning more than one row | 134 |
| Records with evidence (J) continuation | 15 |
| Records with explanation (K) continuation | 11 |
| Records with lettered sub-requirements | 72 |

How the rows are joined:
- Lines are joined with `\n`. Spacer rows become empty lines, and leading or trailing spacers are dropped.
- Nothing else is changed.
- Requirement text (I) is stored in `detail_text`, evidence (J) in `expected_evidence`, and explanation (K) in `reasoning`.
- The focus canvas shows evidence and explanation as separate disclosures.
- Lettered parts become `Clause` rows, which are the evidence units. The introduction text stays in `detail_text`.

## Observations (recorded, not corrected)

Lettering that skips letters or restarts. The wording is kept exactly as written.

| QuestionID | Letters as written |
|---|---|
| 01.03.C | B C D E |
| 04.01.C (both variants) | A B C A B C |
| 04.07.B | A B B C |
| 08.08.B | B C D E |

The section names in V3 differ from the names in the shared legacy `Category` rows for all 15 sections. Screens show the V3 name, taken from each requirement's own `section_label`. The legacy rows are not changed.

## Safe import (V3-07)

| Property | How it is verified |
|---|---|
| Dry run stores nothing | test `test_dry_run_stores_nothing`; real source: "Dry run passed … Nothing stored" |
| Idempotent | test `test_import_is_idempotent…`. A real re-run reports "Verified … 164 stored records unchanged" |
| Transactional rollback | test `test_inconsistent_source_imports_nothing`, which removes one variant so a group lacks a question: no catalogue is stored |
| Checksum | key and `sha256` come from the source bytes. A JSON extract carries the workbook SHA, so both produce the same version |
| Anomaly reporting | orphan continuation rows, header changes, ID/level/position mismatches and missing groups are all reported. Test `test_orphan_continuation_is_an_error` covers this |
| Immutable versions | a stored record that differs from its source fails with "versions are immutable". Test `test_new_version_keeps_earlier_records_and_assessments` covers this |
