from pathlib import Path
import hashlib
import json
import datetime
import platform
import os
import importlib.metadata
import psutil

def sha256(data):
    return hashlib.sha256(data).hexdigest()

def confined(root, path):
    root = Path(root).resolve()
    candidate = Path(path)
    target = (candidate if candidate.is_absolute() else root / candidate).resolve()
    if not target.is_relative_to(root):
        raise ValueError(f'Path outside permitted corpus: {path}')
    return target

def dump_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')

def now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).isoformat()

def environment():
    packages = ['numpy','pandas','scikit-learn','cryptography','Pillow','reportlab','matplotlib','psutil','pytest','scipy','joblib']
    cpu=os.environ.get('PROCESSOR_IDENTIFIER',platform.processor())
    if os.name=='nt':
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,r'HARDWARE\DESCRIPTION\System\CentralProcessor\0') as key:
                cpu=winreg.QueryValueEx(key,'ProcessorNameString')[0].strip()
        except OSError:
            pass
    return {'time':now(), 'os':platform.platform(), 'python':platform.python_version(),
            'cpu':cpu, 'physical_cores':psutil.cpu_count(logical=False), 'logical_threads':os.cpu_count(),
            'ram_bytes':psutil.virtual_memory().total,
            'versions':{p:importlib.metadata.version(p) for p in packages}}
