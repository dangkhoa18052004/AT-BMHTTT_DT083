# Protocol và cách diễn giải

Mục tiêu kỹ thuật: pipeline byte hoàn chỉnh, source không đổi, mọi round-trip đúng, không giao group/content qua split, đủ cả hai lớp và ba seed cho mỗi tổ hợp được báo cáo, cùng tập test giữa bốn model. Không có ngưỡng F1/FPR đặt trước để gọi model thành công; mọi giá trị đo phải được công bố. Không biến điều kiện kiểm tra phần mềm thành chứng minh khả năng phát hiện ransomware.

Câu hỏi RQ1: B0 entropy threshold so với B1 entropy RF và M1 thống kê trên group-held-out corpus? RQ2: thêm recompression M2 thay đổi encrypted F1/archive FPR và ms/segment ra sao? RQ3: kích thước/policy sampling ảnh hưởng kết quả cùng selection bias như thế nào? Các câu hỏi và mô hình đã khai báo trong config trước khi train; không đổi feature/threshold grid dựa trên test.

Train chỉ fit RF. Validation chọn threshold trong grid RF 0.3/0.4/0.5/0.6/0.7; B0 candidates sinh từ entropy train. Max validation encrypted F1, tie theo FPR thấp hơn rồi threshold gần .5. RF hyperparameters được giữ cố định để so sánh fair; không chạy grid search trong own corpus. Config và model checksum được lưu trước khi đọc score test cho mỗi seed/size/policy. Cỡ split thực tế 7/2/3 template groups.

Metric chính precision/recall/F1 encrypted và archive FPR; macro-F1/accuracy bổ sung. FPR chia theo archive/source format kèm samples/groups. Không cân bằng bằng cách đưa original vào negative class. Threshold có thể tối ưu khác nếu deployment cost khác, nhưng đó là run/protocol mới. Không bỏ seed xấu hoặc run xấu. Mean±sample SD qua ba seed mô tả độ nhạy split, không CI/significance. Không fit feature selection/scaler/imputer trên toàn dữ liệu.

Timing pipeline thí nghiệm gồm generate/derive/split/extract/train/benchmark/report; timing đường phát hiện chỉ byte read→features→prediction. Benchmark không dùng CSV precomputed làm input feature của mô hình. Chỉ dùng CSV test prediction metadata để chọn lại byte/offset và đọc corpus. Feature recomputed thật cho mọi lượt benchmark. Repetition/warm-up/threads/batch/CPU/RAM được ghi protocol.

Không có aggregation theo tệp, nên không báo file precision/recall/F1. Không có confidence intervals; nếu bổ sung phải bootstrap group, không bootstrap segment IID. CSV tham khảo upstream có đường protocol riêng và không dùng để xác nhận điều kiện group độc lập. Dấu ± của CSV reference cũng là SD qua seed sau fold averaging, khác SD trong paper.
