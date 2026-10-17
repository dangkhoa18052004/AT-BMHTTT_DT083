"""Download ONLY passive research references; never execute upstream code."""
from pathlib import Path
import hashlib
import json
import urllib.request
import zipfile
import csv
import io
import collections
import datetime

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'references'

def fetch(url, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={'User-Agent': 'DT083-research/1.0'})
    with urllib.request.urlopen(req, timeout=90) as response:
        raw = response.read()
    target.write_bytes(raw)
    return {'url': url, 'path': str(target.relative_to(ROOT)), 'size_bytes': len(raw),
            'sha256': hashlib.sha256(raw).hexdigest()}

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    records = []
    records.append(fetch('https://api.github.com/repos/francasino/Ransomware_analysis/commits/main', OUT/'commit.json'))
    commit = json.loads((OUT/'commit.json').read_text())['sha']
    base = f'https://raw.githubusercontent.com/francasino/Ransomware_analysis/{commit}/'
    paths = ['README.md', 'datasets/readme', 'Ransomware_clean.ipynb', 'hedge_office.ipynb',
             'tests/StatSeeker.py','tests/ais31.py','tests/batteries.py','tests/ent.py',
             'tests/fips.py','tests/readme','tests/testsp80022.py','tests/utilities.py']
    paths += [f'datasets/final{k}.zip' for k in [64,128,256,512,1024]]
    audits = []
    for name in paths:
        print('Downloading', name, flush=True)
        try:
            records.append(fetch(base + name, OUT/'author'/name))
            if name.endswith('.zip'):
                with zipfile.ZipFile(OUT/'author'/name) as archive:
                    for member in archive.infolist():
                        item = {'archive':name, 'member':member.filename, 'uncompressed_bytes':member.file_size}
                        if member.filename.endswith('.csv'):
                            with archive.open(member) as handle:
                                reader = csv.DictReader(io.TextIOWrapper(handle,encoding='utf-8-sig'))
                                item['columns'] = reader.fieldnames
                                counts = collections.defaultdict(collections.Counter)
                                missing = collections.Counter()
                                n = 0
                                examples = []
                                for row in reader:
                                    if n < 3: examples.append(row)
                                    for key,value in row.items():
                                        if not value or value.lower() in ['nan','none','null']: missing[key] += 1
                                        if key and ('label' in key.lower() or 'type' in key.lower() or 'class' in key.lower()): counts[key][value] += 1
                                    n += 1
                                item.update(rows=n,missing=dict(missing),categorical_counts={k:dict(v) for k,v in counts.items()},examples=examples,
                                            source_group_id_present='source_group_id' in item['columns'])
                        audits.append(item)
        except Exception as exc:
            records.append({'url':base+name,'error':str(exc)})
    external = [
        ('https://kar.kent.ac.uk/112636/1/ransomware%20detection%20through%20classification%20of%20high-entropy%20file%20segments.pdf','paper.pdf'),
        ('https://zenodo.org/api/records/5148542','zenodo_metadata.json')]
    for url,name in external:
        try: records.append(fetch(url, OUT/name))
        except Exception as exc: records.append({'url':url,'error':str(exc)})
    inventory = {'commit':commit,'accessed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                 'files':records,'license_note':'No license found in upstream tree: local research only; do not redistribute author files.'}
    (OUT/'downloads.json').write_text(json.dumps(inventory,indent=2),encoding='utf-8')
    (OUT/'schema_audit.json').write_text(json.dumps(audits,indent=2),encoding='utf-8')
    for name in ['Ransomware_clean','hedge_office']:
        path=OUT/'author'/f'{name}.ipynb'
        if path.exists():
            notebook=json.loads(path.read_text(encoding='utf-8'))
            text='\n\n'.join(f'# CELL {i} ({c["cell_type"]})\n'+''.join(c.get('source',[])) for i,c in enumerate(notebook['cells']))
            (OUT/f'{name}_readable.txt').write_text(text,encoding='utf-8')
    print('Saved reference inventory and schema audit', flush=True)

if __name__ == '__main__': main()
