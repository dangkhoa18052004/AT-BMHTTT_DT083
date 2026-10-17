# DT083 — Phát hiện ransomware bằng entropy theo đoạn tệp

Nguyên mẫu Python phân biệt **đoạn compressed (0)** và **đoạn encrypted mô phỏng (1)**. Mã hóa AES-GCM không chứng minh có ransomware. Demo chỉ đọc corpus của dự án; không quét máy, chạy malware, xóa tệp hoặc dừng process.

## Cài đặt trên Windows PowerShell

Chạy trong thư mục `DT083`:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
```

Python đã kiểm tra: 3.12.7 / Windows 11. Các phiên bản đã cài được khóa trong `requirements-lock.txt`; `requirements.in` chỉ là danh sách phụ thuộc để phát triển, không dùng thay lock khi tái lập. Không cần activate hoặc cài package editable. Mỗi lần tạo corpus dùng tên run mới; chương trình từ chối ghi đè inventory/derived manifest.

## Một lệnh smoke

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/run.py pipeline --config configs/smoke.json --run smoke-new
```

60 tệp tổng hợp / 12 nhóm template, 64 KiB, 3 seed 42/123/2026, 2 policy và 4 model. `runs/smoke` là kết quả đã chạy trong phiên xây dựng. Chi phí toàn thí nghiệm của smoke được chia thành nhiều lệnh vì sandbox chặn train lần đầu; không có số wall time tổng hợp giả định cho phiên đó.

## Full: tạo corpus, train/evaluate ba seed

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/run.py pipeline --config configs/full.json --run full-new
```

360 tệp tổng hợp / **12 nhóm template**, 64/128/256 KiB. Đây chưa đạt mục tiêu 300–600 **nguồn độc lập thực/public**. Các tệp khác seed, độ phân giải, định dạng từ cùng họ mẫu vẫn có chung `source_group_id`. Mục tiêu corpus độc lập cần thu thập bổ sung nhiều nguồn public có provenance và giấy phép, rồi kiểm tra nhóm và duplicate. Không suy ra tính đại diện chỉ từ số tệp.

Có CLI cho từng bước. Ví dụ run mới `full-steps`:

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/run.py prepare --config configs/full.json --run full-steps
.\.venv\Scripts\python.exe -X utf8 scripts/run.py derive --config configs/full.json --run full-steps
.\.venv\Scripts\python.exe -X utf8 scripts/run.py split --config configs/full.json --run full-steps
.\.venv\Scripts\python.exe -X utf8 scripts/run.py extract --config configs/full.json --run full-steps
.\.venv\Scripts\python.exe -X utf8 scripts/run.py train --config configs/full.json --run full-steps
.\.venv\Scripts\python.exe -X utf8 scripts/run.py benchmark --config configs/full.json --run full-steps
.\.venv\Scripts\python.exe -X utf8 scripts/run.py report --config configs/full.json --run full-steps
```

`train` vừa chọn threshold trên validation vừa đánh giá test sau khi ghi cấu hình khóa. RF có tham số khai báo trước, giống nhau giữa B1/M1/M2. Không có scaler/imputer. B0 dùng threshold entropy chọn trên validation từ ứng viên sinh bằng train. Không điều chỉnh dựa trên test. Nếu một split thiếu hai lớp, tổ hợp đó được ghi là skipped, không điền metric.

## Demo

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/run.py demo --config configs/full.json --run full --file data/derived/waves_01_png__aesgcm.bin --model M2 --seed 42 --kib 64 --policy interior
```

Đường dẫn `--file` tương đối với `runs/full`, chỉ được nằm trong `data/source` hoặc `data/derived` của run. Demo hiển thị feature, offset, score, lớp dự đoán và ms cho từng đoạn. Score là đầu ra model, **không phải xác suất tệp là ransomware**. B0 score là entropy. Không có quy tắc gộp cấp tệp. Tệp ngắn trả về `too_small`.

## Kiểm thử

```powershell
.\.venv\Scripts\python.exe -X utf8 -m pytest -q --junitxml=results/tests.xml --basetemp=results/pytest-local
```

28 tests bao gồm test kiểm tra lựa chọn threshold rút gọn khớp metric tham chiếu. Kết quả chạy trong hai môi trường ghi ở `results/tests.xml` và `results/tests-fresh.xml`. Một số sandbox Windows chặn named pipe dùng bởi joblib và thư mục tạm pytest; chạy trên PowerShell bình thường nếu gặp `WinError 5`. Không âm thầm đổi RF sang ít luồng để làm benchmark đẹp hơn. Không dùng lại một `--basetemp` thuộc tác vụ khác.

## Đối chiếu nghiên cứu tác giả

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/fetch_references.py
.\.venv\Scripts\python.exe -X utf8 scripts/author_reference.py --sizes 64 128 256 512 1024 --folds 10 --seeds 42 123 2026
```

Chỉ tải code/notebook để đọc, không thực thi notebook hoặc `eval` CSV. Tệp tải được ghi checksum, commit và schema trong `references/downloads.json`, `references/schema_audit.json`. Trình tải lần sau sẽ chụp commit main mới; nếu cần đúng phiên này, dùng commit đã ghi `7645cacfb304aa8666f109cba758a3933c579819` và đối chiếu checksum. Kết quả tham khảo chỉ từ CSV nằm ở `results/author_reference`; **không có bảo đảm độc lập theo nguồn và không có tốc độ end-to-end**.

Zenodo đã tải **metadata**, chưa tải `dataset_raw.zip` 6.300.255.462 byte. Code GitHub không có LICENSE chung trong tree được kiểm tra; một số module có header riêng. Không phân phối lại notebook/CSV/ZIP tác giả trong submission. Metadata Zenodo ghi CC BY 4.0 nhưng không tự suy rộng giấy phép đó cho toàn GitHub.

Nếu muốn tải riêng raw sau phiên này (cần hơn 6,3 GB, không tự trích xuất/chạy):

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/fetch_zenodo_raw.py
```

Script kiểm tra size/MD5 server trước khi chấp nhận file. Việc tải archive không tự bổ sung provenance/group IDs hoặc đưa nó vào thí nghiệm kiểm soát.

## Đọc artifact

- `runs/full/results/RESULTS.md`: bảng mean ± sample SD của các seed.
- `metrics_raw.csv`, `test_predictions.csv`: metrics/dự đoán chưa tổng hợp; encrypted là positive.
- `metrics_subgroups.csv`: ZIP/GZIP/BZIP2, định dạng nguồn, original bổ sung; có mẫu số và số nhóm. Subgroup chỉ có một lớp không có ý nghĩa F1 nhị phân đầy đủ; dùng FPR riêng cho archive.
- `sample_counts.csv`, `excluded_by_split.csv`: kiểm tra số mẫu/nhóm và selection bias theo size/policy/split.
- `locked_*.json`: feature, threshold, validation metrics và checksum model đã khóa trước test.
- `benchmark_raw.csv`, `benchmark_protocol.json`: đọc byte, feature, predict, toàn đường phát hiện; ms/đoạn, MiB/s, batch, warm-up, luồng, RAM.
- `pipeline_cost.json`: wall time của cả thí nghiệm full, khác với detection benchmark.
- `ablation_M2_minus_M1.csv`, `header_sensitivity.csv`, `tradeoff.csv`, `tradeoff.png`: đóng góp riêng và chi phí.
- `confusion_*.png`: confusion matrix cộng seed; nguồn có thể lặp giữa seed, không dùng như cỡ mẫu độc lập.
- `data/manifests/inventory.csv`, `derived_seed_*.csv`, `splits_*.csv`: provenance và group split.
- `models/*.joblib`: model đã fit. Chỉ load model do dự án này tạo; joblib không phải định dạng an toàn cho file tải từ nguồn không tin cậy.

Các thư mục gốc `data`, `models`, `results` là điểm tổ chức dự án; dữ liệu và model mỗi thí nghiệm thực tế nằm trong `runs/<run>/` để tránh trộn smoke/full. AES dùng khóa mới an toàn mỗi lần tạo: raw ciphertext/checksum thay đổi giữa lần chạy; source tổng hợp và phép chia giữ seed. Không hứa metric giống từng bit ở môi trường khác.

## Giới hạn và xử lý lỗi

Chỉ corpus tổng hợp, ít họ mẫu; không có video/audio/bin, malware, partial encryption hoặc dữ liệu hành vi. Header margin không bảo đảm bỏ mọi metadata. Tệp nén quá ngắn bị loại, không padding/nối tệp. BZIP2 và ảnh đã nén có thể rất giống ciphertext. Ba seed đo ổn định split trên cùng corpus, không phải ba corpus độc lập. Chưa bootstrap confidence interval; không dùng segment IID để suy ra CI.

Không có dữ liệu: chạy prepare → derive → split → extract trước train. Config khác run hiện hữu: dùng `--run` mới. Corpus bị sửa: checksum sẽ báo lỗi, tạo run mới hoặc khôi phục từ nguồn đã xác minh. Thiếu dung lượng/RAM: smoke có cấu hình riêng; đừng thay full mà vẫn gọi kết quả là full. Hỗ trợ 512/1024 KiB: tạo config mới đổi `segment_kib`, dùng run mới; nhiều biến đổi có thể không đủ byte, xem excluded trước khi diễn giải.

Tài liệu: [dataset card](docs/dataset_card.md), [reproduction card](docs/reproduction_card.md), [công thức](docs/features.md), [paper mapping](docs/paper_mapping.md), [phân tích lỗi](docs/error_analysis.md), [khung báo cáo](docs/report_outline.md), [trạng thái](docs/STATUS.md).

Đóng gói hợp lệ sau khi chạy xong:

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/package_submission.py
```

Package gồm code, docs, config, kiểm thử, manifest, feature, metric/hình và model tự tạo; bỏ reference của tác giả, corpus có thể sinh lại, khóa mô phỏng và môi trường ảo. Checksum package trong `results/submission_sha256.txt`.
