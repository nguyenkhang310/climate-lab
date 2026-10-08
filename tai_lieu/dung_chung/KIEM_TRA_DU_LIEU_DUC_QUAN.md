# Kiểm tra dữ liệu sau xử lý của Đức và Quân

Ngày kiểm tra: 08/10/2026. Đợt đầu đối chiếu 7 CSV của Đức và Quân, hai CSV ghép,
các báo cáo chất lượng, đầu vào và kết quả mô hình. Sau sửa có thêm bảng nhiệt độ
năm lịch và kết quả đánh giá cuốn chiếu. Phần "Đối chiếu trước sửa" bên dưới ghi
các phát hiện ban đầu; trạng thái hiện tại được ghi ngay dưới đây.

## Trạng thái hiện tại: bộ lọc riêng và kiểm tra lại mô hình

- Nhiệt độ: **1961–2025**, toàn cầu dùng NASA và quốc gia dùng FAOSTAT.
- CO₂: **1850–2024**; toàn cầu đọc OWID World riêng, không bị cắt về 1880.
- Tổng quan, Bản đồ, Nhận định, Dữ liệu: **1961–2024**. Chuỗi toàn cầu có đủ
  nhiệt độ và CO₂ cho cả 64 năm. Bảng quốc gia có 11.520/15.456 dòng đủ cặp;
  các giá trị thiếu vẫn giữ null. EDGAR chỉ có từ 1970, tái tạo từ 1990.
- CSV quốc gia và view SQLite: **39.643 dòng, 244 mã, 1850–2024**, khóa không trùng.
  File nguồn NASA vẫn giữ 1880–2025; không xóa dữ liệu lịch sử.

Bộ lọc lưu riêng thập kỷ, châu lục, quốc gia và màu bản đồ cho từng trang bằng
một Store và một callback cập nhật đồng thời. Đã bỏ hai callback bộ lọc cũ,
callback chọn bản đồ ghi trùng đầu ra, vòng tự chạy bản đồ mỗi 1,5 giây và các
đoạn giải thích dài lặp trong giao diện. Bấm ngoài châu lục đang chọn trên địa
cầu chuyển cả quốc gia và châu lục; bấm bản đồ EDA cũng cập nhật bộ lọc.
Nút Phát/Dừng dùng chuyển động Plotly với xử lý hủy promise khi dừng/đổi bộ lọc.

Mô hình được chạy lại và so sánh ba mốc học trên cùng bốn cửa sổ 1995–2014:
MAE mốc 1880: **0,036037°C**, 1961: **0,038280°C**, 1970: **0,048218°C**.
Chọn 1880 cho mô hình CO₂; kiểm tra cuối 2015–2024 cho R² **0,822917**,
MAE **0,030670°C**, RMSE **0,036991°C** trên mục tiêu trung bình 5 năm.
Baseline theo năm chọn từ 1970 có MAE test **0,104129°C**, giữ nhiệt độ cuối tập
học có MAE **0,218000°C**. Cấu hình tốt nhất vẫn dùng lịch sử 1880 nên kết quả
điểm không đổi sau chạy lại. Xem `mo_hinh_du_doan/nguyen_khang/GIAI_THICH.md`
và `so_sanh_giai_doan_huan_luyen.csv` để biết giới hạn và từng phép so sánh.

Kiểm chứng: **87/87 kiểm thử đạt** (83,626 giây), gồm đối chiếu nguồn–CSV–SQLite,
tái tạo mô hình và thử đổi nhiệt độ tương lai để chứng minh lựa chọn lịch sử
không dùng tập kiểm tra cuối. Chrome kiểm tra 7 trang, xuất CSV, nút Phát/Dừng,
chọn quốc gia trên cả 4 bản đồ, đổi châu lục, nhớ bộ lọc, 20 lần đổi năm sau khi
xoay địa cầu, mở rộng/đóng biểu đồ, bố cục 1440/1024/390 px: không lỗi console
hoặc JavaScript, không tràn ngang. Thử chạm Australia từ bộ lọc Châu Á trên
màn hình cảm ứng 390 px ở cả Tổng quan và Bản đồ: bộ lọc, hình và số liệu đồng bộ.

Tổng quan đã thay biểu đồ ngành bằng donut CO₂ theo châu lục, nên giai đoạn
1961–1969 vẫn có dữ liệu. Tab CO₂ thay area ngành bằng area châu lục; treemap
vẫn giữ phân tích ngành từ 1970. Khi đổi thập kỷ, thanh năm và địa cầu tự về năm
cuối khoảng; chọn lại Toàn bộ 1961–2024 đưa cả nhãn, màu và tooltip về 2024.

## Đợt trước: mở phạm vi 1880 (đã thay đổi bộ lọc ở trên)

Tổng quan toàn cầu và mô hình dùng chung chuỗi NASA + OWID **1880–2024**:
145 năm liên tiếp, không thiếu nhiệt độ, CO₂, CO₂ tích lũy hoặc trùng năm.
Bảng quốc gia và view SQLite mở về 1880: 33.114 dòng, 244 mã; nhiệt độ quốc gia
trước 1961 giữ null. CSV Tổng quan toàn cầu lấy đúng chuỗi toàn cầu đang vẽ.
CO₂ tích lũy giữ số nguồn, không đặt lại về 0 ở năm 1880.

Bộ lọc thập kỷ lưu riêng lựa chọn từng trang bằng một `dcc.Store` trong callback
có sẵn. Tổng quan 1880–2024; Nhiệt độ 1880–2025; CO₂, Bản đồ, Nhận định và
Dữ liệu giữ 1970–2024. Mô hình dùng lịch sử 1880–2024, có điều khiển kịch bản riêng.

Mô hình đã huấn luyện lại: 141 mẫu trung bình trượt đủ 5 năm, bắt đầu 1884.
Train 1884–2014 (131 mẫu), test 2015–2024 (10 mẫu), sau đánh giá fit toàn bộ
1884–2024 cho kịch bản. R² test 0,822917; MAE 0,030670°C; RMSE 0,036991°C.
Hệ số mới: intercept −0,2842913; coefficient 0,0007012609 trên CO₂ tích lũy Gt.
Có 24 cửa sổ đánh giá cuốn chiếu 1905–2024: 120 quan sát, MAE 0,089240°C,
độ phủ dải 77,5%. Trục biểu đồ đã mở về 1880 và hiển thị nhiệt độ lịch sử âm.
Những chỉ số và phạm vi trong các phần dưới đây là kết quả của đợt trước đó.

Kiểm chứng cuối của phạm vi mới: **81/81 kiểm thử đạt**, 74,022 giây; đối chiếu
CSV, SQLite, dữ liệu nguồn và tái tạo mô hình đều đạt. Chrome kiểm tra cả 7 trang,
nhớ riêng thập kỷ khi đổi trang, lịch sử từ 1880 và trục nhiệt độ âm. Có 20 lần
đổi năm sau khi xoay địa cầu; đã cố định lề để năm thiếu nhiệt độ không làm đổi
kích thước/góc nhìn. Không có lỗi JavaScript hoặc tràn ngang ở màn hình 390 px.

## Kết quả sửa lỗi dữ liệu trước khi mở phạm vi 1880

- Notebook `phan_tich_nhiet_do/duc/01_lam_sach_va_eda.ipynb` đã chạy đầy đủ 8 ô lệnh,
  lưu thứ tự thực thi 1–8, không có đầu ra lỗi. Ô kiểm tra độc lập xác nhận các
  nhiệt độ NASA, FAOSTAT và cờ nguồn khớp dữ liệu gốc; không trùng khóa năm/tháng.
  Các biểu đồ thập kỷ ghi đúng khoảng có số liệu, kể cả 1961–1969 và 2020–2025;
  bản đồ tĩnh lấy trung bình 2020–2025, không cố định riêng năm 2024.
- Giữ nguyên giá trị của `duc/nhiet_do_quoc_gia.csv` (năm khí tượng). Tạo riêng
  `duc/nhiet_do_quoc_gia_nam_lich.csv` từ tháng 1–12: 14.263 dòng, 1961–2025,
  13.459 dòng đủ 12 tháng và 804 dòng thiếu tháng giữ null. Bảng ghép và SQLite
  đọc bảng năm lịch; trang Nhiệt độ và EDA giữ chuỗi năm khí tượng, có ghi quy ước.
- CSV NASA vẫn giữ 1880–2025. `START_YEAR = 1970` và `END_YEAR = 2024` là phạm vi
  phân tích chung đã chọn, không phải giới hạn của nguồn nhiệt độ hoặc điều kiện
  bắt buộc để ghép nhiệt độ với CO₂. EDGAR theo ngành bắt đầu 1970; mô hình hiện
  tại dùng NASA + OWID, không dùng EDGAR. Không xóa lịch sử cũ của Đức và Quân.
- Chuẩn hóa đúng các dòng EDGAR có mã `ANT`, tên `Curaçao`, sang `CUW`; giữ mã
  nguồn ở `source_iso_alpha`. Giá trị phát thải không đổi. `SCG` giữ là thực thể
  gộp ở Europe: được tính trong phạm vi có cả Serbia và Montenegro, không gán cho
  một nước riêng. `ATA` được phân loại Antarctica ngay trong các bước làm sạch.
- EDGAR lưu `entity_type`, `sectors_available`, `sectors_expected`. Biểu đồ ghi
  tỷ trọng của các ngành có số liệu và số nhóm thiếu ngành; biểu đồ tái tạo ghi
  số quốc gia có số liệu, tránh diễn giải độ phủ thay đổi như xu hướng phát thải.
- Dữ liệu mô hình toàn cầu và dự đoán điểm không đổi: R² test 0,834506;
  MAE test 0,030610°C trên mục tiêu trung bình trượt 5 năm. Dải OLS giả định phần
  dư độc lập được thay bằng bootstrap phần dư theo khối 5 năm (2.000 mẫu, seed 18).
  Bổ sung `danh_gia_cuon_chieu.csv`: sáu cửa sổ test 5 năm, 30 quan sát,
  MAE trung bình 0,044406°C. Độ phủ dải phân vị 5%–95% là 76,7% trên đánh giá
  cuốn chiếu và 100% trên 10 quan sát holdout; chưa có căn cứ đảm bảo độ phủ
  tương lai 90%. Giao diện và tài liệu mô hình ghi rõ giới hạn này.

Kiểm chứng sau sửa: **78 kiểm thử đạt**, 61,095 giây, bằng lệnh
`python -X utf8 -m unittest discover -s bang_dieu_khien/nguyen_khang/kiem_thu -v`.
Các kiểm thử gồm tái tạo dữ liệu từ nguồn, đối chiếu toàn bộ bảng năm lịch với
12 tháng, bảo toàn giá trị sau ghép/lọc/SQLite, xử lý mã EDGAR và nhóm gộp,
trạng thái notebook, tái tạo kết quả mô hình và bảo đảm đánh giá chỉ fit quá khứ.
Dữ liệu gốc không bị sửa. Năm nhóm PNG của notebook đã được kiểm tra trực quan;
tiêu đề bản đồ được xuống dòng để không bị cắt chữ.

Kiểm thử Chrome trên dashboard cục bộ cũng đạt ở cả 7 trang: đồng bộ bộ lọc khi
chuyển trang, bản đồ/thập kỷ, mở và đóng biểu đồ, tương tác địa cầu, kịch bản và
tải CSV. Không có lỗi JavaScript hoặc lỗi console. Màn hình 390 px không tràn ngang.
Sơ đồ ERD đã bổ sung các trường nguồn/độ phủ ngành và được kết xuất kiểm tra.

## Đối chiếu trước sửa

## Kết quả chính

Không phát hiện bước làm sạch làm thay đổi sai giá trị nhiệt độ hoặc CO₂ toàn cầu
đang dùng cho mô hình. Cả 7 CSV được tái tạo từ nguồn và khớp bản đang lưu;
đối chiếu riêng trực tiếp với CSV/workbook gốc cũng khớp các giá trị và cờ nguồn.
Không có khóa trùng hoặc giá trị vô hạn trong 9 bảng đã kiểm tra.

Có vấn đề về mã quốc gia EDGAR, độ phủ dữ liệu và sự khác nhau giữa năm khí tượng
với năm lịch. Chúng ảnh hưởng đến phân tích/ghép dữ liệu quốc gia; hiện không đi vào
mô hình toàn cầu. Mô hình còn giới hạn về đánh giá trên chuỗi làm trượt và giả định
phần dư độc lập. Khớp nguồn không có nghĩa số liệu nguồn không có bất định đo lường.

## Các CSV đã kiểm tra

Tất cả đường dẫn trong bảng nằm dưới `data/du_lieu_da_xu_ly/`.

| CSV | Khoảng năm | Số dòng | Giá trị chính bị thiếu |
|---|---|---:|---|
| `duc/nhiet_do_toan_cau.csv` | 1880–2025 | 146 | 0 nhiệt độ |
| `duc/nhiet_do_quoc_gia.csv` | 1961–2025 | 14.263 | 496 nhiệt độ, 3,48% |
| `duc/nhiet_do_theo_thang.csv` | Toàn cầu 1880–2025; quốc gia 1961–2025 | 172.908 | 5.923 nhiệt độ, 3,43% |
| `quan/co2_quoc_gia.csv` | 1750–2024 | 42.480 | 19.072 CO₂, 44,90% trên toàn lịch sử |
| `quan/co2_toan_cau.csv` | 1750–2024 | 275 | 0 CO₂ hoặc CO₂ tích lũy |
| `quan/co2_theo_nganh.csv` | 1970–2025 | 82.040 | 2.712 CO₂ theo ngành, 3,31% |
| `quan/nang_luong_tai_tao.csv` | 1990–2024 | 7.673 | 0 tỷ lệ trong các dòng hiện có |

Tổng cộng đã đối chiếu 319.785 dòng của 7 CSV thành viên. Tỷ lệ thiếu CO₂ quốc gia
trên toàn lịch sử cao vì có nhiều năm cũ; riêng 1970–2024 là 459/11.990 dòng, 3,83%.
Không có dòng trong bảng khác với có dòng nhưng giá trị null; bảng tái tạo không có
null cũng không đồng nghĩa tất cả quốc gia đều có số liệu mỗi năm.

## Phát hiện ban đầu và ảnh hưởng

### 1. Mã EDGAR chưa thống nhất với khóa quốc gia dùng chung

Workbook và CSV theo ngành ghi `ANT` cho `Curaçao`; bảng OWID và danh mục UN M49
ghi `CUW` cho `Curacao`. Có 336 dòng theo ngành thuộc `ANT`, trong đó 330 dòng
ở 1970–2024. Lọc `CUW` không lấy được các dòng này. Đây là vấn đề khóa ghép;
các giá trị phát thải vẫn khớp workbook.

EDGAR còn dùng `SCG` cho `Serbia and Montenegro`: 448 dòng, trong đó 440 dòng
ở 1970–2024. EDGAR không có chuỗi riêng `SRB` và `MNE` trong bảng này.
`SCG` không thuộc danh mục ISO3 hiện tại; không được tự gán toàn bộ phát thải chung
cho Serbia hoặc Montenegro. Giữ riêng thực thể chung và ghi rõ phạm vi;
với `ANT`, cần xác nhận phạm vi lãnh thổ của nguồn trước khi chuẩn hóa sang `CUW`.

Hai mã này không có trong bảng quốc gia ghép. Chúng vẫn được tính khi biểu đồ ngành
lấy toàn bộ bảng EDGAR, nhưng có thể bị bỏ khi lọc theo danh sách quốc gia/châu lục
của bảng ghép. Không ảnh hưởng đầu vào mô hình hiện tại vì mô hình dùng dòng World
của OWID, không cộng CO₂ ngành EDGAR.

### 2. Nhiệt độ quốc gia là năm khí tượng, CO₂ là năm lịch

Đức lọc `Months = Meteorological year`. Năm này gồm tháng 12 năm trước và tháng
1–11 năm đang xét; NASA `J-D` dùng tháng 1–12. Cả hai cùng mốc tham chiếu 1951–1980,
nhưng NASA là chuỗi đất liền + đại dương, FAOSTAT là nhiệt độ trên đất liền.
[NASA giải thích năm khí tượng và chỉ số đất liền–đại dương](https://data.giss.nasa.gov/gistemp/faq/),
[FAO mô tả chuỗi nhiệt độ trên đất liền](https://www.fao.org/statistics/highlights-archive/highlights-detail/temperature-change-statistics-1961-2023.-global--regional-and-country-trends/en).

Đã kiểm tra 13.225 quốc gia–năm có đủ tháng tương ứng: trung bình tháng 12 trước
và tháng 1–11 khớp nhiệt độ năm FAOSTAT với chênh lệch tối đa 0,000917°C,
phù hợp độ chính xác số lẻ của nguồn. Ví dụ Việt Nam 2024: CSV năm +1,914°C;
trung bình năm khí tượng +1,913667°C; trung bình tháng 1–12 +1,821333°C.

Không phải lỗi lấy sai dòng của Đức. Khi xây dựng mô hình quốc gia theo năm lịch,
cần thống nhất cửa sổ thời gian hoặc ghi rõ quy ước; không mặc định hai nhãn năm
đại diện cùng 12 tháng. Mô hình hiện tại dùng NASA `J-D` và OWID nên không bị lệch này.

### 3. Độ phủ và cờ nguồn cần giữ khi phân tích

- FAOSTAT có 236 mã quốc gia/lãnh thổ. 13.767 giá trị nhiệt độ năm có số liệu đều
  mang cờ `E` (Estimated); 495 dòng `O` và 1 dòng `L` đều thiếu giá trị trong bản này.
  Không diễn giải null ở cột cờ như bằng chứng quan sát trực tiếp. Chuỗi NASA tháng
  để trống cờ vì không dùng hệ thống cờ FAOSTAT.
- Nhiệt độ quốc gia có 199 ngoại lai theo IQR. Chúng được giữ nguyên và khớp nguồn;
  phát hiện IQR không tự chứng minh sai dữ liệu. Nam Cực (`ATA`) thiếu nhãn châu lục
  trong CSV thành viên; bảng ghép và bộ đọc dashboard đã bổ sung `Antarctica`.
- EDGAR có 2.420 nhóm quốc gia–năm thiếu ít nhất một giá trị ngành trong các dòng
  ngành hiện có; riêng 2024 có 47/208 nhóm. Tỷ trọng hiện tính trên các giá trị không
  thiếu nên tổng vẫn bằng 100%. Tổng bằng 100% không chứng minh đủ dữ liệu ngành;
  cần diễn giải là tỷ trọng trong tổng phát thải ngành có số liệu.
- Tái tạo có 225 quốc gia năm 2023, chỉ 84 năm 2024. So sánh trung bình giữa hai năm
  mà không giữ cùng nhóm quốc gia có thể phản ánh thay đổi độ phủ.
- NASA 2026 mới có 8 tháng trong tệp gốc và đã loại khỏi CSV sạch. EDGAR 2025 được
  giữ ở CSV ngành; bảng ghép và mô hình hiện tại chỉ đến 2024.

Những bảng quốc gia, ngành, tháng và tái tạo này không được mô hình toàn cầu hiện tại
sử dụng. Nếu xây dựng mô hình có các biến đó, phải xử lý độ phủ và quy ước thời gian
trước khi fit; không tự thay null bằng 0 hoặc xóa ngoại lai chỉ vì vượt IQR.

### 4. Chênh lệch số lẻ không phải lỗi chuyển đổi đơn vị

Nhiệt độ giữ °C; CO₂ giữ Mt/năm; CO₂/người giữ tấn/người; biến hồi quy tích lũy
đổi Mt sang Gt bằng chia 1.000. EDGAR lọc `Substance = CO2`, không trộn các khí
nhà kính khác vào CO₂. Tái tạo là % tổng tiêu thụ năng lượng cuối cùng.

Các chênh lệch số thực khi tái tạo CSV phát sinh ở mức khoảng 1e-12 hoặc nhỏ hơn.
CO₂/người của OWID không luôn bằng phép chia hai cột đã làm tròn, nhưng toàn bộ
chênh lệch kiểm tra đều nằm trong biên tương thích với làm tròn CO₂ đến 0,001 Mt
và CO₂/người đến 0,001 tấn/người.

CO₂ tích lũy nguồn khác tổng cộng các CO₂ năm đã xuất số lẻ: năm 2024 chênh
0,021 Mt trên khoảng 1.849.124 Mt. Thử dùng tổng cộng từ 1750 thay cho cột tích lũy
nguồn và fit lại: dự đoán 2050 của kịch bản tiếp diễn đổi khoảng 5,15e-9°C.
Không có ảnh hưởng thực tế đáng kể từ chênh lệch này trong phép thử.

## Kiểm tra mô hình trước sửa

Đầu vào: `nguyen_khang/khi_hau_toan_cau_nam.csv`, 55 năm liên tiếp 1970–2024,
không thiếu `temperature_anomaly`, `co2`, `cumulative_co2`; không trùng năm.
Nguồn nhiệt độ là NASA toàn cầu; nguồn CO₂ là dòng World của OWID.

Mô hình dùng dữ liệu từng năm; bộ lọc thập kỷ trên giao diện không thay dữ liệu huấn luyện.
Đích dự đoán là trung bình trượt 5 năm, có 51 quan sát: train 41 năm 1974–2014,
test 10 năm 2015–2024. Chia theo thời gian; backtest khớp phép fit chỉ trên train.
Việc fit lại toàn bộ dữ liệu chỉ phục vụ tạo kịch bản sau đánh giá.

| Kiểm chứng | Kết quả |
|---|---|
| R² test tính lại | 0,834506 |
| MAE test tính lại | 0,030610°C |
| RMSE test tính lại | 0,035760°C |
| MAE đường cơ sở hồi quy theo năm, cùng split | 0,097813°C |
| MAE giữ giá trị cuối train, cùng split | 0,218000°C |
| Tương quan phần dư lag 1, fit toàn bộ | 0,744426 |
| Durbin–Watson, fit toàn bộ | 0,507395 |

Đã tái tạo và đối chiếu `du_doan_kiem_tra.csv`, `kich_ban_2050.csv` và
`thong_tin_mo_hinh.json`; tất cả khớp trong sai số biểu diễn số thực.

Hai giới hạn quan trọng:

1. MAE 0,031°C là lỗi trên trung bình trượt 5 năm, không phải nhiệt độ riêng mỗi năm.
   Nếu chỉ đối chiếu cùng dự đoán với nhiệt độ năm chưa làm trượt, MAE là 0,124047°C;
   phép đối chiếu này minh họa khác biệt biến mục tiêu, không thay thế chỉ số đánh giá
   đúng của mô hình hiện tại. CO₂ trong tập test là số liệu đã biết, nên backtest
   không kiểm chứng khả năng dự báo CO₂ của các kịch bản tương lai.
2. Phần dư có tự tương quan mạnh. Dải OLS 90% hiện giả định phần dư độc lập;
   không có căn cứ đảm bảo độ phủ thực tế đúng 90%. Tài liệu mô hình đã ghi đây là
   dải xấp xỉ. Nên bổ sung đánh giá cuốn chiếu và khoảng dự đoán có xét phụ thuộc
   thời gian trước khi diễn giải độ chắc chắn của dự đoán dài hạn.

Kiểm tra thêm bằng sáu lần chia theo thời gian, mỗi lần test 5 năm:

| Cuối train | Test | MAE (°C) | RMSE (°C) |
|---:|---|---:|---:|
| 1994 | 1995–1999 | 0,070799 | 0,076669 |
| 1999 | 2000–2004 | 0,014145 | 0,016973 |
| 2004 | 2005–2009 | 0,026140 | 0,027276 |
| 2009 | 2010–2014 | 0,092965 | 0,096614 |
| 2014 | 2015–2019 | 0,034015 | 0,039220 |
| 2019 | 2020–2024 | 0,028371 | 0,031943 |

MAE trung bình sáu cửa sổ là 0,044406°C. Hiệu quả thay đổi theo giai đoạn;
không chỉ dựa vào một lần chia train/test để khẳng định khả năng dự đoán đến 2050.

Thử giữ lịch sử NASA từ 1880, dùng cùng biến và cùng test 2015–2024:
train sau rolling là 1884–2014, MAE 0,030670°C, RMSE 0,036991°C. Trong phép thử này
thêm lịch sử cũ không cải thiện MAE rõ rệt. Dữ liệu trước 1961 vẫn hợp lệ để phân tích
toàn cầu; không cần xóa khỏi CSV vì biểu đồ quốc gia chưa có dữ liệu.

## Kiểm chứng ban đầu chạy trên dự án

```powershell
python -X utf8 -m unittest discover -s bang_dieu_khien/nguyen_khang/kiem_thu -v
```

Kết quả: **66 kiểm thử đạt**, thời gian 54,373 giây. Bên cạnh bộ kiểm thử, đã thực hiện
đối chiếu độc lập tất cả giá trị năm/tháng với CSV gốc, toàn bộ các năm và ngành với
workbook EDGAR, cờ FAOSTAT, công thức tăng trưởng, tái tạo báo cáo chất lượng,
hai bảng ghép và kết quả mô hình. Các thử nghiệm không ghi đè dữ liệu nguồn,
CSV đã xử lý hoặc kết quả mô hình đang dùng.

Ưu tiên được xác định ở đợt kiểm tra ban đầu: làm rõ và thống nhất khóa EDGAR, ghi rõ năm khí tượng của dữ liệu
quốc gia, công khai độ phủ khi tính tỷ trọng ngành/tái tạo, rồi bổ sung đánh giá
cuốn chiếu và khoảng dự đoán có xét tự tương quan. Đây là các phát hiện của đợt
kiểm tra trước sửa; kết quả thực hiện sau đó được ghi ở đầu báo cáo này.
