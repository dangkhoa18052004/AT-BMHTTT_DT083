# Trạng thái thực nghiệm và bàn giao

Tài liệu này sinh từ artifact đã lưu; không tự điền kết quả chưa đo. Các đường dẫn tương đối với DT083.

## Đã triển khai

CLI từng bước và pipeline; nguồn tổng hợp TXT/CSV/PDF/PNG/JPEG; manifest/SHA256; group split; nén ZIP/GZIP/BZIP2/AES-GCM, round-trip; sáu feature; B0/B1/M1/M2; validation threshold/model lock; subgroup/error/speed artifacts; demo; tài liệu tiếng Việt và gói nộp không kèm reference upstream/khóa.

## Dữ liệu đã thực sự tải/tạo

Tải PDF bài báo, notebook/code để đọc, năm ZIP feature CSV, metadata Zenodo. Commit 7645cacfb304aa8666f109cba758a3933c579819, SHA256 từng file trong references/downloads.json; mọi download đều thành công. Không tải/chạy malware. Không tải raw archive Zenodo và không có nguồn public trong corpus kiểm soát.

- **smoke**: 60 source files / 12 template groups; 18002344 byte source; 300 derivatives; 594 segment rows gồm original/size/policy; 24 model/seed/size/policy evaluations.
- **full**: 360 source files / 12 template groups; 438613171 byte source; 1800 derivatives; 17109 segment rows gồm original/size/policy; 72 model/seed/size/policy evaluations.

## Kiểm thử và tái lập

- Môi trường chính: 28 tests, 0 failures, 0 errors.
- Môi trường mới từ requirements-lock: 28 tests, 0 failures, 0 errors.
- results/verification.json kiểm tra nguồn/dẫn xuất, group/hash leakage, test sets giống nhau và model checksum.
- .venv-repro là môi trường mới độc lập, không dùng system-site-packages; fresh_environment.json ghi đối chiếu lock.
- CSV tham khảo: 5 size × 10 folds × 3 seed = 150 lượt fit/evaluate; giới hạn row split trong author_reference/protocol.json.

## Kết quả corpus kiểm soát — 64 KiB, interior

| model | precision | recall | f1 | fpr_archive | ms/segment read→features→predict |
| --- | --- | --- | --- | --- | --- |
| B0 | 0.8994 ± 0.0138 | 0.9722 ± 0.0172 | 0.9342 ± 0.0029 | 0.0370 ± 0.0062 | 0.410 |
| B1 | 0.8758 ± 0.0150 | 0.9782 ± 0.0034 | 0.9241 ± 0.0091 | 0.0471 ± 0.0066 | 0.559 |
| M1 | 0.9744 ± 0.0094 | 0.9841 ± 0.0225 | 0.9792 ± 0.0159 | 0.0087 ± 0.0030 | 1.714 |
| M2 | 0.9707 ± 0.0062 | 0.9861 ± 0.0191 | 0.9783 ± 0.0121 | 0.0101 ± 0.0020 | 3.232 |

Mean±sample SD ba seed trên cùng corpus, không CI. Các size/policy còn lại trong runs/full/results/RESULTS.md. Chỉ cấp đoạn compressed/encrypted, không phải ransomware detection rates.

## Kết quả tham khảo CSV tác giả

Xem results/author_reference/RESULTS.md. Đây là đường đối chiếu chọn lọc, không bảo đảm độc lập nguồn và không có raw byte speed. Không tuyên bố vượt paper.

## Chi phí full và giới hạn

Whole experiment wall time đã đo: 1870.61 s. Đây bao gồm sinh/nén/mã hóa/train/artifact, không phải detection latency.

| stage | seconds |
| --- | --- |
| prepare | 232.076 |
| derive | 428.497 |
| split | 0.410 |
| extract | 694.692 |
| train | 394.998 |
| benchmark | 117.385 |
| report | 1.950 |

Không còn bước thực thi thiết kế hiện tại bị sandbox chặn sau khi đã chạy ngoài sandbox. Các phần chưa thực hiện: raw Zenodo 6.3 GB; corpus public với 300–600 nguồn độc lập; own 512/1024 KiB; bootstrap group CI; model calibration; partial encryption và file-write/process sensor; báo cáo hoàn chỉnh/slide/video ngoài dàn ý.

360 tệp full chỉ có 12 group. Điều kiện độc lập/đại diện của tài liệu thực chưa đạt. Framework sinh chung vẫn có thể tạo phụ thuộc giữa các họ. Header margin và size filtering có bias, đọc dataset/error cards trước khi diễn giải.

## Lệnh dùng tiếp

Chạy trong DT083:

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/run.py demo --config configs/full.json --run full --file data/derived/waves_01_png__aesgcm.bin --model M2 --seed 42 --kib 64 --policy interior
.\.venv\Scripts\python.exe -X utf8 scripts/run.py pipeline --config configs/full.json --run full-new
.\.venv\Scripts\python.exe -X utf8 scripts/fetch_zenodo_raw.py
```

Lệnh raw là tùy chọn, chưa được chạy và không tự đưa archive vào training. Để tái tạo gói sau thay đổi artifact: scripts/package_submission.py. Hướng dẫn đầy đủ ở README.md.
