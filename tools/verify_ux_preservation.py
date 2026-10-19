"""Compare pre-upgrade domain records with live demo; allow new fictional rows."""
import sqlite3
import sys
from pathlib import Path

root=Path(__file__).resolve().parents[1]
baseline=Path(sys.argv[1]) if len(sys.argv)>1 else root/'backups/pre-ux-upgrade.sqlite3'
with sqlite3.connect(baseline) as before, sqlite3.connect(root/'local.sqlite3') as after:
    tables=[row[0] for row in before.execute("SELECT name FROM sqlite_master WHERE type='table'")
            if row[0].startswith('core_')]
    total=0
    for table in tables:
        columns=[row[1] for row in before.execute(f'PRAGMA table_info("{table}")')]
        selection=','.join('"'+column+'"' for column in columns)
        old=before.execute(f'SELECT {selection} FROM "{table}" ORDER BY 1').fetchall()
        new={row[0]:row for row in after.execute(f'SELECT {selection} FROM "{table}"')}
        assert all(new.get(row[0])==row for row in old),f'Existing records changed: {table}'
        total+=len(old)
    print(f'PRESERVATION VERIFIED: {total} existing rows across {len(tables)} domain tables unchanged.')
    print('New fictional rows and added location columns are excluded from the comparison.')
