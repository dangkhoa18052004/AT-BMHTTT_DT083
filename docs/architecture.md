# Kiến trúc nguyên mẫu

```mermaid
flowchart TD
    A[TXT CSV PDF PNG JPEG tổng hợp] --> B[Inventory SHA256 và source_group_id]
    B --> C[Split group theo seed 60/20/20]
    B --> D[Original ZIP GZIP BZIP2 AES-GCM]
    D --> E[Round-trip và checksum nguồn]
    C --> F[Manifest dẫn xuất theo seed]
    E --> F
    F --> G[Đoạn đầy đủ có offset và SHA256]
    G --> H[Feature thống kê và recompression]
    H --> I[Train B0 B1 M1 M2]
    I --> J[Validation chọn threshold]
    J --> K[Khóa config model SHA256]
    K --> L[Held-out test metrics và dự đoán]
    G --> M[Đọc byte lại cho benchmark]
    K --> M
    L --> N[Bảng hình phân tích lỗi và ablation]
    M --> N
```

Tag/nonce/AAD/key AES nằm ngoài byte input classifier. Metadata nguồn/dẫn xuất chỉ dùng join, chia dữ liệu và phân tích subgroup; `matrix` chỉ nhận allowlist feature. Original không nối vào negative class. Không có process monitoring hoặc nhánh phản ứng tự động.

CSV tác giả có pipeline riêng: ZIP→parse chín feature→10-fold row CV→kết quả tham khảo. Nó không nối vào train/validation/test của corpus kiểm soát hoặc benchmark đọc byte.
