# Phân tích lỗi và cách đọc

Phân tích tự động theo dữ liệu thực của mỗi run ở `runs/<run>/results/error_analysis.md`, `errors.csv`, `error_counts.csv`. Không chép số từ paper vào kết quả nhóm. Dự đoán sai có ID, nguồn, group, transform, offset, length, feature, score và true/predicted label.

Đọc theo thứ tự: kiểm tra sample_counts/excluded_by_split → RF/B0 false-positive counts và mẫu số theo archive → source format → M1/M2 paired deltas → header sensitivity → cost protocol. Tổng lỗi giữa seed/size/policy có lặp byte và nguồn, không là số quan sát độc lập. FPR ZIP/GZIP/BZIP2 là số đoạn archive dự đoán encrypted chia số đoạn cùng nhóm; cả numerator/denominator phải được ghi.

Ba tình huống cần phân tích: compressed image/PDF entropy gần ciphertext; archive text bị lọc do nén nhỏ hơn một đoạn; source-family giữ lại ngoài train có cấu trúc khác. Nén lại có thể không cải thiện khi cả hai phía đều gần ngẫu nhiên. Chênh lệch sampling không chỉ do header vì vị trí đoạn cũng thay đổi. Metric subgroup một lớp không dùng làm F1 tổng quan.

Chỉ xem lỗi test để mô tả giới hạn. Không quay lại đổi threshold/tune và gọi lại đó là cùng holdout test; mọi thiết kế mới cần protocol và run mới, còn kết luận xác nhận cần corpus held-out độc lập. Chưa có quy tắc file-level aggregation hoặc bootstrap CI. Không giải thích score như xác suất ransomware.

## Quan sát đã đo trong full

| Interior | M1 F1 mean±SD | M2 F1 mean±SD | M1 archive FPR | M2 archive FPR |
| --- | --- | --- | --- | --- |
| 64 KiB | 0.979198±0.015869 | 0.978291±0.012129 | 0.008739 | 0.010089 |
| 128 KiB | 0.983048±0.001870 | 0.986210±0.004878 | 0.009877 | 0.008218 |
| 256 KiB | 0.982681±0.003282 | 0.990676±0.002019 | 0.010980 | 0.003290 |

M2 không cải thiện trung bình tại 64 KiB; ở 128/256 KiB trung bình F1 tăng và FPR giảm, nhưng không suy ra ý nghĩa thống kê từ ba seed cùng corpus. Mỗi size giữ lại thành phần mẫu khác nhau. Tại 64 KiB, chi phí batch đọc→features→predict là M1 1.714 ms/đoạn, M2 3.232 ms/đoạn; đây là benchmark cache/batch, không phải demo một đoạn hoặc latency ứng phó ransomware.

`header_sensitivity.csv` ghi F1 start-minus-interior trung bình M1 tại 64/128 là −0.022071/−0.024312, M2 là −0.024593/−0.023086. Quan sát không ủng hộ giả định lấy header luôn giúp model tốt hơn; nó còn thay offset và số mẫu đủ byte. Không diễn giải đây là tác động nhân quả của header.

`error_counts.csv` full có tổng 926 lượt dự đoán sai, gồm mọi model/seed/size/policy; có nguồn lặp. Không dùng tổng này như số lỗi trên 926 tệp độc lập. Subgroup raw và mean±SD/mẫu số trong `metrics_subgroups.csv`/`metrics_subgroups_summary.csv`. Tất cả kết quả này thuộc corpus tổng hợp 12 nhóm, không so trực tiếp với table paper hoặc CSV row-CV.
