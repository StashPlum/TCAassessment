"""SQLite-only local demo backup and disposable restoration check."""
import argparse
import hashlib
import sqlite3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('action',choices=['backup','verify'])
parser.add_argument('path',type=Path)
args=parser.parse_args()
source=ROOT/'local.sqlite3'
target=args.path.resolve()
target.parent.mkdir(parents=True,exist_ok=True)
if args.action=='backup':
    with sqlite3.connect(source) as live, sqlite3.connect(target) as copy:
        live.backup(copy)
    print('BACKUP',target,'sha256',hashlib.sha256(target.read_bytes()).hexdigest())
else:
    if not target.exists(): raise SystemExit('Backup file missing')
    restored=target.with_name(target.stem+'-restored.sqlite3')
    with sqlite3.connect(target) as backup, sqlite3.connect(restored) as copy:
        backup.backup(copy)
    with sqlite3.connect(restored) as db:
        integrity=db.execute('PRAGMA integrity_check').fetchone()[0]
        categories=db.execute('SELECT COUNT(*) FROM core_category').fetchone()[0]
        requirements=db.execute('SELECT COUNT(*) FROM core_requirement').fetchone()[0]
        clauses=db.execute('SELECT COUNT(*) FROM core_clause').fetchone()[0]
    assert integrity=='ok' and (categories,requirements,clauses)==(15,150,494)
    print('RESTORE VERIFIED',restored,'integrity',integrity,'catalog',categories,requirements,clauses)
