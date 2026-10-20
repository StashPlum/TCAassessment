"""Measured local GET workload against the actual demo database."""
import os
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.vendor'))
sys.path.insert(0,str(ROOT))
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')
import django
django.setup()
from django.contrib.auth import get_user_model
from django.test import Client
from core.models import Category, Requirement, Clause

user=get_user_model().objects.get(username='demo')
paths=['/sites/fictional-harbor/','/sites/fictional-harbor/assessment/','/sites/fictional-harbor/evidence/preparation/']
def one(path):
    client=Client(SERVER_NAME='127.0.0.1');client.force_login(user)
    start=time.perf_counter();response=client.get(path);elapsed=(time.perf_counter()-start)*1000
    if response.status_code!=200: raise RuntimeError(f'{path}: {response.status_code}')
    return elapsed
for concurrency in (1,4):
    for path in paths:
        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            samples=list(pool.map(one,[path]*12))
        samples.sort()
        print(f'{path} concurrency={concurrency} n=12 p50={statistics.median(samples):.1f}ms p95={samples[11]:.1f}ms max={max(samples):.1f}ms')
print('dataset',Category.objects.count(),'categories',Requirement.objects.count(),'requirements',Clause.objects.count(),'clauses')
try:
    import psutil
    print('process RSS MB',round(psutil.Process().memory_info().rss/1024/1024,1))
except ImportError:
    if sys.platform=='win32':
        import ctypes
        from ctypes import wintypes
        class Memory(ctypes.Structure):
            _fields_=[('cb',wintypes.DWORD),('PageFaultCount',wintypes.DWORD),
                      ('PeakWorkingSetSize',ctypes.c_size_t),('WorkingSetSize',ctypes.c_size_t),
                      ('QuotaPeakPagedPoolUsage',ctypes.c_size_t),('QuotaPagedPoolUsage',ctypes.c_size_t),
                      ('QuotaPeakNonPagedPoolUsage',ctypes.c_size_t),('QuotaNonPagedPoolUsage',ctypes.c_size_t),
                      ('PagefileUsage',ctypes.c_size_t),('PeakPagefileUsage',ctypes.c_size_t)]
        value=Memory();value.cb=ctypes.sizeof(Memory)
        get_process=ctypes.windll.kernel32.GetCurrentProcess
        get_process.restype=wintypes.HANDLE
        get_memory=ctypes.windll.psapi.GetProcessMemoryInfo
        get_memory.argtypes=[wintypes.HANDLE,ctypes.POINTER(Memory),wintypes.DWORD]
        get_memory.restype=wintypes.BOOL
        ok=get_memory(get_process(),ctypes.byref(value),value.cb)
        print('process working set MB',round(value.WorkingSetSize/1024/1024,1) if ok else 'unavailable')
    else: print('process RSS unavailable')
