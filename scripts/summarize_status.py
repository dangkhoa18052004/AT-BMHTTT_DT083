"""Build submission status from actual saved artifacts only."""
import sys
import json
import xml.etree.ElementTree as ET
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import pandas as pd
from dt083.reporting import markdown_table

ROOT=Path(__file__).resolve().parents[1]

def tests(path):
    if not path.exists(): return 'Chưa có artifact'
    root=ET.parse(path).getroot()
    suites=[root] if root.tag=='testsuite' else list(root.iter('testsuite'))
    return f"{sum(int(s.attrib.get('tests',0)) for s in suites)} tests, {sum(int(s.attrib.get('failures',0)) for s in suites)} failures, {sum(int(s.attrib.get('errors',0)) for s in suites)} errors"

def main():
    lines=['# Trạng thái thực nghiệm và bàn giao','',
        'Tài liệu này sinh từ artifact đã lưu; không tự điền kết quả chưa đo. Các đường dẫn tương đối với DT083.','',
        '## Đã triển khai','',
        'CLI từng bước và pipeline; nguồn tổng hợp TXT/CSV/PDF/PNG/JPEG; manifest/SHA256; group split; nén ZIP/GZIP/BZIP2/AES-GCM, round-trip; sáu feature; B0/B1/M1/M2; validation threshold/model lock; subgroup/error/speed artifacts; demo; tài liệu tiếng Việt và gói nộp không kèm reference upstream/khóa.','',
        '## Dữ liệu đã thực sự tải/tạo','',
        'Tải PDF bài báo, notebook/code để đọc, năm ZIP feature CSV, metadata Zenodo. Commit 7645cacfb304aa8666f109cba758a3933c579819, SHA256 từng file trong references/downloads.json; mọi download đều thành công. Không tải/chạy malware. Không tải raw archive Zenodo và không có nguồn public trong corpus kiểm soát.','']
    for run in ['smoke','full']:
        root=ROOT/'runs'/run
        corpus=json.loads((root/'data/manifests/corpus_summary.json').read_text())
        metrics=pd.read_csv(root/'results/metrics_raw.csv')
        frame=pd.read_csv(root/'data/features/segments.csv')
        lines += [f"- **{run}**: {corpus['source_files']} source files / {corpus['source_groups']} template groups; {corpus['bytes']} byte source; {corpus['source_files']*5} derivatives; {len(frame)} segment rows gồm original/size/policy; {len(metrics)} model/seed/size/policy evaluations."]
    lines += ['', '## Kiểm thử và tái lập','',f"- Môi trường chính: {tests(ROOT/'results/tests.xml')}.",
              f"- Môi trường mới từ requirements-lock: {tests(ROOT/'results/tests-fresh.xml')}.",
              '- results/verification.json kiểm tra nguồn/dẫn xuất, group/hash leakage, test sets giống nhau và model checksum.',
              '- .venv-repro là môi trường mới độc lập, không dùng system-site-packages; fresh_environment.json ghi đối chiếu lock.',
              '- CSV tham khảo: 5 size × 10 folds × 3 seed = 150 lượt fit/evaluate; giới hạn row split trong author_reference/protocol.json.',
              '', '## Kết quả corpus kiểm soát — 64 KiB, interior','']
    summary=pd.read_csv(ROOT/'runs/full/results/metrics_summary.csv')
    cost=pd.read_csv(ROOT/'runs/full/results/tradeoff.csv')
    part=summary[(summary.segment_kib==64)&(summary.policy=='interior')]
    table=part[['model']].copy()
    for name in ['precision','recall','f1','fpr_archive']:
        table[name]=[f'{m:.4f} ± {s:.4f}' for m,s in zip(part[name+'_mean'],part[name+'_std'])]
    speeds=cost[(cost.segment_kib==64)&(cost.policy=='interior')].set_index('model')
    table['ms/segment read→features→predict']=[f"{speeds.loc[name,'end_to_end_ms_per_segment_mean']:.3f}" for name in table.model]
    lines += [markdown_table(table),'',
        'Mean±sample SD ba seed trên cùng corpus, không CI. Các size/policy còn lại trong runs/full/results/RESULTS.md. Chỉ cấp đoạn compressed/encrypted, không phải ransomware detection rates.',
        '', '## Kết quả tham khảo CSV tác giả','',
        'Xem results/author_reference/RESULTS.md. Đây là đường đối chiếu chọn lọc, không bảo đảm độc lập nguồn và không có raw byte speed. Không tuyên bố vượt paper.',
        '', '## Chi phí full và giới hạn','']
    total=json.loads((ROOT/'runs/full/results/pipeline_cost.json').read_text())
    lines += [f"Whole experiment wall time đã đo: {total['wall_s']:.2f} s. Đây bao gồm sinh/nén/mã hóa/train/artifact, không phải detection latency.",
              '',markdown_table(pd.DataFrame([{'stage':k,'seconds':f'{v:.3f}'} for k,v in total['stages_seconds'].items()])),
              '', 'Không còn bước thực thi thiết kế hiện tại bị sandbox chặn sau khi đã chạy ngoài sandbox. Các phần chưa thực hiện: raw Zenodo 6.3 GB; corpus public với 300–600 nguồn độc lập; own 512/1024 KiB; bootstrap group CI; model calibration; partial encryption và file-write/process sensor; báo cáo hoàn chỉnh/slide/video ngoài dàn ý.',
              '', '360 tệp full chỉ có 12 group. Điều kiện độc lập/đại diện của tài liệu thực chưa đạt. Framework sinh chung vẫn có thể tạo phụ thuộc giữa các họ. Header margin và size filtering có bias, đọc dataset/error cards trước khi diễn giải.',
              '', '## Lệnh dùng tiếp','', 'Chạy trong DT083:','', '```powershell',
              '.\\.venv\\Scripts\\python.exe -X utf8 scripts/run.py demo --config configs/full.json --run full --file data/derived/waves_01_png__aesgcm.bin --model M2 --seed 42 --kib 64 --policy interior',
              '.\\.venv\\Scripts\\python.exe -X utf8 scripts/run.py pipeline --config configs/full.json --run full-new',
              '.\\.venv\\Scripts\\python.exe -X utf8 scripts/fetch_zenodo_raw.py', '```',
              '', 'Lệnh raw là tùy chọn, chưa được chạy và không tự đưa archive vào training. Để tái tạo gói sau thay đổi artifact: scripts/package_submission.py. Hướng dẫn đầy đủ ở README.md.']
    (ROOT/'docs/STATUS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')

if __name__=='__main__': main()
