# Môi trường và ranh giới an toàn

## Môi trường tái lập

Dự án yêu cầu Python 3.12 trở lên. Cài đặt từ `requirements-lock.txt` để dùng các phiên bản phụ thuộc đã khóa. Cấu hình benchmark, số lần lặp và warm-up được khai báo cùng cấu hình thí nghiệm hoặc artifact của lần chạy.

Thời gian xử lý phụ thuộc vào phần cứng, tải hệ thống, bộ nhớ đệm và hoạt động I/O. Kết quả benchmark phù hợp để so sánh các biến thể trong cùng quy trình đo; không nên diễn giải như cam kết hiệu năng trên thiết bị khác. Thời gian chạy toàn pipeline và độ trễ xử lý từng đoạn là các phép đo khác nhau.

## An toàn dữ liệu

- Không tải hoặc thực thi malware; không quét máy, sửa/xóa tệp ngoài corpus hay dừng tiến trình.
- Corpus được tạo tổng hợp. Phép biến đổi mã hóa chỉ nhằm kiểm tra pipeline; khóa sinh ra không phải khóa sản xuất và không được chia sẻ hoặc tái sử dụng.
- Các tài liệu tham khảo bên ngoài chỉ được xử lý theo đúng phạm vi đã mô tả trong từng quy trình. Không thực thi notebook hoặc đánh giá mã được nhúng trong dữ liệu tham khảo.
- Đường dẫn đầu vào demo được giới hạn trong thư mục dữ liệu của lần chạy. Chỉ nạp model `joblib` do dự án tạo; định dạng này không an toàn khi nhận tệp từ nguồn không tin cậy.
- Dữ liệu, model, khóa mô phỏng, log và artifact của từng lần chạy là đầu ra cục bộ, không thuộc source control mặc định.

## Diễn giải và quyền sử dụng

Nhãn của thí nghiệm là đoạn đã nén hoặc đã mã hóa mô phỏng; kết quả không phải tỷ lệ phát hiện ransomware. Số mẫu biến thể không đồng nghĩa với số nguồn độc lập. Xem [dataset card](dataset_card.md) và [quy trình nghiên cứu](research_protocol.md) trước khi diễn giải kết quả.

Quyền sử dụng mã nguồn, bài báo và dữ liệu bên thứ ba cần được xác minh riêng. Metadata hoặc giấy phép của một nguồn không tự động áp dụng cho các nguồn khác.
