"""Package original project code/artifacts; omit upstream copies, keys and corpus bytes."""
from pathlib import Path
import hashlib
import json
import zipfile

ROOT=Path(__file__).resolve().parents[1]

def main():
    output=ROOT/'results'; output.mkdir(exist_ok=True)
    archive=output/'DT083_submission.zip'
    candidates=[]
    for folder in ['src','scripts','tests','configs','docs']:
        candidates.extend(p for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    for filename in ['README.md','requirements-lock.txt','requirements.in','pyproject.toml','.gitignore']:
        candidates.append(ROOT/filename)
    for relative in ['references/downloads.json','references/schema_audit.json','references/commit.json']:
        candidates.append(ROOT/relative)
    for run in ['smoke','full']:
        for folder in ['results','models','data/manifests','data/features']:
            candidates.extend(p for p in (ROOT/'runs'/run/folder).glob('*') if p.is_file() and p.name!='simulation_key.json')
    candidates.extend(p for p in (output/'author_reference').glob('*') if p.is_file())
    candidates.extend(p for p in output.glob('*') if p.is_file() and p.name in ['tests.xml','tests-fresh.xml','fresh_environment.json','hardware.json','verification.json'])
    index=[]
    for path in sorted(set(candidates)):
        if not path.exists(): continue
        raw=path.read_bytes()
        index.append({'path':path.relative_to(ROOT).as_posix(),'size_bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
    (output/'submission_inventory.json').write_text(json.dumps(index,indent=2),encoding='utf-8')
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as handle:
        for entry in index: handle.write(ROOT/entry['path'],arcname='DT083/'+entry['path'])
        handle.write(output/'submission_inventory.json',arcname='DT083/results/submission_inventory.json')
    digest=hashlib.sha256(archive.read_bytes()).hexdigest()
    (output/'submission_sha256.txt').write_text(f'{digest}  DT083_submission.zip\n',encoding='ascii')
    print(f'Packaged {len(index)} files; {archive.stat().st_size} bytes; sha256={digest}')

if __name__=='__main__': main()
