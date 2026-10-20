"""Migrate a disposable copy of the pre-toolbox database and compare old columns."""
import os, sqlite3, sys
from pathlib import Path
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import django
from django.conf import settings
root=Path(__file__).resolve().parents[1]
source=root/'backups/pre-toolbox.sqlite3';target=root/'tmp/toolbox-migration.sqlite3'
target.parent.mkdir(exist_ok=True)
with sqlite3.connect(source) as old,sqlite3.connect(target) as copy: old.backup(copy)
settings.DATABASES['default']['NAME']=target
django.setup()
from django.core.management import call_command
call_command('migrate',verbosity=0)
count=0
with sqlite3.connect(source) as old,sqlite3.connect(target) as new:
    tables=[r[0] for r in old.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'core_%'")]
    for table in tables:
        columns=[row[1] for row in old.execute(f'PRAGMA table_info("{table}")')]
        quoted=','.join('"'+c+'"' for c in columns)
        before=old.execute(f'SELECT {quoted} FROM "{table}" ORDER BY 1').fetchall()
        after=new.execute(f'SELECT {quoted} FROM "{table}" ORDER BY 1').fetchall()
        assert before==after,table
        count+=len(before)
    assert new.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    assert all(r[0]=='legacy' for r in new.execute('SELECT input_profile FROM core_kaizen'))
print(f'Disposable migration verified: {count} old rows in {len(tables)} tables unchanged; legacy classification retained; integrity ok.')
