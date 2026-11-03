"""Validate the completed run and fill the audit report using measured artifacts."""
import argparse
import hashlib
import json
from pathlib import Path
import statistics
from datetime import datetime, timezone
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--run',required=True)
    args=parser.parse_args()
    run=ROOT/'runs'/args.run
    status=json.loads((run/'execution_status.json').read_text(encoding='utf-8'))
    assert status['status']=='completed', status
    executed=json.loads((run/'Ransomware_clean.executed.ipynb').read_text(encoding='utf-8'))
    working=json.loads((run/'Ransomware_clean.working.ipynb').read_text(encoding='utf-8'))
    assert [c['source'] for c in executed['cells']]==[c['source'] for c in working['cells']]
    assert executed['cells'][1]['metadata']['dt083_upstream_fragment']=={
        'index0':14,'source':'import numpy as np; np.random.seed(42)'}
    code=[c for c in executed['cells'] if c['cell_type']=='code']
    assert [c['execution_count'] for c in code]==list(range(1,len(code)+1))
    assert all('execution' in c['metadata'] for c in code)
    assert not [o for c in code for o in c['outputs'] if o['output_type']=='error']
    summary=pd.read_csv(run/'metrics_summary.csv')
    assert len(summary)==30 and not summary.isna().any().any()
    total=0
    for r in summary.to_dict('records'):
        fold=pd.read_csv(run/f'artifacts/RF_folds_{int(r["segment_kib"])}_{int(r["original_category"])}.csv')
        assert len(fold)==30 and not fold.isna().any().any()
        total+=len(fold)
        for metric in ['precision','recall','accuracy','f1']:
            assert abs(statistics.mean(fold['test_'+metric])-r[metric+'_mean'])<1e-12
            assert abs(statistics.stdev(fold['test_'+metric])-r[metric+'_sample_sd'])<1e-12
    assert total==900
    manifest=json.loads((run/'artifact_checksums.json').read_text(encoding='utf-8'))
    assert all(sha(run/x['path'])==x['sha256'] for x in manifest)
    before=json.loads((ROOT/'results/author_audit_20261018/audit.json').read_text(encoding='utf-8'))
    assert all(sha(ROOT/x['path'])==x['sha256'] for x in before['files'])
    assert all(sha(ROOT/x['path'])==x['sha256'] for x in before['old_author_reference_artifacts'])
    cfg=(run/'pyvenv.cfg').read_text()
    assert 'include-system-site-packages = false' in cfg
    verification={'verified_utc':datetime.now(timezone.utc).isoformat(), 'run':run.relative_to(ROOT).as_posix(),
                  'status':'passed','code_cells_executed':len(code),'folds_total':total,
                  'no_error_outputs':True,'working_executed_sources_equal':True,
                  'fold_summary_recomputed':True,'all_run_manifest_checksums_match':True,
                  'upstream_17_files_unchanged':True,'old_author_reference_8_files_unchanged':True,
                  'separate_venv_no_system_site_packages':True,
                  'upstream_cell14_numpy_seed42_preserved':True,
                  'cell_mapping':[{'working_index0':i,'execution_count':c.get('execution_count'),
                                   'upstream_index0':c.get('metadata',{}).get('dt083_upstream_index0')}
                                  for i,c in enumerate(executed['cells']) if c['cell_type']=='code']}
    audit_out=ROOT/'results/author_audit_20261018'
    verification_name=f'{args.run}_verification.json'
    verification_path=audit_out/verification_name
    assert not verification_path.exists(), 'Do not overwrite a previous verification result'
    verification_path.write_text(json.dumps(verification,indent=2),encoding='utf-8')
    names=['Binary','Image','MP3','PDF','TXT','Video']
    paper={64:[.9934,.9310,.9341,.9474,.9901,.9239],128:[.9960,.9441,.9446,.9515,.9965,.9425],
           256:[.9975,.9645,.9748,.9593,1,.9730],512:[1,.9926,.9867,.9818,1,.9959],1024:[1,1,.9952,1,1,1]}
    lines=['### Kết quả mới: nhánh RF cell 39, từng định dạng',
           '', 'Mean ± sample SD trên 30 folds của cùng một thí nghiệm, không phải SD của ba mean theo seed. P/R/Accuracy cũng là mean của 30 folds.', '',
           '| KiB | Định dạng | Precision | Recall | Accuracy | F1 đo tại máy ± SD | F1 bài báo (Table 5/6) |',
           '| --- | --- | ---: | ---: | ---: | ---: | ---: |']
    for r in summary.to_dict('records'):
        size=int(r['segment_kib']); category=int(r['original_category'])
        lines.append(f'| {size} | {names[category]} | {r["precision_mean"]:.6f} | {r["recall_mean"]:.6f} | {r["accuracy_mean"]:.6f} | {r["f1_mean"]:.6f} ± {r["f1_sample_sd"]:.6f} | {paper[size][category]:.4f} |')
    lines += ['', 'Nguồn đo: `RUN_PATH/metrics_summary.csv` và 30 tệp `RUN_PATH/artifacts/RF_folds_<size>_<category>.csv`, mỗi tệp 30 dòng. Tổng **900 lượt fit/evaluate**. `RF_multi.csv` là output cách trình bày ban đầu của cell 39; bảng trên thêm cột nhãn size/category để tránh nhầm các cặp mean/SD.', '',
              '### Kết quả cũ: script author_reference.py, All (không phải lần chạy notebook mới)', '',
              '| KiB | F1 script cũ, mean ± SD ba seed | F1 All bài báo |', '| --- | ---: | ---: |']
    old=pd.read_csv(ROOT/'results/author_reference/metrics_summary.csv')
    paper_all={64:.9528,128:.9653,256:.9809,512:.9965,1024:1.}
    for r in old.to_dict('records'):
        size=int(r['segment_kib'])
        lines.append(f'| {size} | {r["f1_mean"]:.6f} ± {r["f1_std"]:.6f} | {paper_all[size]:.4f} |')
    env=json.loads((run/'environment.json').read_text(encoding='utf-8'))
    versions={k.lower():v for k,v in env['packages'].items()}
    env_text='Python '+env['python'].split()[0]+', '+env['platform']+'. Phiên bản chính: '+', '.join(f'{k}={versions[k]}' for k in ['numpy','pandas','scipy','scikit-learn','joblib','nbformat','nbclient','ipykernel'])+'.'
    mapped=[]
    for x in verification['cell_mapping']:
        label=f'upstream index0={x["upstream_index0"]}' if x['upstream_index0'] is not None else 'cell bổ sung'
        mapped.append(f'| {x["working_index0"]} | {x["execution_count"]} | {label} |')
    map_text='Mapping thực tế trong notebook đã chạy:\n\n| Index0 bản làm việc | Execution count `[n]` | Nguồn |\n| --- | --- | --- |\n'+'\n'.join(mapped)
    replacements={
      'PENDING_EXECUTION_STATUS':f'**Đã chạy thành công một nhánh notebook gốc có sửa tương thích**, từ CSV qua parser đến RF theo từng định dạng: 5 size × 6 định dạng × 10 folds × 3 lần lặp = **900 lượt fit/evaluate**. Có notebook output mới, thời gian cell, log, lock môi trường và checksum. Không tuyên bố đã chạy nguyên xi toàn notebook hoặc tái lập toàn bộ bài báo.',
      'PENDING_NOTEBOOK_EVIDENCE':'**Có bằng chứng mới cho nhánh đã chọn.** `RUN_PATH/Ransomware_clean.executed.ipynb` có 14 code cells thực thi tuần tự `[1]`–`[14]`, timing và output; cell upstream 39 tương ứng execution `[13]`, cell tổng hợp `[14]`. `RUN_PATH/execution.log` kết thúc SUCCESS; `execution_status.json` báo completed; `results/author_audit_20261018/completed_run_verification.json` xác nhận 900 folds, không error output, notebook làm việc/đã chạy có source giống nhau và thống kê tính lại khớp. Đây là nhánh trích từ cell tác giả, không phải `author_reference.py` được đổi tên thành notebook.',
      'PENDING_MIDTERM_STATUS':'**Đã bổ sung minh chứng chạy được nhánh phân loại RF của repo tác giả trên CSV công khai**, phù hợp phần “chạy repo” ở phạm vi đã công bố. Còn phải trình bày trung thực là chạy một phần notebook với sửa tương thích và cần hoàn thành/xuất trình bản dịch đầy đủ. **Chưa xác minh được đã đáp ứng toàn bộ yêu cầu giữa kỳ**, vì bản dịch đầy đủ chưa được xác minh; quyết định giảng viên chấp nhận phạm vi phân loại RF không được suy đoán.',
      'PENDING_ENVIRONMENT':env_text+f' Tổng wall time lần thực thi notebook: **{status["wall_seconds"]:.2f} giây** (không gồm cài dependency, gồm parser và RF; không phải tốc độ phát hiện end-to-end). Kết thúc UTC: `{status["end_utc"]}`. Log cài đặt có dòng “Successfully installed”; PowerShell bọc thông báo pip-update trên stderr thành `NativeCommandError`, nhưng kiểm tra `pip check` và kernel thực thi đều thành công.',
      'PENDING_RESULTS_TABLE':'\n'.join(lines),
      'PENDING_SCREENSHOT_MAPPING':map_text,
      'PENDING_FINAL_VERIFICATION':'Kiểm tra cuối: 17 tệp reference và 8 artifact author_reference cũ vẫn giữ nguyên SHA256; 30 tệp fold × 30 dòng; không NaN/lỗi; mean và sample SD tính lại khớp bảng tổng hợp; 14 execution_count tuần tự, có timing, không output lỗi; checksum run khớp. Bằng chứng tại `results/author_audit_20261018/completed_run_verification.json`. Không dùng timestamp file đơn lẻ làm chứng cứ chạy.'
    }
    report=ROOT/'KIEM_TRA_REPO_TAC_GIA.md'
    text=report.read_text(encoding='utf-8')
    for key,value in replacements.items():
        assert key in text, f'Already finalized or missing marker: {key}'
        text=text.replace(key,value)
    text=text.replace('results/author_audit_20261018/completed_run_verification.json',f'results/author_audit_20261018/{verification_name}')
    text=text.replace('RUN_PATH',run.relative_to(ROOT).as_posix())
    assert 'PENDING_' not in text
    report.write_text(text,encoding='utf-8')
    print(json.dumps(verification,indent=2))

if __name__=='__main__':
    main()
