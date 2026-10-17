# Ánh xạ với paper

Nguồn: [paper DOI](https://doi.org/10.1093/cybsec/tyaf009), [notebook commit cố định](https://github.com/francasino/Ransomware_analysis/blob/7645cacfb304aa8666f109cba758a3933c579819/Ransomware_clean.ipynb). Các số paper dưới đây chỉ dùng làm mốc tham khảo, không suy ra vượt paper.

| Thành phần | Paper/code upstream | DT083 đã triển khai | Artifact đối chiếu |
| --- | --- | --- | --- |
| RF cấu hình | Table 4: 100 cây / depth 10 | cùng 100/depth10, nhưng own max_features=sqrt/balanced | configs/*.json; author_reference/protocol.json |
| RF All 64 KiB | Table 5 F1 0.9528 ± 0.0051 | CSV tham khảo theo hàng; own group holdout riêng | results/author_reference/metrics_summary.csv; runs/full/results/metrics_summary.csv |
| RF All 128 KiB | Table 5 F1 0.9653 ± 0.0051 | tương tự | cùng artifact, lọc segment_kib=128 |
| RF All 256 KiB | Table 5 F1 0.9809 ± 0.0047 | tương tự | cùng artifact, lọc segment_kib=256 |
| RF All 512/1024 | Table 6/7: 0.9965 / 1 | CSV reference; own chỉ hỗ trợ config, chưa chạy | author_reference; không có own metrics |
| Entropy ablation | Table 7 | B1 vs M1/M2 trên corpus riêng | runs/full/results/metrics_raw.csv |
| Feature battery | Table 3; notebook parser | chín feature tham khảo / sáu feature riêng | scripts/author_reference.py; docs/features.md |
| Compression/encryption | upstream nhiều thuật toán | ZIP/GZIP/BZIP2/AES-256-GCM | data/manifests/derived_seed_*.csv |
| Độc lập theo source | không đủ metadata CSV để xác minh | own group split, conservative template groups | splits_*.csv và tests.xml |
| Speed | upstream có feature/predict timing | byte read→features→predict, batch và cache công bố | benchmark_raw.csv; benchmark_protocol.json |
| Đóng góp riêng | không dùng làm kết quả paper | recompression ablation + start/interior | ablation_M2_minus_M1.csv; header_sensitivity.csv |

Các row author reference không được trộn với own group-held-out test. Không tái lập SVC/XGBoost/HEDGE, grid search hay tất cả per-file-type table rows. Không truy nguyên dataset bytes, chunk offset hoặc checksum nguồn tác giả.
