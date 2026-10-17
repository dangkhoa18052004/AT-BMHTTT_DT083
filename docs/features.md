# Đặc trưng của dự án

Đây là bộ đặc trưng tự triển khai. Chỉ Shannon và chi-square có ý tưởng tương ứng trực tiếp; không gọi cả bộ là implementation chính xác của paper.

Với n byte, c_b là số byte b, p_b=c_b/n, b=0…255:

- Entropy: H = −Σ_{c_b>0} p_b log₂ p_b, đơn vị bit/byte, không bias correction. H=0 cho dữ liệu hằng và H=8 cho 256 byte đều.
- Chi-square: Σ_{b=0}^{255}(c_b−n/256)²/(n/256), giữ cả các bucket bằng 0. Đây là statistic, không p-value hoặc pass/fail.
- Serial correlation: Pearson(x[0:n−1], x[1:n]), không nối vòng cuối với đầu. Nếu n<2 hoặc một vector phương sai 0: trả 0.
- Bit-one ratio: n₁/(8n), unpack bit theo MSB trước (`big`). Đây là tỷ lệ, không phải pass/fail FIPS trên từng cửa sổ 20.000 bit.
- Runs statistic: trên chuỗi bit MSB-first, R=1+Σ I(bit_i≠bit_{i−1}); E[R]=1+2n₀n₁/N; Var[R]=2n₀n₁(2n₀n₁−N)/(N²(N−1)). Feature z=(R−E[R])/√Var[R], giữ dấu. Trả 0 khi variance không dương (chuỗi một giá trị). Không dùng continuity correction. Đây là Wald–Wolfowitz conditional statistic, không runs pass/fail của FIPS/SP800-22.
- Recompression ratio: len(zlib.compress(segment, level=6))/n; tính cả wrapper zlib. Có thể lớn hơn 1; không clip. M2 thêm feature này.

Segment rỗng: ValueError, không thay bằng số 0. Frame có NaN/infinity: từ chối, không tự impute. Không fit scaler. `matrix` chỉ cho phép allowlist feature, không filename/extension/path/ID/transform/label.

KiB=1024 byte, MiB=1024² byte. Paper dùng tên KB; `size` trong CSV xác nhận 65536/131072/262144/524288/1048576 byte, nên các phép so sánh kích thước ở đây dùng KiB.

`start`: offset 0, L,… tối đa 2 đoạn hoàn chỉnh, có thể chứa header. `interior`: bỏ 4096 byte hai đầu, trải đều tối đa 2 đoạn trong vùng còn lại; không chồng lấn. Nếu chỉ có 1 đoạn, đặt giữa vùng đủ điều kiện. Không padding hoặc nối source. Margin khác 0 không đảm bảo đã loại mọi cấu trúc định dạng. So sánh policy làm rõ shortcut nhưng không cô lập tác động nhân quả của header vì còn thay offset nội dung.

Trong benchmark, B0/B1 chỉ tính entropy; M1 tính năm feature thống kê; M2 tính thêm zlib. Trong stage extract, feature thống kê và recompression được đo riêng để lưu data dùng chung cho mọi model. Sampling/feature rows giống nhau giữa model trong từng seed/size/policy. Các kích thước có các điều kiện chọn khác nhau, nên không coi sự tăng F1 theo size là chỉ do thêm byte.
