# DT083 — Phân tích entropy trên các đoạn tệp

DT083 là nguyên mẫu nghiên cứu bằng Python để phân loại các đoạn dữ liệu tệp tổng hợp thành **đã nén** hoặc **đã mã hóa mô phỏng**. Dự án khảo sát đặc trưng entropy, một số mô hình phân loại và chi phí xử lý theo từng đoạn.

> **Phạm vi an toàn:** Đây không phải công cụ phát hiện ransomware. Dự án không tải hoặc chạy mã độc, không quét máy, không xóa tệp và không dừng tiến trình.

## Tổng quan

- Tạo corpus tổng hợp có thể tái lập bằng các cấu hình smoke và full.
- Tính đặc trưng trên các đoạn dữ liệu và đánh giá nhiều biến thể mô hình.
- Tách dữ liệu theo nhóm mẫu để hạn chế rò rỉ giữa các tập.
- Ghi lại metric, phân tích lỗi và benchmark trong thư mục của từng lần chạy.
- Cung cấp CLI cho toàn pipeline hoặc từng bước riêng.

Corpus hiện tại được sinh từ **12 nhóm mẫu thủ tục**; nhiều tệp biến thể trong cùng nhóm không phải là các nguồn độc lập. Kết quả chỉ phản ánh corpus tổng hợp và không đại diện cho tệp thực hay khả năng phát hiện ransomware.

## Yêu cầu

- Python 3.12 trở lên.
- Windows PowerShell cho các lệnh ví dụ bên dưới.

Các phiên bản phụ thuộc được khóa trong [`requirements-lock.txt`](requirements-lock.txt). Cấu hình thí nghiệm nằm trong [`configs/`](configs/).

## Cài đặt

Chạy từ thư mục gốc của repository:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
```

## Chạy thử

Smoke kiểm tra pipeline với corpus nhỏ:

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/run.py pipeline --config configs/smoke.json --run smoke-01
```

Chạy cấu hình full bằng tên lần chạy mới:

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/run.py pipeline --config configs/full.json --run full-01
```

Kết quả được ghi vào `runs/<run-name>/`. Hãy dùng tên mới cho mỗi lần chạy; chương trình không ghi đè một số manifest hoặc dữ liệu đã tạo.

Có thể thực thi từng giai đoạn bằng các lệnh `prepare`, `derive`, `split`, `extract`, `train`, `benchmark` và `report`. Ví dụ:

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/run.py prepare --config configs/full.json --run full-01
.\.venv\Scripts\python.exe -X utf8 scripts/run.py derive --config configs/full.json --run full-01
.\.venv\Scripts\python.exe -X utf8 scripts/run.py split --config configs/full.json --run full-01
.\.venv\Scripts\python.exe -X utf8 scripts/run.py extract --config configs/full.json --run full-01
.\.venv\Scripts\python.exe -X utf8 scripts/run.py train --config configs/full.json --run full-01
.\.venv\Scripts\python.exe -X utf8 scripts/run.py benchmark --config configs/full.json --run full-01
.\.venv\Scripts\python.exe -X utf8 scripts/run.py report --config configs/full.json --run full-01
```

## Chạy kiểm thử

```powershell
.\.venv\Scripts\python.exe -X utf8 -m pytest -q
```

## Demo

Sau khi chạy pipeline, thay `REPLACE_WITH_FILE_NAME.bin` bằng tên tệp có trong `data/source` hoặc `data/derived` của lần chạy đó:

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/run.py demo --config configs/full.json --run full-01 --file data/derived/REPLACE_WITH_FILE_NAME.bin --model M2 --seed 42 --kib 64 --policy interior
```

Demo chỉ đọc dữ liệu trong thư mục lần chạy đã chọn. Điểm số là đầu ra của mô hình, không phải xác suất một tệp là ransomware. Không tải model `joblib` từ nguồn không tin cậy.

## Kết quả và tài liệu

Các kết quả sinh tự động được lưu trong `runs/<run-name>/`, bao gồm metric, dự đoán, cấu hình đã khóa, benchmark và báo cáo. Thư mục `runs/` cùng dữ liệu và kết quả cục bộ được loại khỏi Git theo [`.gitignore`](.gitignore); không đưa khóa mô phỏng, dữ liệu tải về hoặc artifact máy cục bộ vào commit.

- [Kiến trúc](docs/architecture.md)
- [Đặc trưng](docs/features.md)
- [Dataset card](docs/dataset_card.md)
- [Quy trình tái lập](docs/reproduction_card.md)
- [Quy trình nghiên cứu](docs/research_protocol.md)
- [Phân tích lỗi](docs/error_analysis.md)
- [Môi trường và an toàn](docs/environment_and_safety.md)
- [Trạng thái dự án](docs/STATUS.md)
- [Hướng dẫn chạy chi tiết](HUONG_DAN_CHAY_CHUONG_TRINH.md)

## Giới hạn và giấy phép

Thử nghiệm hiện tập trung vào phân loại đoạn **đã nén / mã hóa mô phỏng** trên dữ liệu tổng hợp. Dự án không đánh giá hành vi ransomware trên tệp thật, mã hóa một phần, hoặc khả năng phát hiện ở cấp toàn bộ tệp. Không diễn giải metric của các đoạn như tỷ lệ phát hiện ransomware.

Repository hiện chưa khai báo giấy phép tổng thể. Nội dung và dữ liệu tham khảo bên thứ ba có điều khoản riêng; cần kiểm tra nguồn và giấy phép tương ứng trước khi sử dụng hoặc phân phối lại.
