# Mô hình và kịch bản nhiệt độ toàn cầu

## Câu hỏi

Nếu phát thải CO₂ toàn cầu thay đổi sau năm 2024, xu hướng nhiệt độ trung bình 5 năm
đến năm 2050 thay đổi như thế nào?

## Dữ liệu

- Nhiệt độ toàn cầu: NASA GISTEMP.
- CO₂ hằng năm và CO₂ tích lũy: OWID/Global Carbon Project.
- Giai đoạn chung: 1970–2024.
- Biến mục tiêu: trung bình trượt 5 năm của `temperature_anomaly`.
- Biến đầu vào: `cumulative_co2` đổi từ Mt sang Gt.

## Mô hình

Linear Regression đơn biến:

```text
temperature_trend_5y = intercept + coefficient × cumulative_co2_gt
temperature_trend_5y = -0,3112 + 0,0007194 × cumulative_co2_gt
```

Mô hình được huấn luyện trên 1974–2014 và kiểm tra trên 2015–2024. Sau khi đánh giá,
mô hình được huấn luyện lại bằng toàn bộ dữ liệu 1974–2024 để tạo kịch bản tương lai.

| Chỉ số | Kết quả |
|---|---:|
| Số quan sát hợp lệ | 51 |
| R² trên tập huấn luyện | 0,956 |
| R² trên tập kiểm tra | 0,835 |
| MAE trên tập kiểm tra | 0,031 °C |
| RMSE trên tập kiểm tra | 0,036 °C |

## Kịch bản 2025–2050

1. **Tiếp diễn xu hướng:** CO₂ hằng năm thay đổi theo tốc độ trung bình 2005–2024.
2. **Giữ mức năm 2024:** CO₂ hằng năm không đổi.
3. **Giảm 5% mỗi năm:** CO₂ hằng năm giảm 5% so với năm trước.
4. **Tùy chỉnh trên dashboard:** người dùng chọn từ -10% đến +5% mỗi năm.

CO₂ hằng năm của mỗi kịch bản được cộng vào CO₂ tích lũy. Giá trị tích lũy sau đó được
đưa vào phương trình hồi quy để mô phỏng xu hướng nhiệt độ. Hàm `kich_ban()` được dùng
chung cho CSV và thanh trượt dashboard để hai nơi luôn cho cùng kết quả.

Dải trên biểu đồ là khoảng dự đoán OLS 90% xấp xỉ, dùng phân vị Student-t với
49 bậc tự do và sai số phần dư của mô hình fit toàn bộ. Dải này giả định phần dư độc lập,
phương sai không đổi; trung bình trượt có tự tương quan nên không khẳng định độ phủ
thực tế đạt 90%. Dải chưa bao gồm bất định phát thải hoặc các yếu tố khí hậu khác.

## Hiển thị trên dashboard

- Biểu đồ chính: quan trắc trung bình 5 năm và ba kịch bản tới 2050; đánh dấu năm được chọn.
- Ba chỉ số: độ lệch nhiệt độ, chênh so với tiếp diễn, phát thải năm được chọn (Gt/năm).
- Biểu đồ phát thải: lượng CO₂ hằng năm, không phải CO₂ tích lũy.
- Biểu đồ kiểm tra: dự đoán và quan trắc cùng là trung bình 5 năm, trên 2015–2024;
  R² và MAE hiển thị đều tính trên tập test. Test dùng CO₂ đã quan trắc, không đánh giá
  khả năng dự báo CO₂ tương lai.
- Phương pháp thu gọn mặc định; dữ liệu đầy đủ và hai cận vẫn có trong CSV tải xuống.

## Cách đọc kết quả

Kết quả thể hiện mối liên hệ thống kê quan sát được trong dữ liệu lịch sử. Chênh lệch giữa
các đường giúp người dùng so sánh tác động của giả định phát thải lên kết quả mô phỏng.

## Giới hạn

- Chỉ có 51 quan sát sau khi tạo trung bình trượt 5 năm.
- Mô hình tuyến tính không mô tả đầy đủ hệ thống khí hậu vật lý.
- Mô hình không đưa vào đại dương, aerosol, núi lửa, El Niño và các phản hồi khí hậu.
- CO₂ tích lũy và nhiệt độ đều tăng theo thời gian nên không diễn giải hệ số như bằng
  chứng nhân quả tuyệt đối.
- Kết quả đến 2050 phụ thuộc vào giả định phát thải và không phải dự báo chính thức.
