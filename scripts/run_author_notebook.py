"""Execute a reviewed RF branch copied from the pinned author notebook.

Never executes the upstream notebook wholesale. New output directory is mandatory.
"""
import argparse
from datetime import datetime, timezone
import difflib
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import sys
import time
import zipfile

ROOT = Path(__file__).resolve().parents[1]
COMMIT = '7645cacfb304aa8666f109cba758a3933c579819'
EXPECTED = 'a05b276a287d9f2a944a7ac77ef85109d22d912ba6e4447dfa4609abd08b06aa'

def digest(data):
    return hashlib.sha256(data).hexdigest()

def save_json(p, value):
    p.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', required=True, help='New folder name under runs/')
    args = parser.parse_args()
    if Path(args.run).name != args.run or args.run in {'.','..'}:
        raise ValueError('Use a plain new run name')
    import nbformat
    from nbclient import NotebookClient
    from jupyter_client import KernelManager
    out = ROOT/'runs'/args.run
    out.mkdir(exist_ok=False)
    (out/'runner_source.py').write_bytes(Path(__file__).read_bytes())
    (out/'pyvenv.cfg').write_bytes((Path(sys.prefix)/'pyvenv.cfg').read_bytes())
    log = (out/'execution.log').open('x',encoding='utf-8',buffering=1)
    def record(s):
        message = f'{datetime.now(timezone.utc).isoformat()} {s}'
        print(message,flush=True)
        log.write(message+'\n')
    raw = (ROOT/'references/author/Ransomware_clean.ipynb').read_bytes()
    if digest(raw) != EXPECTED:
        raise ValueError('Upstream notebook checksum mismatch')
    (out/'upstream').mkdir()
    (out/'upstream/Ransomware_clean.ipynb').write_bytes(raw)
    source = nbformat.reads(raw.decode('utf-8'),as_version=4)
    (out/'data').mkdir()
    inventory = json.loads((ROOT/'references/downloads.json').read_text(encoding='utf-8'))
    checksums=[]
    for size in [64,128,256,512,1024]:
        archive = ROOT/f'references/author/datasets/final{size}.zip'
        data = archive.read_bytes()
        entry = next(x for x in inventory['files'] if x.get('path','').replace('\\','/')==archive.relative_to(ROOT).as_posix())
        if digest(data) != entry['sha256']:
            raise ValueError(f'ZIP checksum mismatch: {archive}')
        member = f'final{size}.csv'
        with zipfile.ZipFile(archive) as z:
            if z.namelist() != [member]:
                raise ValueError('Unexpected ZIP contents')
            csv_data=z.read(member)
        (out/'data'/member).write_bytes(csv_data)
        checksums.append({'segment_kib':size,'url':entry['url'],'zip_sha256':digest(data),
                          'csv_sha256':digest(csv_data),'csv_bytes':len(csv_data),'csv':f'data/{member}'})
    save_json(out/'data_checksums.json',checksums)
    env={'created_utc':datetime.now(timezone.utc).isoformat(),'source_commit':COMMIT,
         'python':sys.version,'executable':sys.executable,'prefix':sys.prefix,'base_prefix':sys.base_prefix,'platform':platform.platform(),
         'logical_cpus':os.cpu_count(),'packages':{d.metadata['Name']:d.version for d in importlib.metadata.distributions()}}
    save_json(out/'environment.json',env)
    (out/'requirements-lock.txt').write_text('\n'.join(f'{k}=={v}' for k,v in sorted(env['packages'].items(),key=lambda x:x[0].lower()))+'\n',encoding='utf-8')
    selected=[1,3,5,7,9,22,24,25,37,39]
    changes=[]
    def original(i):
        return source.cells[i].source
    def transform(i):
        s=original(i)
        if i==1:
            s=s.replace('%load_ext google.colab.data_table','')
        if i==3:
            s=s.replace('path+"final','data_path+"final')
        if i==7:
            s='import ast\n'+s.replace('eval(x)', 'ast.literal_eval(x)')
        if i==22:
            s=s.replace('from xgboost import XGBClassifier','')
        if i==39:
            s=s.replace('n_jobs=-1','n_jobs=1',1)
            s=s.replace('cv=cv,n_jobs=-1','cv=cv,n_jobs=2, error_score="raise"')
            s=s.replace('    calc_averages(n_scores)', '''    # Added evidence only: preserve unsummarised upstream cross_validate outputs.
    pd.DataFrame(n_scores).to_csv(path+f'RF_folds_{dataset}_{typefile}.csv', index=False)
    calc_averages(n_scores)''')
            s=s.replace('df=df.append(pd.DataFrame.from_dict(n_scores))','df=pd.concat([df, pd.DataFrame.from_dict(n_scores)])')
        if s!=original(i):
            changes.append({'upstream_index0':i,'diff':''.join(difflib.unified_diff(original(i).splitlines(True),s.splitlines(True),fromfile=f'upstream/cell_{i}',tofile=f'working/cell_{i}'))})
        return s
    heading=nbformat.v4.new_markdown_cell('''# DT083 — chạy nhánh RF của notebook tác giả

Nguồn: francasino/Ransomware_analysis, commit `'''+COMMIT+'''`.
Chỉ chạy nhánh CSV → parser → RF theo từng định dạng. Mọi output upstream đã được xóa khỏi bản làm việc.
Chỉ số upstream dưới đây tính từ 0; giao diện Jupyter hiển thị thứ tự cell của bản sao.
Giữ gamma 0/2, global min-max trước CV, 9 features, RF100/depth10/all features/OOB,
RepeatedStratifiedKFold(10,3,random_state=1), RF random_state=None.
Đây là chạy một phần notebook có điều chỉnh tương thích, không tái lập toàn bộ bài báo.
''')
    seed_fragment = next(line for line in original(14).splitlines() if 'np.random.seed(42)' in line)
    setup=nbformat.v4.new_code_cell('''from pathlib import Path
import sys, json, platform, hashlib
from datetime import datetime, timezone
print("RUN START UTC", datetime.now(timezone.utc).isoformat())
print("KERNEL", sys.executable)
print("PYTHON", sys.version)
print("SOURCE COMMIT", "'''+COMMIT+'''")
assert Path(sys.executable).resolve() == Path('''+repr(sys.executable)+''').resolve()
data_path = str(Path.cwd() / 'data') + '/'
path = str(Path.cwd() / 'artifacts') + '/'
Path(path).mkdir(exist_ok=False)
print("DATA CHECKSUMS", Path('data_checksums.json').read_text())
'''+ '\n# Exact seed fragment carried from skipped upstream plotting cell 14:\n'+seed_fragment+'\nprint("UPSTREAM CELL 14 RNG SEED", 42)\n')
    setup.metadata['dt083_upstream_fragment']={'index0':14,'source':seed_fragment}
    changes.append({'upstream_index0':14,'diff':'Carry exact seed line from skipped plotting cell into setup: '+seed_fragment})
    cells=[heading,setup]
    for i in selected:
        cells.append(nbformat.v4.new_markdown_cell(f'### Upstream cell index0={i} (cell {i+1} nếu đếm từ 1)'))
        c=nbformat.v4.new_code_cell(transform(i))
        c.metadata['dt083_upstream_index0']=i
        cells.append(c)
        if i==3:
            cells.append(nbformat.v4.new_code_cell('''data_rows=[]
for size, frame in datasets.items():
    info={'segment_kib':size,'rows':len(frame),'labels':frame.Filetype.value_counts().to_dict(),
          'size_bytes':frame[' size'].unique().tolist(), 'original_counts':frame[' Original'].value_counts().to_dict()}
    data_rows.append(info)
    assert set(frame.Filetype.unique()) == {0,1}
    assert frame[' size'].eq(size*1024).all()
    print(info)
Path('dataset_observed.json').write_text(json.dumps(data_rows,indent=2),encoding='utf-8')
'''))
        if i==25:
            cells.append(nbformat.v4.new_code_cell('''import numpy as np
for size, frame in datasets_test.items():
    X=frame.drop(['Filetype',' Original'],axis=1)
    assert X.shape[1] == 9, X.columns
    assert np.isfinite(X.to_numpy()).all(), (size, X.isna().sum())
    print(size, 'RF features in original order:', list(X.columns), 'rows:', len(X))
    frame.to_csv(path+f'parsed_{size}.csv',index=False)
'''))
    cells.append(nbformat.v4.new_code_cell('''import statistics
result_rows=[]
for size in [64,128,256,512,1024]:
    for category in [0,1,2,3,4,5]:
        fold=pd.read_csv(path+f'RF_folds_{size}_{category}.csv')
        assert len(fold)==30
        row={'segment_kib':size,'original_category':category,'folds':len(fold)}
        for metric in ['precision','recall','accuracy','f1']:
            row[metric+'_mean']=statistics.mean(fold['test_'+metric])
            row[metric+'_sample_sd']=statistics.stdev(fold['test_'+metric])
        result_rows.append(row)
summary=pd.DataFrame(result_rows)
summary.to_csv('metrics_summary.csv',index=False)
print(summary.to_string(index=False))
print('COMPLETED: 5 sizes x 6 categories x 30 folds = 900 fits')
print('END UTC', datetime.now(timezone.utc).isoformat())
'''))
    nb=nbformat.v4.new_notebook(cells=cells,metadata={'kernelspec':{'display_name':'Python (DT083 author isolated)','language':'python','name':'python3'},
             'dt083':{'source_commit':COMMIT,'upstream_sha256':EXPECTED,'selected_upstream_indices0':selected,'scope':'RF per-original-category classification only'}})
    save_json(out/'changes.json',changes)
    (out/'changes.diff').write_text('\n\n'.join(x['diff'] for x in changes),encoding='utf-8')
    skipped=[]
    for i,c in enumerate(source.cells):
        if c.cell_type=='code' and i not in selected:
            skipped.append({'upstream_index0':i,'reason': 'Alternative exploratory HEDGE/FIPS branch mutates loaded data; not RF path' if i in [11,12,18] else 'Plots, grid search, feature relevance, reduced-feature or SVC/XGBoost experiments outside selected RF classification path'})
    save_json(out/'cell_review.json',{'selected':selected,'skipped_code_cells':skipped,
              'review':'No shell/system/malware execution in selected cells. CSV data parsed with literal_eval. Global minmax retained as upstream; this is not a methodological correction.',
              'resource_adaptation':'RF n_jobs=1 and CV n_jobs=2 avoid nested oversubscription; error_score=raise prevents silent failed folds.',
              'nondeterminism':'RF random_state=None retained. CV split seed remains 1. Exact np.random.seed(42) line from upstream plotting cell 14 carried into setup. No new model seed or experiment tuning; parallel workers and skipped exploratory fits prevent claims of identical historic RNG state.'})
    nbformat.write(nb,out/'Ransomware_clean.working.ipynb')
    record(f'PREPARED source={COMMIT} selected={selected} interpreter={sys.executable}')
    km=KernelManager(kernel_name='python3')
    km.kernel_spec.argv=[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}']
    def on_start(cell,cell_index,**kwargs):
        record(f'CELL_START working_index0={cell_index} upstream_index0={cell.metadata.get("dt083_upstream_index0")}')
    def on_complete(cell,cell_index,**kwargs):
        # Save a checkpoint after every executed cell, including outputs and timings.
        nbformat.write(nb,out/'Ransomware_clean.executed.ipynb')
        record(f'CELL_SAVED working_index0={cell_index} execution_count={cell.get("execution_count")} outputs={len(cell.get("outputs",[]))}')
    client=NotebookClient(nb,km=km,timeout=3600,allow_errors=False,record_timing=True,
                          resources={'metadata':{'path':str(out)}},on_cell_start=on_start,on_cell_executed=on_complete)
    started=time.perf_counter()
    status='failed'
    try:
        client.execute(cwd=str(out))
        status='completed'
        record('SUCCESS 900 fits completed; summary saved by notebook')
    except Exception as exc:
        record(f'FAILURE {type(exc).__name__}: {exc}')
        raise
    finally:
        nbformat.write(nb,out/'Ransomware_clean.executed.ipynb')
        save_json(out/'execution_status.json',{'status':status,'wall_seconds':time.perf_counter()-started,
                  'end_utc':datetime.now(timezone.utc).isoformat(),'source_commit':COMMIT})
        artifacts=[]
        for p in sorted(out.rglob('*')):
            if p.is_file() and p.name != 'artifact_checksums.json':
                artifacts.append({'path':p.relative_to(out).as_posix(),'bytes':p.stat().st_size,'sha256':digest(p.read_bytes())})
        save_json(out/'artifact_checksums.json',artifacts)
        log.close()

if __name__ == '__main__':
    main()
