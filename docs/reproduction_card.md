# Reproduction card — DT083

## Bài báo được đọc

Casino, Hurley-Smith, Hernandez-Castro, Patsakis (2025), *Not on my watch: ransomware detection through classification of high-entropy file segments*, Journal of Cybersecurity 11(1), tyaf009. [DOI](https://doi.org/10.1093/cybsec/tyaf009), [publisher PDF tại Kent](https://kar.kent.ac.uk/112636/1/ransomware%20detection%20through%20classification%20of%20high-entropy%20file%20segments.pdf). Đã tải PDF 21 trang, trích text và đọc phương pháp/đánh giá; PDF có trang bìa repository. Checksum ở downloads.json; bản tại Kent ghi CC BY-NC-ND 4.0. Không đưa PDF/text toàn văn vào package.

Tóm tắt paper: phân loại luồng entropy cao để hỗ trợ theo dõi file-write. Corpus gồm nhiều định dạng, nén ZIP/RAR/BZIP2/GZIP và AES/Camellia. Các cỡ 64–1024 KB. Battery gồm entropy, thống kê phân bố, FIPS/NIST; bước tối ưu giữ monobit và bỏ một số FIPS. RF, XGBoost, SVC được đánh giá qua 10-fold, lặp ba lần. Table 4: RF 100 cây, depth 10. Mốc đối chiếu RF/All: Table 5 F1 64=0.9528±0.0051, 128=0.9653±0.0051, 256=0.9809±0.0047; Table 6/7: 512=0.9965, 1024=1. Các mốc chỉ là số paper, không phải số nhóm.

## Phạm vi và threat model của nguyên mẫu

Input: byte của các đoạn đủ kích thước từ corpus được phép. Output: class compressed/encrypted và score. Câu hỏi: entropy đơn lẻ, các thống kê rẻ và recompression khác nhau thế nào về encrypted F1, archive FPR và chi phí? Giả thuyết trước chạy: thêm thống kê/recompression có thể giảm FPR nhưng tăng chi phí; chưa biết chiều/lượng thay đổi thực tế.

Đối thủ giả định tạo ciphertext, hệ thống quan sát được byte đầy đủ. Không có cảm biến file-write, attribution process, whitelist, khóa crypto của đối thủ hay thông tin user intent. Byte ciphertext có thể hợp lệ. Phân loại sai không dẫn đến tác vụ phản ứng. Không thực thi malware và không kiểm tra chống né tránh/partial encryption. Không gọi đây là EDR hoàn chỉnh.

## Nguồn và code đã kiểm tra

[Repository tại commit cố định](https://github.com/francasino/Ransomware_analysis/tree/7645cacfb304aa8666f109cba758a3933c579819), nhất là `datasets/readme`, `Ransomware_clean.ipynb` cells 5/7/9/26/39 và `tests/ent.py`, `tests/StatSeeker.py`. Notebook ghi Filetype 0 compressed / 1 encrypted; ` Original` 0 bin,1 img,2 mp3,3 pdf,4 txt,5 video. Schema/data provenance ở dataset card.

Notebook parser: entropy; Jarque-Bera/Shapiro trên histogram; tổng p-values ở bốn trường NIST; Monobit_ pass iff mọi cửa sổ trong [9725,10275]; Chi_score khi gamma_hedge=2 là I(chi<299). Các ngưỡng này là của đường notebook tham khảo, khác raw chi-square và bit-one ratio trong corpus riêng. Parser dùng ast.literal_eval/json.loads, không chạy eval/execute notebook. Global minmax của notebook bị bỏ trong bản tham khảo vì RF không cần scaler; không fit preprocessing trên test. Chi tiết đóng băng ở `results/author_reference/protocol.json`.

## Hai loại thí nghiệm

Tham khảo CSV: RF 100/depth10, chín feature parse theo notebook, max_features=all, stratified 10-fold theo hàng cho mỗi seed; duplicate feature+label chính xác bị loại trước CV. Ghi khác biệt shuffle/seed/version, không giả vờ source-group split. Không raw feature extraction hoặc kết luận speed.

Corpus kiểm soát: synthetic-only, 12 nhóm template, ZIP/GZIP/BZIP2/AES-GCM; group holdout khoảng 60/20/20; không RAR/Camellia/audio/video/bin. Sáu feature của dự án theo `features.md`; B0/B1/M1/M2 và 64/128/256 KiB. RF tham số fair khai báo trước (100/depth10, max_features=sqrt, balanced, n_jobs=4); threshold chọn validation F1, tie lower FPR rồi gần .5. Khóa và checksum model trước test. Metrics encrypted precision/recall/F1, macro-F1/accuracy, FPR_archive=FP/(TN+FP), subgroup, sample/group counts; mean±sample SD qua seed. Không báo cáo CI hay file-level metric.

## Đối chiếu và giới hạn phải nêu

1. CSV upstream thiếu source_group_id, không chứng minh độc lập nguồn; row CV có nguy cơ phụ thuộc chunk.
2. Không có raw Zenodo trong phiên này; không tái lập thống kê từ byte tác giả.
3. Corpus synthetic không có ảnh/tài liệu public, audio/video/bin; chưa đủ 300–600 nhóm độc lập.
4. AES-GCM của nhóm khác các thuật toán/mode upstream; ciphertext không đồng nghĩa ransomware.
5. Bộ sáu feature không trùng battery; serial/runs/recompression là biến thể riêng.
6. Group split khác row CV; dữ liệu, độ cân bằng và độ khó khác, không so vượt paper trực tiếp.
7. Lọc size/margin có selection bias; header còn có thể tồn tại và two-policy không chỉ thay header.
8. 12 họ mẫu tạo test ít groups; seed lặp lại nguồn, SD không là CI hoặc kiểm định khác biệt.
9. Hệ điều hành/hardware/library version và cơ chế parallel khác; benchmark cache nóng không là latency ứng phó thực tế.
10. Notebook có cấu hình gamma/minmax, phải ghi chính xác; một số parser/comment/feature names khác prose paper. Điều kiện đối chiếu RF All chỉ tương đồng một phần.
11. Thiếu license chung GitHub, không tự gán CC BY của metadata Zenodo cho repo; không redistribute upstream.

Kết quả nào đã chạy và artifact ở `STATUS.md`. Paper mapping lưu riêng; đóng góp nhóm là ablation M1→M2 và sampling sensitivity, không khẳng định ưu thế thống kê hay triển khai EDR.
