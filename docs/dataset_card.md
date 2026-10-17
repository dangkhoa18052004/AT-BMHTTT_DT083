# Dataset card

## Ba nguồn dữ liệu được tách biệt

**Corpus tự tạo**: `runs/smoke/data` và `runs/full/data`. TXT/CSV nhiều số liệu/chủ đề và mức lặp; ảnh có sóng/radial/grid/terrain/rings/diagonal/checker/mosaic/bands/spiral/contour/blocks, hình vẽ và texture có biên độ khác nhau; PDF có chữ, bảng và hình. Không chỉ dùng noise thuần hoặc văn bản lặp. Mức nén PNG 1/6/9, JPEG quality 65/85/95, độ phân giải theo config. 12 họ template được giữ chung group cho tất cả variants/định dạng. Giấy phép byte tổng hợp được dự án gán CC0-1.0. Không có nguồn public trong corpus kiểm soát hiện tại. Template không đại diện tài liệu/ảnh thực và group khác nhau vẫn chia sẻ framework sinh, nên độc lập ngữ nghĩa không được bảo đảm tuyệt đối.

**CSV tác giả đã tải**: năm ZIP tại commit `7645cacfb304aa8666f109cba758a3933c579819`; mỗi ZIP chứa CSV feature, không raw bytes. Tương ứng 64/128/256/512/1024 KiB có 19200/9600/4800/2400/1200 hàng. Audit ban đầu không có giá trị trống/NaN/None/null trong chuỗi; bước parse kiểm tra numeric missing. `Filetype` có 0/1 cân bằng. Nhãn được xác nhận từ notebook, không đoán. Có metadata ` Original`, ` size` nhưng không có ID nguồn, byte checksum, offset hoặc loại transform cụ thể; không dùng các metadata này làm feature. Schema đầy đủ, ví dụ raw, missing và checksum lưu ở `references/schema_audit.json`, `references/downloads.json`. Các trường FIPS/NIST là chuỗi danh sách, cần parser an toàn.

**Zenodo chỉ metadata**: record 5148542; file `dataset_raw.zip` dung lượng 6.300.255.462 byte, MD5 từ server `87825a676ba20d18b86c7b38406973cf`; chưa tải/kiểm chứng nội dung. Metadata ghi `cc-by-4.0`; không suy ra quyền phân phối lại các tệp GitHub. Không lấy metadata access làm bằng chứng raw download. [Zenodo](https://zenodo.org/records/5148542), [datasets readme](https://github.com/francasino/Ransomware_analysis/blob/7645cacfb304aa8666f109cba758a3933c579819/datasets/readme).

## Provenance và an toàn

Inventory chứa source_id, source_group_id, source_sha256, source_type, size_bytes, source_url (trống vì synthetic), license, acquisition_date, generation_method, generation_seed và path tương đối. Ngày sinh dùng ISO với timezone +07:00. SHA trùng bị loại trước chia; không lấy thay seed/tên làm căn cứ độc lập. Số files/groups thật đọc `corpus_summary.json`.

Mỗi source có original benign=-1, ZIP-DEFLATE/GZIP/BZIP2 compressed=0, AES-256-GCM encrypted=1. `original` là bản sao byte; không sửa source. Key từ AESGCM.generate_key, nonce 96-bit từ os.urandom, chống trùng trong corpus; ciphertext không có wrapper riêng của dự án. Tag/nonce/AAD nằm ngoài classifier input trong sidecar/manifest; key chỉ phục vụ round-trip mô phỏng cục bộ. Original/nén/mã hóa đã kiểm tra khôi phục checksum. Không cần key để trích feature hoặc predict. AES không deterministic dù corpus generation có seed.

## Split và lọc

Nhóm chia khoảng 60/20/20, thực tế với 12 groups là 7 train / 2 validation / 3 test. Mọi group có đủ định dạng source, nhưng các archive nhỏ có thể bị lọc khác nhau. Split khác theo seed 42/123/2026; group và SHA source/derived/segment không được giao nhau trong một seed. `derived.csv` là manifest biến đổi dùng chung; `derived_seed_42.csv`, v.v. có trường split cụ thể. `splits_<seed>.csv` là inventory được gán split. Group giữa seed có thể dùng lại, không phải dữ liệu mới.

Tệp thiếu kích thước bị loại theo policy/size, tuyệt đối không pad/nối. `excluded_by_split.csv` ghi source format, transform và split; số mẫu retained trong `sample_counts.csv`. Do nén làm giảm size còn AES giữ size, tỷ lệ lớp không cân bằng cố định và có selection bias. Không trộn original vào bài toán chính. Source public đa dạng, nhiều nhóm hơn, encrypted có partial/streaming và hành vi process chỉ là hướng mở rộng chưa chạy.

Không áp dụng bộ lọc entropy tiền xử lý: tất cả đoạn compressed/encrypted đủ byte đều tham gia. Vì thế không bảo đảm mọi negative có entropy gần 8; metric chính có thể bao gồm archive dễ phân biệt. Một đánh giá chỉ trên miền entropy cao với cutoff khai báo từ train/validation là hướng phân tích tiếp, chưa được dùng để thay đổi tập test hiện tại.

## Phân phối

Notebook/ZIP của tác giả chỉ dùng nghiên cứu cục bộ; không có LICENSE chung trong tree đã khảo sát. `tests/ent.py` có MIT header riêng, không đại diện cả repo. Submission bỏ tất cả reference upstream và simulation key; corpus tự tạo có thể sinh lại từ code/config. Không đưa data riêng tư hay tệp hệ thống vào corpus.
