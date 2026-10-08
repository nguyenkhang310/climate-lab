# Kiểm tra mô hình theo Chương 9 - Mô hình dự báo

Nguồn đối chiếu: `GSV_Chuong09_mohinhdubao.pdf` (53 slide).

## Kết luận

Sau khi bổ sung chẩn đoán và giao diện, mô hình **đúng loại bài toán và đã hoàn thiện cho phạm vi đồ án** theo các yêu cầu hồi quy phù hợp trong slide 20-27. Các giả định chưa đạt được hiển thị công khai thay vì bị che đi.

Mô hình phù hợp để trình bày một **kịch bản có điều kiện theo CO₂** trong đồ án môn học. Mô hình chưa đủ cơ sở để được diễn giải như một dự báo khí hậu chính thức đến 2050.

Logistic Regression, threshold và confusion matrix trong slide 28-49 không áp dụng cho dự án này vì biến mục tiêu là nhiệt độ liên tục. Chọn Linear Regression thay vì Logistic Regression là đúng.

## Những phần đã làm đúng

| Yêu cầu từ bài giảng | Hiện trạng | Đánh giá |
|---|---|---|
| Xác định biến mục tiêu Y và biến giải thích X | Y là nhiệt độ trung bình trượt 5 năm; X là CO₂ tích lũy | Đạt |
| Chọn mô hình theo loại Y | Linear Regression cho Y liên tục | Đạt |
| Chuẩn bị dữ liệu | Chuỗi 1880-2024 đủ năm, không có khóa trùng hoặc giá trị vô hạn | Đạt |
| Train / validation / test | Validation cuốn chiếu 1995-2014; holdout 2015-2024 | Đạt tốt |
| Tránh nhìn trước tương lai | Không chia ngẫu nhiên; holdout không tham gia chọn lịch sử | Đạt tốt |
| Metrics | Có R², MAE, MSE, RMSE; kết quả test được tính lại từ code | Đạt |
| So sánh đối chứng | Có baseline theo năm và persistence | Đạt |
| Trực quan thực tế và dự báo | Có đường thực tế, dự báo và backtest | Đạt |
| Mức độ bất định | Có dải bootstrap 5%-95%, block length chọn theo ACF | Đạt có giới hạn |
| Diễn giải giới hạn | Tài liệu đã nói rõ quan hệ không chứng minh nhân quả và còn thiếu biến khí hậu | Đạt |

Các kết quả hiện tại được tái lập đúng:

- Train: 131 quan sát (1884-2014).
- Test: 10 quan sát (2015-2024).
- R² train: 0,919.
- R² test: 0,823.
- MAE test: 0,03067°C.
- MSE test: 0,001368°C².
- RMSE test: 0,03699°C.

So sánh thêm trên cùng các cửa sổ thời gian cho thấy mô hình bậc 2 và bậc 3 kém hơn rõ rệt. Kiểm định RESET có p = 0,105, nên chưa có bằng chứng đủ mạnh để thay đường tuyến tính bằng đa thức. Linear Regression vẫn là lựa chọn đơn giản hợp lý cho câu hỏi hiện tại.

## Các chẩn đoán đã được bổ sung

### 1. Residual không ngẫu nhiên quanh 0

Slide 23-25 yêu cầu xem residual plot và tìm dạng cong, hình phễu, cụm hoặc đoạn riêng. Chẩn đoán trên tập train cho kết quả:

- Tương quan residual lag 1: 0,935.
- Durbin-Watson: 0,130 (rất xa mức gần 2 của sai số ít tự tương quan).
- Ljung-Box p-value tại lag 1, 5 và 10 đều nhỏ hơn 10^-26.
- ACF còn dương đến khoảng lag 18.

Residual tạo thành các đoạn dài cùng dấu theo thời gian. Mô hình đang bỏ sót cấu trúc thời gian hoặc các biến khí hậu khác. Dashboard hiện đã có residual plot theo năm và đánh dấu các điểm Cook để đáp ứng phần trực quan của bài giảng.

### 2. Phương sai residual không ổn định và phân phối không chuẩn

- Breusch-Pagan p = 0,0076: có bằng chứng phương sai thay đổi.
- Shapiro-Wilk p = 0,0001: residual không có phân phối chuẩn.
- Có 7 quan sát vượt ngưỡng Cook 4/n; Cook lớn nhất 0,051 ở năm 1944. Không có một điểm phá hủy toàn bộ mô hình, nhưng ảnh hưởng của các giai đoạn bất thường cần được trình bày.

Điều này không làm dự báo điểm tự động trở thành sai, nhưng làm các khoảng bất định kiểu residual bootstrap cần được diễn giải thận trọng.

### 3. Block bootstrap 5 năm chưa bao phủ hết phụ thuộc thời gian

Độ dài khối không còn cố định bằng 5. Code chọn lag đầu tiên trong 5-15 mà ACF không vượt ngưỡng `1,96/√n`; dữ liệu hiện tại chọn khối 10 năm và tạo dải 2050 thận trọng hơn.

Độ phủ 100% trên 20 điểm validation và 10 điểm test không chứng minh dải 90% được hiệu chỉnh tốt, vì mẫu nhỏ và các mục tiêu 5 năm chồng lấn nhau.

### 4. Dự báo 2050 là ngoại suy rõ rệt

Slide 20, 23 và 26 cảnh báo không đọc đường hồi quy quá xa vùng dữ liệu. CO₂ tích lũy năm 2050 so với mức lớn nhất đã quan sát năm 2024 là:

| Kịch bản | Mức X năm 2050 so với cực đại quan sát |
|---|---:|
| Giảm 5%/năm | 1,29 lần |
| Giữ mức 2024 | 1,54 lần |
| Tiếp diễn | 1,66 lần |

Dashboard hiện ghi trực tiếp tỷ lệ ngoại suy tại mốc người dùng chọn và nói rõ miền quan sát kết thúc ở năm 2024.

### 5. Tập test nhỏ và phụ thuộc nhau

Test có 10 năm, nhưng mỗi Y là trung bình của 5 năm liên tiếp nên các quan sát test chồng lấn mạnh. R² = 0,823 và MAE = 0,031°C là đúng theo phép tính hiện tại, nhưng không nên dùng như bằng chứng mạnh rằng mô hình tổng quát hóa tốt cho mọi giai đoạn tương lai.

### 6. Dashboard đã đủ thành phần hồi quy cần thiết

Trang mô hình hiện có lịch sử/kịch bản, phát thải, thực tế-vs-dự báo và phần dư. Phần giao diện đã bổ sung:

- Residual plot và điểm vượt ngưỡng Cook `4/n`.
- R², MAE, MSE, RMSE và số mẫu test.
- Durbin-Watson, Breusch-Pagan và diễn giải hệ số.
- Cảnh báo ngoại suy theo phạm vi X đã học.
- Cảnh báo rằng chuỗi test là trung bình trượt chồng lấn.

## Mức độ hoàn thiện

- **Theo quy trình đồ án môn học:** hoàn thiện; mô hình đúng loại, chia dữ liệu đúng thời gian, có validation, holdout, baseline và bất định.
- **Theo nội dung hồi quy phù hợp của Chương 9:** đạt; có residual plot và trình bày rõ các giả định bị vi phạm.
- **Theo chuẩn dự báo khoa học:** chưa đủ; kết quả 2050 phải giữ nhãn “kịch bản minh họa có điều kiện”, không gọi là dự báo chính thức.

## Những việc đã hoàn thiện

1. Đã thêm residual plot theo năm vào dashboard.
2. Đã hiển thị R², MAE, MSE, RMSE cùng số lượng mẫu test.
3. Đã hiển thị cảnh báo ngoại suy và tỷ lệ X so với cực đại đã quan sát.
4. Đã thêm Durbin-Watson, Breusch-Pagan và Cook bằng ngôn ngữ đơn giản.
5. Đã chọn block length tự động theo ACF; dữ liệu hiện tại chọn 10 năm.
6. Đã giữ rolling validation bốn giai đoạn và holdout độc lập 2015-2024.
7. Đã so sánh đa thức và GLSAR; không có cải thiện ổn định nên giữ Linear Regression.

Không nên thêm Logistic Regression, confusion matrix hoặc threshold vào dự án này, vì chúng không phù hợp với biến mục tiêu nhiệt độ liên tục.
