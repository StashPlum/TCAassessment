# Source traceability

The original workbooks in `sources/original/` are immutable and private. `sources/extracted/manifest.json` records SHA-256. `tools/extract_sources.py` creates full cell-level JSON, including hidden sheets, formulas, comments, validations, defined names, merged ranges, and ZIP part inventory. This extraction is inspectable, not a replacement for the workbook archive; openpyxl warns that some extension validations, conditional formatting, and drawings are not fully understood. We do not rewrite the originals.

## Assessment mapping

`Sheet1!A4:B626` contains 15 category headings and 150 IDs. `Sheet1!A<row>` maps to requirement ID, category, level code, and position. Each `Sheet1!B<start:end>` maps to an ordered clause list and exact detail text. `C`, `D`, and `E` at the ID row map to reasoning, expected evidence, and remote assessment method. Every clause retains its source address. All 150 records are imported even when wording repeats. The original source guide remains available for unsupported cell formatting and surrounding context.

The parser assigns consecutive B rows after an ID to that requirement, ending before the next ID or category. This preserves notes and detail clauses. An exhaustive check found no unassigned nonblank B-column text beyond the sheet header and category headings. Two whitespace-only B cells have no assignment. Search tags and plain-language help are separate from the imported text.

## Kaizen mapping

The full 15-sheet template has 46,179 populated cells, including 10,885 formula cells. Visible sheets: 5W2H, TEAM, PLAN, DO, CHECK, ACT, COACH REVIEW, PORTRAIT, LANDSCAPE, DL_UPLOAD, LocationID. Hidden sheets: BU, AUTO_UPLOAD, VERSION_CONTROL, DROP_DOWNS. The extracted JSON stores each cell address and formula. VERSION_CONTROL records changes through 28 April 2023, despite the supplied filename's 2024 date. Confirm the intended current template version with its owner.

PLAN and 5W2H map to overall and specific problems, current/target measures, symptom, investigated root cause, and source guidance. DO maps to solution and all actions with owner and dates. CHECK maps to comparable before/after results, target, benefit types, and green impact. ACT maps to sustain actions and updated document/tool types. TEAM maps to participants, roles, and hours. COACH REVIEW maps to completeness and review criteria. PORTRAIT/LANDSCAPE are concise output layouts. DL_UPLOAD and AUTO_UPLOAD are legacy export mappings, not evidence of an API. LocationID, BU, and DROP_DOWNS are versioned reference sources, subject to freshness review.

Defined names `BU`, `Contribution`, `Country`, `Site_ID`, and `USD_Conversion` contain `#REF!`. Formula engine compatibility is not established. Preserve the source and flag these mappings; do not claim parity from a parsed formula. The source guide references missing FAQ/User Guide materials. A4, A3, and Business Process conditional requirements require owner confirmation where not explicit in workbook text.

## Known source conflicts and ambiguity

Response A meaning; meeting duration guidance; Environment evidence window; dated qualifiers; missing FAQ/User Guide; broken defined names and stale reference lists. These are tracked in `docs/STATUS.md`. Source wording takes precedence over the build brief where they conflict.

