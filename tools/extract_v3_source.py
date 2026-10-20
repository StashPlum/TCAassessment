"""Write a JSON extract of the private V3 workbook's raw rows (for a Render secret file). Never commit the output.

    python tools/extract_v3_source.py "V3assessment .xlsx" /secure/place/tca-v3-source.json

The extract keeps every cell value exactly and records the workbook's SHA-256, so an import from the extract
produces the same catalogue version as an import from the workbook. The workbook is opened read-only.
"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.v3_source import parse, reconcile, rows_from_workbook

if len(sys.argv) != 3: sys.exit(__doc__)
source = rows_from_workbook(sys.argv[1])
report = reconcile(*parse(source))
if report['errors']: sys.exit('Source has errors:\n' + '\n'.join(report['errors']))
out = Path(sys.argv[2])
repo = Path(__file__).resolve().parents[1]
if out.resolve().is_relative_to(repo):
    sys.exit('Write the extract outside the repository; it contains the official wording.')
out.write_text(json.dumps(source, ensure_ascii=False), encoding='utf-8')
print(f"{report['records']} records, {report['questions']} QuestionIDs, {len(report['groups'])} groups; SHA-256 {source['sha256']} -> {out}")
