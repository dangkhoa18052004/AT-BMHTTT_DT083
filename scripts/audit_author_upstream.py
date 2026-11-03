"""Read-only source audit; fetch GitHub metadata, never raw archives or executable code."""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]

def sha256(data):
    return hashlib.sha256(data).hexdigest()

def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'DT083-source-audit'})
    with urllib.request.urlopen(req, timeout=90) as response:
        return response.read()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    out = ROOT / args.output
    out.mkdir(parents=True, exist_ok=False)
    manifest = json.loads((ROOT/'references/downloads.json').read_text(encoding='utf-8'))
    commit = manifest['commit']
    base = 'https://api.github.com/repos/francasino/Ransomware_analysis'
    remote_commit = get(f'{base}/commits/{commit}')
    (out/'upstream_commit.json').write_bytes(remote_commit)
    commit_info = json.loads(remote_commit)
    tree = get(f"{base}/git/trees/{commit_info['commit']['tree']['sha']}?recursive=1")
    (out/'upstream_tree.json').write_bytes(tree)
    remote = {x['path']: x for x in json.loads(tree)['tree'] if x['type'] == 'blob'}
    try:
        latest = get(f'{base}/commits/main')
        (out/'upstream_main.json').write_bytes(latest)
        latest_sha = json.loads(latest)['sha']
    except Exception as exc:
        latest_sha = str(exc)
    files = []
    for p in sorted((ROOT/'references/author').rglob('*')):
        if not p.is_file():
            continue
        name = p.relative_to(ROOT/'references/author').as_posix()
        data = p.read_bytes()
        blob_sha = hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        old = next((x for x in manifest['files'] if x.get('path', '').replace('\\','/') == p.relative_to(ROOT).as_posix()), {})
        files.append({'path':p.relative_to(ROOT).as_posix(), 'size':len(data),
                      'sha256':sha256(data), 'git_blob_sha1':blob_sha,
                      'upstream_blob_sha1':remote.get(name,{}).get('sha'),
                      'matches_upstream':blob_sha == remote.get(name,{}).get('sha'),
                      'matches_old_download_manifest':sha256(data)==old.get('sha256')})
    notebooks = []
    for folder in ['references','runs','results','docs','scripts']:
        for p in (ROOT/folder).rglob('*.ipynb'):
            n = json.loads(p.read_text(encoding='utf-8'))
            notebooks.append({'path':p.relative_to(ROOT).as_posix(),'sha256':sha256(p.read_bytes()),
                              'metadata':n.get('metadata'), 'cells':[
                                  {'index0':i,'type':c['cell_type'],'execution_count':c.get('execution_count'),
                                   'output_count':len(c.get('outputs',[])), 'metadata':c.get('metadata'),
                                   'error_names':[v.get('ename') for v in c.get('outputs',[]) if v['output_type']=='error']}
                                  for i,c in enumerate(n['cells'])]})
    artifacts=[]
    for folder in ['results/author_reference']:
        for p in sorted((ROOT/folder).glob('*')):
            if p.is_file():
                artifacts.append({'path':p.relative_to(ROOT).as_posix(),'size':p.stat().st_size,
                                  'sha256':sha256(p.read_bytes())})
    report={'observed_at_utc':datetime.now(timezone.utc).isoformat(), 'source_commit':commit,
            'upstream_main_at_audit':latest_sha, 'files':files,'notebooks_before_execution':notebooks,
            'old_author_reference_artifacts':artifacts,
            'note':'Git blob SHA-1 comparison is against live GitHub commit tree; existing notebook outputs are upstream bytes if entire file matches.'}
    (out/'audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'commit':commit,'main':latest_sha,'files':len(files),
                      'all_match_upstream':all(x['matches_upstream'] for x in files),
                      'notebooks':[(x['path'],len(x['cells'])) for x in notebooks]},ensure_ascii=False))

if __name__ == '__main__':
    main()
