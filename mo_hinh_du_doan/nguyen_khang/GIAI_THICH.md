# Mô hình và kịch bản nhiệt độ toàn cầu

## Câu hỏi

Nếu phát thải CO₂ toàn cầu thay đổi sau năm 2024, xu hướng nhiệt độ trung bình 5 năm
đến năm 2050 thay đổi như thế nào?

## Dữ liệu

- Nhiệt độ toàn cầu: NASA GISTEMP.
- CO₂ hằng năm và CO₂ tích lũy: OWID/Global Carbon Project.
- Giai đoạn chung: 1880–2024, đủ 145 năm liên tiếp.
- Biến mục tiêu: trung bình trượt 5 năm của `temperature_anomaly`.
- Biến đầu vào: `cumulative_co2` đổi từ Mt sang Gt.
- `START_YEAR = 1850` phục vụ trang CO₂. Phép ghép toàn cầu bắt đầu 1880 theo NASA;
  Tổng quan hiển thị 1961–2024, độc lập với thời gian học. Các CSV nguồn giữ đầy đủ; chuỗi quốc gia dùng bảng năm lịch
  `duc/nhiet_do_quoc_gia_nam_lich.csv`, còn mô hình dùng NASA `J-D` và OWID World.

## Mô hình

Linear Regression đơn biến:

```text
temperature_trend_5y = intercept + coefficient × cumulative_co2_gt
temperature_trend_5y = -0,2843 + 0,0007013 × cumulative_co2_gt
```

Trung bình trượt đủ 5 năm đầu tiên là năm 1884, tính từ 1880–1884; không thêm
giá trị giả cho 1880–1883. Có 131 mẫu huấn luyện 1884–2014 và 10 mẫu kiểm tra
2015–2024. Sau đánh giá, mô hình được fit lại bằng cả 141 mẫu 1884–2024 để tạo
kịch bản. CO₂ tích lũy giữ nguyên cột nguồn, gồm cả phát thải trước 1880;
không đặt lại lượng tích lũy về 0 tại năm bắt đầu bộ lọc.

| Chỉ số | Kết quả |
|---|---:|
| Số quan sát hợp lệ | 141 |
| R² trên tập huấn luyện | 0,919 |
| R² trên tập kiểm tra | 0,823 |
| MAE trên tập kiểm tra | 0,031 °C |
| MSE trên tập kiểm tra | 0,001368 °C² |
| RMSE trên tập kiểm tra | 0,037 °C |

## Kịch bản 2025–2050

1. **Tiếp diễn xu hướng:** CO₂ hằng năm thay đổi theo tốc độ trung bình 2005–2024.
2. **Giữ mức năm 2024:** CO₂ hằng năm không đổi.
3. **Giảm 5% mỗi năm:** CO₂ hằng năm giảm 5% so với năm trước.
4. **Tùy chỉnh trên dashboard:** người dùng chọn từ -10% đến +5% mỗi năm.

CO₂ hằng năm của mỗi kịch bản được cộng vào CO₂ tích lũy. Giá trị tích lũy sau đó được
đưa vào phương trình hồi quy để mô phỏng xu hướng nhiệt độ. Hàm `kich_ban()` được dùng
chung cho CSV và thanh trượt dashboard để hai nơi luôn cho cùng kết quả.

Dải trên biểu đồ lấy phân vị 5%–95% từ **circular block residual bootstrap**:
2.000 lần lấy mẫu, seed 18. Độ dài khối được chọn từ tự tương quan phần dư: lấy
lag đầu tiên từ 5–15 có tương quan không còn vượt ngưỡng nhiễu `1,96/√n`; dữ liệu
hiện tại chọn khối **10 năm**. Các khối giữ sự phụ thuộc giữa
các phần dư lân cận; mỗi lần lấy mẫu tính lại hệ số hồi quy và lấy khối phần dư
cho tương lai. `prediction_interval()` được dùng chung cho CSV và kịch bản tùy chỉnh.

Phần dư có tương quan lag 1 khoảng 0,929, vì vậy không tiếp tục dùng công thức OLS
giả định các phần dư độc lập. Bootstrap vẫn là xấp xỉ, phụ thuộc giả định cấu trúc
phần dư có thể đại diện cho tương lai; chưa gồm sai số nguồn và bất định phát thải.
Không khẳng định độ phủ thực tế đạt đúng 90%.

Chẩn đoán trên 131 mẫu train cho Durbin–Watson **0,130**, Breusch–Pagan
**p = 0,0076** và Shapiro–Wilk **p = 0,0001**. Có **7** điểm vượt ngưỡng Cook
`4/n`; lớn nhất là năm 1944 với Cook = 0,051. Vì phần dư còn tự tương quan,
phương sai chưa đều và không chuẩn, các chỉ số test và dải 90% phải được đọc thận trọng.
File `phan_du_huan_luyen.csv` lưu các giá trị fitted, residual, leverage và Cook để
tái kiểm tra; dashboard hiển thị phần dư thay vì che các giả định chưa đạt.

## Chọn giai đoạn học và kiểm tra theo thời gian

So sánh lịch sử từ 1880, 1961, 1970 trên **cùng** các giai đoạn đánh giá
1995–1999, 2000–2004, 2005–2009, 2010–2014. Mỗi lần chỉ học từ các năm trước
giai đoạn đánh giá; không chia ngẫu nhiên. Cách chia tuân theo nguyên tắc
[đánh giá chuỗi thời gian của scikit-learn](https://scikit-learn.org/stable/modules/cross_validation.html#time-series-split).
Trung bình 5 năm chỉ dùng năm hiện tại và bốn năm trước, không dùng trung bình giữa.
Chuỗi mục tiêu được tính trên toàn bộ NASA trước khi lọc năm học; mốc 1961/1970
là năm đích đầu tiên được học, với bốn năm trước đó chỉ làm ngữ cảnh tính trung bình.

| Lịch sử bắt đầu | MAE CO₂ tích lũy | MAE xu hướng theo năm | MAE giữ nhiệt độ cuối tập học |
|---|---:|---:|---:|
| 1880 | 0,0360 | 0,2400 | 0,0505 |
| 1961 | 0,0383 | 0,0532 | 0,0505 |
| 1970 | 0,0482 | 0,0335 | 0,0505 |

Chọn 1880 vì MAE thấp nhất trong ba mô hình nhận CO₂ tích lũy, phù hợp câu hỏi
kịch bản phát thải. Xu hướng theo năm từ 1970 có MAE validation thấp hơn một chút;
không khẳng định mô hình CO₂ thắng mọi baseline. Mô hình theo năm không phản ứng
với thay đổi phát thải nên dùng làm đối chứng, không dùng tạo các kịch bản CO₂.
File `so_sanh_giai_doan_huan_luyen.csv` lưu đủ bảng trên; `danh_gia_cuon_chieu.csv`
lưu từng cửa sổ của lịch sử được chọn. Dữ liệu 2015–2024 không tham gia lựa chọn.

Đánh giá cuối **2015–2024** với cấu hình đã chọn: MAE CO₂ **0,030670°C**,
MSE **0,001368°C²**, RMSE **0,036991°C**, R² **0,822917**. Baseline theo năm dùng lịch sử 1970
(chọn qua validation) có MAE **0,104129°C**, giữ nhiệt độ cuối tập học có
MAE **0,218000°C**. Điểm đánh giá là nhiệt độ trung bình 5 năm **với CO₂ đã biết**;
không phải sai số dự báo nhiệt độ từng năm hay sai số dự báo CO₂ tương lai.

Dải bootstrap bao phủ 20/20 quan sát validation và 10/10 quan sát holdout. Số mẫu
nhỏ và các mục tiêu trung bình trượt phụ thuộc nhau; không suy ra dải tương lai
có độ phủ 100% hoặc bảo đảm 90%. Sau đánh giá đã chạy lại mô hình và xuất lại
các CSV, hệ số và khoảng dự đoán. Cấu hình được chọn vẫn dùng lịch sử 1880,
nên dự đoán điểm giữ nguyên; không sửa số liệu để làm sai số trông nhỏ hơn.

## Hiển thị trên dashboard

- Biểu đồ chính: quan trắc trung bình 5 năm và ba kịch bản tới 2050; đánh dấu năm được chọn.
- Ba chỉ số: độ lệch nhiệt độ, chênh so với tiếp diễn, phát thải năm được chọn (Gt/năm).
- Biểu đồ phát thải: lượng CO₂ hằng năm, không phải CO₂ tích lũy.
- Biểu đồ kiểm tra: dự đoán và quan trắc cùng là trung bình 5 năm, trên 2015–2024;
  R², MAE, MSE và RMSE hiển thị đều tính trên tập test. Test dùng CO₂ đã quan trắc, không đánh giá
  khả năng dự báo CO₂ tương lai.
- Biểu đồ phần dư theo năm: tô cam các điểm vượt ngưỡng Cook `4/n`; phần phương pháp
  ghi rõ Durbin–Watson và Breusch–Pagan.
- Mỗi mốc kịch bản ghi tỷ lệ CO₂ tích lũy so với cực đại quan sát năm 2024. Đến 2050,
  tỷ lệ lần lượt là 1,66 (tiếp diễn), 1,54 (giữ mức) và 1,29 (giảm 5%/năm), nên đều là ngoại suy.
- Phương pháp thu gọn mặc định; dữ liệu đầy đủ và hai cận vẫn có trong CSV tải xuống.

## Cách đọc kết quả

Kết quả thể hiện mối liên hệ thống kê quan sát được trong dữ liệu lịch sử. Chênh lệch giữa
các đường giúp người dùng so sánh tác động của giả định phát thải lên kết quả mô phỏng.

## Giới hạn

- Có 141 quan sát sau khi tạo trung bình trượt 5 năm; các mẫu lân cận phụ thuộc nhau.
- Tập test chỉ có 10 mục tiêu trung bình trượt chồng lấn; kết quả tốt chưa chứng minh
  mô hình tổng quát hóa cho mọi giai đoạn tương lai.
- Mô hình tuyến tính không mô tả đầy đủ hệ thống khí hậu vật lý.
- Mô hình không đưa vào đại dương, aerosol, núi lửa, El Niño và các phản hồi khí hậu.
- CO₂ tích lũy và nhiệt độ đều tăng theo thời gian nên không diễn giải hệ số như bằng
  chứng nhân quả tuyệt đối.
- Kết quả đến 2050 phụ thuộc vào giả định phát thải và không phải dự báo chính thức.
