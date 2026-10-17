# Dàn ý báo cáo 20–30 trang

Đề xuất 26 trang nội dung (chưa tính bìa/tài liệu tham khảo/phụ lục). Đây là dàn ý, không phải báo cáo hoàn thiện.

| Phần | Trang | Nội dung và bằng chứng |
| --- | --- | --- |
| 1. Bài toán/câu hỏi | 2 | DT083, mục tiêu compressed/encrypted, FPR archives; không đồng nhất encryption/ransomware |
| 2. Paper và tái lập chọn lọc | 3 | reproduction_card, Table4/5/6/7 mapping, threat model, phần khác |
| 3. Threat model/phạm vi | 2 | byte observer, false positives, hành vi chưa quan sát, không malware |
| 4. Dữ liệu/provenance | 4 | synthetic-vs-upstream, checksum/commit/license, 360 files vs12 groups; schema/missing/dedup |
| 5. Thiết kế và triển khai | 4 | source→transform→segment→features→model, AES sidecars, split invariants, công thức feature |
| 6. Protocol và validation | 3 | seeds, train/val/test, thresholds khóa, fairRF, sample counts, selection bias, tests |
| 7. Kết quả | 4 | precision/recall/F1, archiveFPR, subgroupcounts, raw metrics, confusion và tradeoff |
| 8. Ablation và lỗi | 2 | M1/M2 từng seed, start/interior, errors.csv; không kết luận significance từ SD |
| 9. Chi phí/giới hạn/kết luận | 2 | byte pipeline speed, warm-up/batch/cache, resources, synthetic limits, mở rộng public |

Hình cần chèn từ artifact: sơ đồ pipeline (tự vẽ), một mẫu mỗi source type (synthetic), confusion_{64,128,256}_interior.png, tradeoff.png. Bảng cần chèn: schema audit; số files/groups/split; excluded; metrics mean±SD; ZIP/GZIP/BZIP2 FPR và sample/group counts; M2-minus-M1 speed/F1.

Phụ lục: lệnh tái lập, full config, lock, version/CPU/RAM, tests.xml, demo.json, commit/checksum. Đính kèm references qua URL thay vì phân phối lại notebook/PDF/dataset thiếu quyền. Ghi rõ các phần chưa chạy (512/1024 own, raw Zenodo, public independent corpus, EDR integration). Nếu giảng viên cần slide/video thì dựng từ kết quả đã đo; tài liệu hiện tại chỉ có demo CLI và script đóng gói.
