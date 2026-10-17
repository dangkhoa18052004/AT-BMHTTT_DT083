# Hướng dẫn chi tiết chạy chương trình DT083

Tài liệu dành cho Windows và PowerShell, áp dụng cho dự án tại:

```text
E:\Project\AT&BMHTTT\DT083
```

Chương trình chạy bằng dòng lệnh. Nó đọc các đoạn byte trong corpus của dự án, tính đặc trưng và dự đoán **compressed** hoặc **encrypted**. Kết quả hiển thị trong terminal và lưu thành JSON, CSV, hình PNG, model. Nhãn encrypted không chứng minh tệp là ransomware.

## 1. Chọn cách chạy phù hợp

| Bạn muốn làm gì? | Đọc phần | Cần huấn luyện lại? |
| --- | --- | --- |
| Xem chương trình hoạt động ngay trên máy hiện tại | 2 và 3 | Không, dùng dữ liệu/model đã có |
| Kiểm tra toàn bộ quy trình bằng bộ dữ liệu nhỏ | 5 | Có, chạy smoke trong thư mục run mới |
| Chạy lại toàn bộ thí nghiệm full | 6 | Có, tạo corpus và model mới |
| Chạy và kiểm tra từng bước | 7 | Tùy bước |
| Xem bảng kết quả, hình và phân tích lỗi | 8 | Không |
| Cài trên máy khác hoặc dùng gói ZIP | 4 và 12 | Cần sinh lại corpus để chạy demo |

**Để bắt đầu trên máy này: làm phần 2, rồi sao chép lệnh ở phần 3.**

Các khối `powershell` dưới đây là lệnh để chạy. Chỉ sao chép nội dung trong khối; không gõ thêm ký hiệu dấu nhắc `PS ...>` hoặc các dòng đánh dấu khối lệnh.

## 2. Mở terminal và vào đúng thư mục

### Cách mở

Bạn có thể dùng một trong hai cách:

- Mở Windows Terminal và chọn tab PowerShell.
- Mở thư mục `DT083` trong VS Code, chọn **Terminal → New Terminal**, rồi chọn PowerShell.

Trong terminal, chạy:

```powershell
Set-Location -LiteralPath 'E:\Project\AT&BMHTTT\DT083'
Get-Location
```

`Get-Location` cần hiển thị thư mục `DT083`. Đường dẫn có ký tự `&`, nên giữ nguyên dấu nháy đơn khi dùng lệnh trên.

Kiểm tra các thành phần cần thiết:

```powershell
Test-Path -LiteralPath '.\scripts\run.py'
Test-Path -LiteralPath '.\.venv\Scripts\python.exe'
Test-Path -LiteralPath '.\runs\full\models\42_64_interior_M2.joblib'
Test-Path -LiteralPath '.\runs\full\data\derived\waves_01_png__aesgcm.bin'
```

Trên workspace đã xây dựng, cả bốn dòng cần trả về `True`. Nếu môi trường `.venv` chưa có, làm phần 4. Nếu dữ liệu/model chưa có, làm phần 5 hoặc 6 trước khi demo, rồi dùng tên run vừa tạo.

Kiểm tra Python của dự án:

```powershell
.\.venv\Scripts\python.exe --version
```

Môi trường đã kiểm tra dùng Python **3.12.7**. Các lệnh hướng dẫn gọi trực tiếp Python trong `.venv`, nên không cần activate môi trường.

## 3. Chạy demo ngay bằng dữ liệu/model có sẵn

### 3.1. Demo một tệp đã mã hóa mô phỏng

Chạy nguyên dòng sau trong thư mục `DT083`:

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/run.py demo --config configs/full.json --run full --file data/derived/waves_01_png__aesgcm.bin --model M2 --seed 42 --kib 64 --policy interior
```

Lệnh này sử dụng model đã huấn luyện, đọc tối đa hai đoạn 64 KiB của một tệp AES-GCM trong corpus và hiển thị kết quả. Nó không chạy lại toàn bộ thí nghiệm.

### 3.2. Demo một tệp nén ZIP

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/run.py demo --config configs/full.json --run full --file data/derived/waves_01_png__zip.bin --model M2 --seed 42 --kib 64 --policy interior
```

Tệp này có transform thật là ZIP-DEFLATE. Model vẫn có thể dự đoán sai; demo dùng để quan sát kết quả, không bảo đảm mỗi tệp sẽ được phân loại đúng.

### 3.3. Đổi sang model M1

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/run.py demo --config configs/full.json --run full --file data/derived/waves_01_png__aesgcm.bin --model M1 --seed 42 --kib 64 --policy interior
```

### 3.4. Hiểu các tham số

| Tham số | Ý nghĩa |
| --- | --- |
| `demo` | Chỉ dự đoán trên tệp được chọn |
| `--config configs/full.json` | Cấu hình phải khớp với run đã tạo |
| `--run full` | Dữ liệu, model và kết quả thuộc thư mục `runs/full` |
| `--file data/derived/...bin` | Đường dẫn tương đối **bên trong run**, không phải đường dẫn tương đối với `DT083` |
| `--model M2` | Chọn B0, B1, M1 hoặc M2 |
| `--seed 42` | Chọn model của seed 42; full đã chạy cả 42, 123 và 2026 |
| `--kib 64` | Kích thước đoạn; 64 KiB = 65.536 byte |
| `--policy interior` | Lấy đoạn bên trong tệp, bỏ margin 4.096 byte ở hai đầu |
| `-X utf8` | Cho Python sử dụng UTF-8 để hiển thị/lưu văn bản thuận tiện trên Windows |

`--policy start` lấy đoạn từ đầu tệp và dùng model tương ứng với policy đó. Với full hiện tại, có model cho 64/128/256 KiB và hai policy `interior`/`start`. Tệp được demo cũng phải đủ lớn cho kích thước và margin đã chọn.

### 3.5. Đọc kết quả JSON

Output có cấu trúc như sau; các chữ mô tả là chỗ giữ vị trí, không phải số liệu đo:

```text
file: đường dẫn tệp đã đọc
model: model được chọn
segments:
  - offset: vị trí bắt đầu đoạn, tính bằng byte
    length: số byte trong đoạn
    features: các đặc trưng mà model sử dụng
    score: đầu ra của model
    predicted_class: compressed hoặc encrypted
    elapsed_ms: thời gian xử lý đoạn trong lần demo này
status: ok hoặc too_small
notice: giải thích giới hạn của score
```

- `entropy` có đơn vị bit/byte, thường trong khoảng 0 đến 8.
- M1 dùng năm đặc trưng thống kê; M2 thêm `recompress_ratio`.
- `score` của RF là đầu ra mô hình cho lớp encrypted, **không phải xác suất tệp là ransomware**. B0 có score là entropy.
- Mỗi phần tử trong `segments` là một dự đoán cấp đoạn. Chương trình chưa gộp thành kết luận chung cho cả tệp.
- `too_small` nghĩa là không có đoạn hoàn chỉnh theo cấu hình; chương trình không padding hoặc nối thêm byte.
- Thời gian demo một đoạn có thể khác benchmark theo batch, vì cách gọi model và overhead khác nhau.

Demo được lưu tại:

```text
runs\full\results\demo.json
```

Đọc lại bằng terminal:

```powershell
Get-Content -Encoding UTF8 -LiteralPath '.\runs\full\results\demo.json'
```

Mỗi lần demo cùng run sẽ cập nhật `demo.json`. Nếu muốn giữ một kết quả để trình bày, sao chép sang tên riêng sau lần demo đó:

```powershell
Copy-Item -LiteralPath '.\runs\full\results\demo.json' -Destination '.\runs\full\results\demo-aes-m2.json'
```

## 4. Cài đặt khi chưa có môi trường hoặc chuyển sang máy khác

### 4.1. Kiểm tra Python hệ thống

```powershell
python --version
```

Nếu Windows không nhận lệnh `python`, thử:

```powershell
py -3.12 --version
```

Nếu cả hai không hoạt động, cài Python 3.12 rồi mở lại terminal. Đây là phiên bản đã dùng để kiểm tra dự án và lock.

### 4.2. Tạo môi trường ảo

Chỉ làm bước tạo môi trường khi `.venv` chưa có. Trong thư mục `DT083`:

```powershell
python -m venv .venv
```

Nếu dùng Python Launcher, thay lệnh tạo bằng:

```powershell
py -3.12 -m venv .venv
```

### 4.3. Cài thư viện đúng phiên bản

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -m pip check
```

Cài thư viện cần kết nối mạng hoặc package cache đầy đủ. `pip check` thành công thường hiển thị `No broken requirements found.`

Dùng `requirements-lock.txt` khi tái lập. `requirements.in` là danh sách phụ thuộc phát triển, không khóa các phiên bản.

### 4.4. Kiểm tra CLI

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/run.py --help
```

CLI cần hiển thị các bước `pipeline`, `prepare`, `derive`, `split`, `extract`, `train`, `benchmark`, `report`, `demo`.

## 5. Chạy smoke: kiểm tra toàn bộ pipeline với corpus nhỏ

Smoke tạo 60 tệp tổng hợp thuộc 12 nhóm template, sinh các biến thể, trích đặc trưng 64 KiB, train/evaluate ba seed và xuất bảng/hình.

Tạo tên run mới tự động rồi chạy:

```powershell
$runSmoke = 'smoke-' + (Get-Date -Format 'yyyyMMdd-HHmmss')
.\.venv\Scripts\python.exe -X utf8 scripts/run.py pipeline --config configs/smoke.json --run $runSmoke
```

Tên run chứa thời điểm giúp tránh đụng dữ liệu đã tồn tại. Nó là tên thư mục, không phải một đường dẫn. Không dùng `--run smoke` để chạy lại toàn pipeline trên corpus smoke đã có, vì chương trình từ chối ghi đè inventory/dẫn xuất.

Terminal sẽ lần lượt ghi các stage:

```text
Stage prepare
Stage derive
Stage split
Stage extract
Stage train
Stage benchmark
Stage report
```

Chờ lệnh kết thúc và dấu nhắc PowerShell xuất hiện trở lại. Kiểm tra mã kết thúc **ngay sau lệnh chạy pipeline**:

```powershell
$LASTEXITCODE
```

Giá trị `0` là thành công. Xem kết quả của run vừa tạo:

```powershell
Get-Content -Encoding UTF8 -LiteralPath ".\runs\$runSmoke\results\RESULTS.md"
```

Giữ nguyên cửa sổ PowerShell nếu còn dùng biến `$runSmoke`. Nếu đã mở terminal mới, thay `$runSmoke` bằng tên thư mục thực tế trong `runs`.

## 6. Chạy full: tái tạo toàn bộ thí nghiệm

Full hiện được cấu hình:

| Thành phần | Giá trị |
| --- | --- |
| Tệp nguồn | 360 tệp tổng hợp: TXT, CSV, PDF, PNG, JPEG |
| Nhóm nguồn | 12 họ template; các biến thể cùng họ giữ chung split |
| Dẫn xuất | Original, ZIP, GZIP, BZIP2, AES-GCM; tổng 1.800 tệp |
| Kích thước đoạn | 64, 128, 256 KiB |
| Seed | 42, 123, 2026 |
| Sampling | `interior`, `start` |
| Model | B0, B1, M1, M2 |
| Số tổ hợp đánh giá | 72 nếu mọi split đều có đủ hai lớp |

Chạy:

```powershell
$runFull = 'full-' + (Get-Date -Format 'yyyyMMdd-HHmmss')
.\.venv\Scripts\python.exe -X utf8 scripts/run.py pipeline --config configs/full.json --run $runFull
```

Lần full đã đo trên máy này mất khoảng **31 phút**, bao gồm sinh corpus, nén/mã hóa, trích đặc trưng, huấn luyện, benchmark và xuất artifact. Thời gian chạy lại có thể khác theo tải máy, I/O và phiên bản code; đây không phải thời gian dự đoán một tệp. Cần dung lượng cho các bản nguồn và dẫn xuất ngoài kích thước của gói ZIP nộp bài.

Không đóng terminal khi đang chạy. Theo dõi log từ **một cửa sổ PowerShell khác**, thay `<ten-run>` bằng tên run thực tế:

```powershell
Get-Content -Encoding UTF8 -LiteralPath 'E:\Project\AT&BMHTTT\DT083\runs\<ten-run>\results\run.log' -Tail 20 -Wait
```

`Ctrl+C` trong cửa sổ theo dõi sẽ dừng theo dõi log. `Ctrl+C` trong cửa sổ chạy pipeline sẽ ngắt thí nghiệm; xem phần 10 để xử lý.

Sau khi full kết thúc thành công:

```powershell
Get-Content -Encoding UTF8 -LiteralPath ".\runs\$runFull\results\RESULTS.md"
```

Demo bằng run mới:

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/run.py demo --config configs/full.json --run $runFull --file data/derived/waves_01_png__aesgcm.bin --model M2 --seed 42 --kib 64 --policy interior
```

**360 tệp không phải 360 nguồn độc lập**: corpus full chỉ có 12 nhóm template. Kết quả thuộc corpus tổng hợp, không đại diện toàn bộ tài liệu thực hoặc ransomware ngoài thực tế.

## 7. Chạy từng bước để học hoặc kiểm tra lỗi

Tạo một tên run mới trong cùng phiên PowerShell:

```powershell
$runSteps = 'steps-' + (Get-Date -Format 'yyyyMMdd-HHmmss')
```

Chạy các lệnh **theo thứ tự**; chỉ chạy bước tiếp theo khi bước trước kết thúc thành công.

### Bước 1 — Tạo corpus nguồn

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/run.py prepare --config configs/smoke.json --run $runSteps
```

Sinh source files và `data/manifests/inventory.csv` bên trong run.

### Bước 2 — Tạo bản dẫn xuất và kiểm tra khôi phục

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/run.py derive --config configs/smoke.json --run $runSteps
```

Tạo bản original/nén/mã hóa, kiểm tra round-trip và ghi `derived.csv`, `round_trip.json`. Tệp nguồn giữ nguyên.

### Bước 3 — Chia train/validation/test theo group

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/run.py split --config configs/smoke.json --run $runSteps
```

Ghi `splits_42.csv`, `splits_123.csv`, `splits_2026.csv` và manifest dẫn xuất có split tương ứng.

### Bước 4 — Lấy đoạn và trích đặc trưng

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/run.py extract --config configs/smoke.json --run $runSteps
```

Ghi `data/features/segments.csv`, thống kê tệp bị loại và thời gian trích feature.

### Bước 5 — Train, chọn threshold và đánh giá test

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/run.py train --config configs/smoke.json --run $runSteps
```

Train B0/B1/M1/M2, chọn threshold trên validation, khóa cấu hình trước test và ghi model/dự đoán/metrics. Không có lệnh `evaluate` riêng: đánh giá nằm trong bước `train` hiện tại.

### Bước 6 — Đo tốc độ từ byte thực

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/run.py benchmark --config configs/smoke.json --run $runSteps
```

Đọc lại đoạn byte, tính feature và predict; lưu timing từng phần và protocol batch/warm-up/luồng.

### Bước 7 — Xuất bảng, hình và phân tích lỗi

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/run.py report --config configs/smoke.json --run $runSteps
```

Tạo `RESULTS.md`, confusion matrices, `tradeoff.png`, ablation và error analysis. Bước này cần đã có cả kết quả train và benchmark.

Để dùng full với cách chạy từng bước, thay `configs/smoke.json` bằng `configs/full.json` ở **mọi lệnh**, và chọn một run mới. Các lệnh từng bước không tự ghi tổng wall time toàn thí nghiệm như lệnh `pipeline`.

## 8. Xem kết quả và biết file nào cần mở

Ví dụ dưới đây dùng run `full` đã có. Với run mới, thay `full` bằng tên run tương ứng.

| Tệp/thư mục | Dùng để làm gì? |
| --- | --- |
| `runs/full/results/RESULTS.md` | Bảng metrics trung bình ± SD qua seed |
| `runs/full/results/metrics_raw.csv` | Metric từng seed, size, policy, model |
| `runs/full/results/test_predictions.csv` | Dự đoán từng đoạn test, score, offset và nhãn thật |
| `runs/full/results/metrics_subgroups.csv` | Kết quả từng ZIP/GZIP/BZIP2 và định dạng nguồn |
| `runs/full/results/metrics_subgroups_summary.csv` | Tổng hợp subgroup qua seed, gồm mẫu số và số nhóm |
| `runs/full/results/sample_counts.csv` | Số đoạn, tệp và nhóm trong từng split |
| `runs/full/results/excluded_by_split.csv` | Các tệp không đủ byte, theo split/format/transform |
| `runs/full/results/errors.csv` | Các lượt dự đoán sai để phân tích |
| `runs/full/results/error_analysis.md` | Phân tích lỗi của run |
| `runs/full/results/benchmark_raw.csv` | Thời gian từng phần và từng lượt đo |
| `runs/full/results/benchmark_protocol.json` | Batch, warm-up, CPU/RAM/luồng và giới hạn timing |
| `runs/full/results/ablation_M2_minus_M1.csv` | Đánh đổi khi thêm recompression |
| `runs/full/results/header_sensitivity.csv` | Chênh lệch giữa start và interior |
| `runs/full/results/tradeoff.png` | Hình F1/FPR/tốc độ theo kích thước |
| `runs/full/results/confusion_64_interior.png` | Confusion matrix cho 64 KiB/interior |
| `runs/full/results/run.log` | Log chạy và các lỗi đã ghi |
| `runs/full/models` | Model lưu dưới dạng `.joblib` |
| `runs/full/data/manifests` | Inventory, split, provenance, checksum |

Đọc CSV trong PowerShell:

```powershell
Import-Csv -LiteralPath '.\runs\full\results\metrics_summary.csv' |
    Where-Object { $_.segment_kib -eq '64' -and $_.policy -eq 'interior' } |
    Select-Object model, f1_mean, f1_std, fpr_archive_mean
```

Có thể mở CSV bằng Excel. Nếu Excel không tự tách cột, dùng **Data → From Text/CSV**, chọn UTF-8 và dấu phân cách dấu phẩy. Mở Markdown bằng VS Code; chọn **Open Preview** để xem bảng. Mở PNG bằng trình xem ảnh thông thường.

### Ý nghĩa model và metric

| Tên | Nội dung |
| --- | --- |
| B0 | Threshold Shannon entropy |
| B1 | Random Forest chỉ dùng entropy |
| M1 | Random Forest dùng năm đặc trưng thống kê |
| M2 | M1 cộng tỷ lệ nén lại bằng zlib |
| Precision | Trong các đoạn dự đoán encrypted, tỷ lệ thật là encrypted |
| Recall | Trong các đoạn encrypted thật, tỷ lệ được phát hiện |
| F1 | Kết hợp precision và recall của lớp encrypted |
| FPR archive | Tỷ lệ đoạn compressed bị dự đoán nhầm thành encrypted |
| Macro-F1 | Trung bình F1 của hai lớp |
| Accuracy | Tỷ lệ dự đoán đúng trên toàn bộ đoạn được đánh giá |

`fpr_archive = 0.01` nghĩa là **1%**, không phải 0,01%. Mean ± SD mô tả dao động qua ba seed, không phải confidence interval. Các đoạn cùng nhóm nguồn có phụ thuộc nội dung. Đọc số mẫu/nhóm và các tệp bị loại trước khi kết luận về F1.

Kết quả tham khảo trên CSV tác giả nằm riêng ở `results/author_reference/RESULTS.md`. CSV đó thiếu ID nguồn, nên không trộn với kết quả group split của corpus tự tạo và không dùng nó để tuyên bố tốc độ đọc byte.

## 9. Chạy bộ kiểm thử

Trong thư mục `DT083`:

```powershell
$testTemp = 'results/pytest-user-' + (Get-Date -Format 'yyyyMMdd-HHmmss')
.\.venv\Scripts\python.exe -X utf8 -m pytest -q --tb=short -p no:cacheprovider --junitxml=results/tests-user.xml --basetemp $testTemp
```

Tên thư mục tạm mới giúp tránh đụng các thư mục test cũ. `-p no:cacheprovider` tắt cache pytest để giảm lỗi ACL cache đã gặp trong sandbox.

Bộ kiểm thử hiện có 28 tests, bao gồm công thức feature, dữ liệu rỗng/ngắn/hỏng, round-trip, group/content leakage, feature allowlist, source integrity, lựa chọn threshold và pipeline tích hợp. Lần xây dựng đã đạt **28 passed** ở cả môi trường chính và môi trường mới từ lock. Kết quả lần bạn chạy sẽ nằm trong `results/tests-user.xml`.

## 10. Xử lý các lỗi thường gặp

| Lỗi hoặc biểu hiện | Nguyên nhân thường gặp | Cách xử lý |
| --- | --- | --- |
| `python` không được nhận diện | Python chưa cài/chưa có trong PATH | Dùng `py -3.12`, hoặc cài Python 3.12 rồi mở terminal mới |
| Không tìm thấy `.venv\Scripts\python.exe` | Chưa có môi trường hoặc đang sai thư mục | Kiểm tra `Get-Location`, làm phần 4 |
| `ModuleNotFoundError` | Chưa cài thư viện hoặc gọi nhầm Python | Dùng đúng `.\.venv\Scripts\python.exe`, cài lại từ lock |
| `Inventory exists` | Chạy prepare/pipeline trên run đã có inventory | Chọn tên run mới; không xóa source/model hiện có để chạy demo |
| `Derived manifest already exists` | Chạy derive lần nữa trên run đã hoàn thành derive | Dùng bước sau nếu dữ liệu hợp lệ, hoặc chọn run mới để chạy lại từ đầu |
| `Run configuration mismatch` | Config hiện tại khác config đã lưu của run | Dùng đúng config của run; nếu muốn thay config, chọn run mới |
| Không tìm thấy `.joblib` | Chưa train hoặc sai run/model/seed/kib/policy | Kiểm tra thư mục models và các tham số demo; chạy train sau extract nếu thiếu |
| `Path outside permitted corpus` | `--file` trỏ ra ngoài root run | Dùng đường dẫn tương đối như `data/derived/...bin` trong đúng run |
| `Demo accepts only files...` | Chọn file ngoài source/derived, ví dụ results hoặc config | Chọn corpus file trong `data/source` hoặc `data/derived` |
| `status: too_small` | Không đủ một đoạn và margin | Chọn tệp lớn hơn hoặc cỡ nhỏ hơn đã có model; không padding tệp |
| `Source was changed` hoặc `Changed/corrupt derived content` | Corpus bị thay đổi sau khi ghi checksum | Giữ lại log để kiểm tra; tạo run mới hoặc khôi phục bản có checksum đúng |
| `WinError 5: Access is denied` | Sandbox, quyền thư mục tạm hoặc named pipe joblib | Chạy trong PowerShell thông thường; kiểm tra quyền thư mục dự án và dùng thư mục temp mới |
| Lỗi mạng khi pip/download | Không kết nối được nguồn tải | Kiểm tra mạng; corpus tự tạo không cần tải reference nếu thư viện đã cài |
| Chạy lâu nhưng chưa thấy kết quả cuối | Đang nén/trích feature/train | Xem `run.log`; các CSV/hình tổng hợp chỉ xuất khi các bước tương ứng kết thúc |

### Nếu bạn ngắt pipeline giữa chừng

Pipeline hiện không tự resume. Không chạy lại `pipeline` cùng run và kỳ vọng nó bỏ qua các bước đã làm.

- Cách dễ nhất: giữ run cũ để kiểm tra, tạo tên run mới và chạy lại.
- Nếu biết các artifact trước đó đã hoàn chỉnh, có thể chạy bước đang thiếu và các bước sau bằng CLI phần 7.
- Nếu bị ngắt giữa `prepare` hoặc `derive`, nên tạo run mới vì corpus/manifest có thể chưa đầy đủ.
- Nếu train chưa hoàn tất, chỉ một số model có thể đã được ghi; đợi hoặc chạy lại train hoàn chỉnh trước benchmark/report.
- Nếu train đã xong nhưng thiếu benchmark, chạy `benchmark` rồi `report` trên đúng run và config.

Khi CLI ghi lỗi, xem `results/last_error.json` và `results/run.log` bên trong run. `last_error.json` có thể lưu lỗi từ một lần trước; đối chiếu log và lần chạy gần nhất để biết đã xử lý xong hay chưa.

## 11. Phần tùy chọn: đối chiếu CSV tác giả và đóng gói

Các bước dưới đây không cần để chạy demo hoặc corpus tổng hợp.

### 11.1. Dùng reference đã tải trong workspace

Kiểm tra:

```powershell
Test-Path -LiteralPath '.\references\author\datasets\final64.zip'
```

Nếu có đủ reference và muốn chạy lại đối chiếu:

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/author_reference.py --sizes 64 128 256 512 1024 --folds 10 --seeds 42 123 2026
.\.venv\Scripts\python.exe -X utf8 scripts/summarize_author.py
```

Nếu chưa có reference:

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/fetch_references.py
```

Trình tải ghi commit và SHA256; chạy lại có thể lấy commit main mới. Không thực thi notebook tác giả. Kết quả tham khảo dùng row-level CV do thiếu source_group_id; giới hạn được ghi trong protocol.

### 11.2. Kiểm tra artifact có sẵn của phiên xây dựng

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/verify_artifacts.py
```

Script này hiện kiểm tra **hai run tên cố định `smoke` và `full`**, không tự nhận run mới của bạn. Nó kiểm tra checksum, group/content leakage, tập test chung, model lock và B0 threshold. Nếu chỉ có run mới, dùng manifest/log của run đó; không đổi tên run tùy tiện để giả như đây là cùng bộ kiểm chứng.

### 11.3. Đóng gói các artifact của phiên xây dựng

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/package_submission.py
```

Script hiện đóng gói `smoke`/`full` và các reference result đã chọn, không tự chọn run mới của bạn. Nó cập nhật `results/DT083_submission.zip`, `submission_inventory.json`, `submission_sha256.txt`. Package bỏ môi trường ảo, corpus raw có thể sinh lại, khóa AES mô phỏng và bản sao upstream. Để đóng gói một run mới, cần điều chỉnh danh sách run trong script hoặc chuẩn bị gói riêng với cùng nguyên tắc.

### 11.4. Raw Zenodo

Demo và thí nghiệm tổng hợp không cần raw Zenodo. Phiên hiện tại mới tải metadata, chưa tải archive 6,3 GB. Lệnh tải thụ động tùy chọn là:

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/fetch_zenodo_raw.py
```

Chỉ chạy khi muốn nghiên cứu raw và đã chuẩn bị dung lượng/mạng. Script kiểm size/MD5, không tự giải nén hoặc đưa dữ liệu đó vào pipeline hiện tại.

## 12. Chạy khi giải nén gói nộp trên máy khác

Gói `results/DT083_submission.zip` chứa code, config, docs, model, feature/manifest và kết quả; **không chứa `.venv` hoặc các byte source/derived dùng để demo**. Vì vậy, chỉ có model trong ZIP chưa đủ để chạy lệnh demo chọn tệp corpus.

Các bước:

1. Giải nén ZIP vào một thư mục bạn có quyền ghi.
2. Mở PowerShell trong thư mục `DT083` sau giải nén.
3. Cài Python/môi trường/thư viện theo phần 4.
4. Chạy smoke hoặc full bằng **tên run mới** theo phần 5/6 để sinh lại corpus.
5. Demo bằng tên run vừa tạo, không dùng `full` cũ thiếu corpus bytes.

Ví dụ sau khi đã cài `.venv`, tái tạo full rồi demo:

```powershell
$runRebuild = 'rebuild-' + (Get-Date -Format 'yyyyMMdd-HHmmss')
.\.venv\Scripts\python.exe -X utf8 scripts/run.py pipeline --config configs/full.json --run $runRebuild
```

Chỉ chạy lệnh tiếp theo sau khi pipeline thành công:

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/run.py demo --config configs/full.json --run $runRebuild --file data/derived/waves_01_png__aesgcm.bin --model M2 --seed 42 --kib 64 --policy interior
```

AES tạo khóa/nonce an toàn mới mỗi lần sinh corpus, nên ciphertext/checksum có thể khác lần đầu dù cấu hình và seed tổng hợp giữ nguyên.

## 13. Trình tự demo trước lớp

Chuẩn bị trước: dùng run `full` đã có trên máy hiện tại hoặc full run mới đã hoàn tất; không chờ huấn luyện full trong lúc trình bày ngắn.

1. Mở terminal trong `DT083`, giải thích bài toán phân loại compressed/encrypted cấp đoạn.
2. Chạy demo AES ở phần 3.1, trình bày offset, entropy, score và prediction.
3. Chạy demo ZIP ở phần 3.2, nói rõ nhãn thật theo transform và model có thể nhầm.
4. Mở `runs/full/results/RESULTS.md` để so sánh B0/B1/M1/M2 qua ba seed.
5. Mở `tradeoff.png`, confusion matrix và bảng ablation để giải thích chi phí/đánh đổi.
6. Nêu giới hạn: corpus tổng hợp 12 nhóm, không có cảm biến hành vi, ciphertext không đồng nghĩa ransomware.

Các tài liệu nghiên cứu và kết quả đo đầy đủ: `README.md`, `docs/STATUS.md`, `docs/dataset_card.md`, `docs/reproduction_card.md`, `docs/error_analysis.md`.
