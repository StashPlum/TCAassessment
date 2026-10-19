"""Produce lossless application source records without modifying either workbook."""
from __future__ import annotations

import hashlib
import json
import re
import warnings
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from zipfile import ZipFile

from openpyxl import load_workbook
from openpyxl.worksheet.formula import ArrayFormula, DataTableFormula

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / "sources" / "original"
OUT = ROOT / "sources" / "extracted"
OUT.mkdir(exist_ok=True)

def serial(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, ArrayFormula):
        return {"kind": "ArrayFormula", "ref": value.ref, "text": value.text}
    if isinstance(value, DataTableFormula):
        return {"kind": "DataTableFormula", "ref": value.ref, "dt2D": value.dt2D,
                "dtr": value.dtr, "r1": value.r1, "r2": value.r2}
    if not isinstance(value, (str, int, float, bool, type(None))):
        return str(value)
    return value

manifest = {}
for path in sorted(ORIGINAL.glob("*.xlsx")):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        book = load_workbook(path, data_only=False)
    record = {"filename": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
              "sheets": [], "defined_names": {k: v.attr_text for k, v in book.defined_names.items()}}
    with ZipFile(path) as archive:
        record["embedded_parts"] = archive.namelist()
    for sheet in book.worksheets:
        cells = [{"address": cell.coordinate, "value": serial(cell.value), "type": cell.data_type,
                  "comment": cell.comment.text if cell.comment else None}
                 for row in sheet for cell in row if cell.value is not None or cell.comment]
        record["sheets"].append({"name": sheet.title, "state": sheet.sheet_state,
                                 "dimensions": [sheet.max_row, sheet.max_column],
                                 "cells": cells,
                                 "validations": [{"range": str(v.sqref), "type": v.type,
                                                  "formula1": v.formula1, "formula2": v.formula2,
                                                  "prompt": v.prompt, "error": v.error}
                                                 for v in sheet.data_validations.dataValidation],
                                 "merged_ranges": [str(r) for r in sheet.merged_cells.ranges],
                                 "images": len(sheet._images), "charts": len(sheet._charts)})
    if path.name.startswith("TCA assessment"):
        ws = book.active
        categories, requirements = [], []
        current_category = None
        for row in range(1, ws.max_row + 1):
            id_value = ws.cell(row, 1).value
            if isinstance(id_value, int) and 1 <= id_value <= 15:
                current_category = {"number": id_value, "name": ws.cell(row, 2).value,
                                    "source": f"{ws.title}!A{row}:B{row}"}
                categories.append(current_category)
            if isinstance(id_value, str) and re.fullmatch(r"\d+\.[CBA]\.\d+", id_value.strip()):
                requirements.append({"id": id_value.strip(), "category_number": current_category["number"],
                                     "level_code": id_value.split(".")[1], "position": int(id_value.split(".")[2]),
                                     "start_row": row, "source": f"{ws.title}!A{row}:E{row}",
                                     "reasoning": serial(ws.cell(row, 3).value),
                                     "expected_evidence": serial(ws.cell(row, 4).value),
                                     "remote_method": serial(ws.cell(row, 5).value)})
        for index, req in enumerate(requirements):
            end = (requirements[index + 1]["start_row"] - 1 if index + 1 < len(requirements)
                   else ws.max_row)
            next_category = next((c for c in categories if c["number"] == req["category_number"] + 1), None)
            if next_category:
                end = min(end, int(next_category["source"].split("!")[1].split(":")[0][1:]) - 1)
            req["clauses"] = [{"address": f"{ws.title}!B{r}", "text": ws.cell(r, 2).value}
                              for r in range(req["start_row"], end + 1)
                              if isinstance(ws.cell(r, 2).value, str) and ws.cell(r, 2).value.strip()]
            req["detail_text"] = "\n".join(c["text"] for c in req["clauses"])
        assert len(categories) == 15 and len(requirements) == 150
        assert Counter(r["level_code"] for r in requirements) == Counter({"C": 75, "B": 45, "A": 30})
        assert all(len(r["clauses"]) for r in requirements)
        record["categories"] = categories
        record["requirements"] = requirements
    manifest[path.name] = {"sha256": record["sha256"], "sheets": len(record["sheets"]),
                           "cells": sum(len(s["cells"]) for s in record["sheets"]),
                           "formula_cells": sum(c["type"] == "f" for s in record["sheets"] for c in s["cells"])}
    (OUT / f"{path.stem}.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
(OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(json.dumps(manifest, indent=2))
