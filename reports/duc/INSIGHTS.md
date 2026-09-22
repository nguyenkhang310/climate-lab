# Khai phá Insight & Storytelling — Nhiệt độ Toàn cầu & Quốc gia (Phần Đức)

**Tác giả:** Huỳnh Cao Trung Đức (Nhóm 18 — Climate Lab)  
**Nguồn dữ liệu:**
- Chuỗi nhiệt độ toàn cầu: NASA GISS — GISTEMP v4 (1880–2025).
- Chuỗi nhiệt độ quốc gia: FAOSTAT Temperature Change on Land (1961–2025).
- Danh mục chuẩn hóa: UN M49 numeric sang ISO-3166-1 alpha-3 & phân loại châu lục Our World in Data (OWID).  
**Quy chuẩn & Đơn vị:** Độ lệch nhiệt độ (°C) so với thời kỳ cơ sở chuẩn **1951–1980 (0°C)**.

---

## 1. Xu hướng Nóng lên Toàn cầu qua Thời gian (1880–2025)

Dựa trên biểu đồ đường (`01_xu_huong_nhiet_do_toan_cau.png`) và biểu đồ cột theo thập kỷ (`02_nhiet_do_theo_thap_ky.png`):

- **Giai đoạn trước 1940:** Nhiệt độ toàn cầu dao động dưới mốc baseline, trung bình từ -0.3°C đến -0.1°C. Đây là thời kỳ trước khi công nghiệp hóa bùng nổ trên quy mô toàn cầu.
- **Giai đoạn 1940–1970:** Xuất hiện giai đoạn chững lại ngắn (plateau) do ảnh hưởng cộng hưởng của bụi khí dung sulfate (aerosols) từ các hoạt động công nghiệp thời kỳ hậu Thế chiến II làm cản trở bức xạ mặt trời.
- **Giai đoạn bùng nổ từ 1970 đến nay:** Nhiệt độ toàn cầu bước vào quỹ đạo tăng dốc đứng liên tục:
  - Thập niên 1980s: Trung bình +0.18°C.
  - Thập niên 1990s: Trung bình +0.32°C.
  - Thập niên 2000s: Trung bình +0.51°C.
  - Thập niên 2010s: Trung bình +0.81°C.
  - Thập niên 2020s (2020–2025): Trung bình vọt lên **+1.08°C**.
- **Kỷ lục lịch sử:** Năm **2023 (+1.17°C)** và năm **2024 (+1.29°C)** liên tiếp xô đổ mọi kỷ lục quan sát trong lịch sử nhân loại kể từ năm 1880.

---

## 2. Bất đối xứng Không gian & Hiện tượng Khuếch đại Bắc Cực (Arctic Amplification)

Dựa trên bản đồ thế giới năm 2024 (`03_ban_do_nhiet_do.html / png`) và biểu đồ nhiệt theo châu lục (`04_heatmap_chau_luc_thap_ky.png`):

- **Ấm lên không đồng đều giữa các vĩ độ:**
  - Các khu vực cận xích đạo và đại dương có mức tăng nhiệt độ ôn hòa hơn (+0.8°C đến +1.4°C).
  - Vùng cực Bắc và các quốc gia vĩ độ cao chứng kiến mức tăng nhiệt độ nhanh gấp **2 đến 3 lần** mức trung bình toàn cầu (hiện tượng *Khuếch đại Bắc Cực* — do hiện tượng phản xạ albedo giảm mạnh khi băng tuyết tan chảy làm lộ mặt đất và mặt biển tối màu hấp thụ nhiều nhiệt hơn).
  - Quần đảo Svalbard and Jan Mayen (`SJM`), Greenland, miền bắc Canada và Nga ghi nhận các dị thường nhiệt độ vượt ngưỡng **+3.5°C đến +5.3°C** (đạt đỉnh vào các năm 2016, 2018, 2020 và 2024–2025).
- **So sánh tốc độ giữa các Châu lục:**
  - **Châu Âu (Europe)** là châu lục lục địa ấm lên nhanh nhất thế giới: từ mức âm ở thập niên 1960s (-0.11°C) vọt lên **+2.02°C** ở thập niên 2020s.
  - **Châu Á (Asia)** tăng từ +0.07°C lên **+1.58°C**.
  - **Bắc Mỹ (North America)** tăng từ +0.15°C lên **+1.54°C**.
  - **Châu Phi (Africa)** tăng từ +0.06°C lên **+1.35°C**, đe dọa trực tiếp đến an ninh lương thực và nguồn nước tại vùng Sahel và cận Sahara.

---

## 3. Phân bố Độ lệch Nhiệt độ giữa các Quốc gia (Boxplot Evolution)

Dựa trên biểu đồ hộp (`05_phan_bo_nhiet_do_quoc_gia.png`):

- **Độ dịch chuyển của phân phối:** Đường trung vị (median) và trung bình (mean) của tất cả các quốc gia trên thế giới dịch chuyển tịnh tiến lên phía trên qua từng thập kỷ mà không có dấu hiệu đảo chiều.
- **Độ phân tán và các giá trị cực đoan (Outliers):**
  - Khoảng biến thiên giữa các tứ phân vị (IQR) ngày càng mở rộng, phản ánh sự phân hóa sâu sắc về tác động khí hậu giữa các vùng địa lý.
  - Số lượng điểm ngoại lai tích cực (cực nóng) tăng vọt sau năm 2010. Không có bất kỳ điểm ngoại lai cực lạnh nào xuất hiện ở thập niên 2020s.
  - Phân tích cờ dữ liệu FAO khẳng định toàn bộ 199 quan sát ngoại lai vượt ngưỡng IQR ($> 2.42^\circ\text{C}$) đều mang cờ **`E` (Estimated)** hợp lệ từ trạm đo mặt đất và vệ tinh của NASA/FAO, chứng minh đây là các hiện tượng nắng nóng cực đoan có thật chứ không phải lỗi dữ liệu.

---

## 4. Mô hình Hồi quy Tuyến tính & Phân tích Dự báo Xu hướng đến năm 2050

Dựa trên mô hình OLS và biểu đồ dự báo (`06_du_bao_hoi_quy_tuyen_tinh.png / html`):

### 4.1. Thông số Kỹ thuật & Chỉ số Đánh giá Mô hình
Mô hình hồi quy tuyến tính đơn biến được huấn luyện trên giai đoạn hiện đại (1970–2025, $n=56$ năm):

$$\widehat{\text{temperature\_anomaly}} = -39.739 + 0.0202 \times \text{year}$$

- **Hệ số xác định ($R^2$):** **0.9075** (giải thích được hơn 90.7% phương sai biến thiên nhiệt độ toàn cầu trong nửa thế kỷ qua).
- **Sai số tuyệt đối trung bình (MAE):** **0.0886°C**.
- **Căn bậc hai sai số toàn phương trung bình (RMSE):** **0.1042°C**.
- **Tốc độ nóng lên (Slope):** **+0.0202°C / năm**, tương đương **+0.202°C / thập kỷ**.

### 4.2. Hiện tượng Gia tốc Nóng lên (Warming Acceleration)
Khi thực hiện kiểm định ngoài mẫu (Out-of-sample test) theo đúng phương pháp luận chuỗi thời gian:
- Huấn luyện trên tập Train (1970–2014): tốc độ tăng là **+0.173°C / thập kỷ**.
- Khi áp dụng mô hình này dự báo cho tập Test (2015–2025): toàn bộ các điểm quan sát thực tế (đặc biệt là 2023–2024) đều nằm **cao hơn đáng kể** so với đường hồi quy dự báo ($\text{RMSE}_{\text{test}} = 0.202^\circ\text{C}$).
- Điều này chứng minh tốc độ biến đổi khí hậu không còn duy trì ở mức tuyến tính cố định mà đang có hiện tượng **tăng tốc (acceleration)** trong thập kỷ gần nhất do các vòng phản hồi khí hậu tích cực (positive climate feedbacks).

### 4.3. Dự báo Xu hướng đến năm 2050
- Nếu xu hướng tuyến tính hiện tại tiếp diễn, đến năm **2050**, độ lệch nhiệt độ toàn cầu dự báo sẽ đạt **+1.54°C** so với thời kỳ 1951–1980 (dải tin cậy 95%: **[+1.33°C, +1.76°C]**).
- Cần lưu ý: Nếu quy đổi về thời kỳ tiền công nghiệp (1850–1900, cao hơn mốc 1951–1980 khoảng 0.3°C), ngưỡng nhiệt độ toàn cầu sẽ vượt quá **+1.8°C**, vượt xa mục tiêu kiềm chế 1.5°C của Hiệp định Paris.

---

## 5. Lưu ý Chất lượng Dữ liệu & Bàn giao Kỹ thuật

Để đảm bảo bước tích hợp dashboard (`scripts/nguyen_khang/chuan_bi_du_lieu_dashboard.py`) diễn ra hoàn hảo:

1. **Khóa ghép bảng:** Sử dụng cặp khóa `(iso_alpha, year)`. Bảng `nhiet_do_quoc_gia.csv` đã được kiểm tra nghiêm ngặt với **0 dòng trùng lặp**.
2. **Khắc phục triệt để trường hợp Trung Quốc:**
   - Mã `CHN` đại diện chính thức cho thực thể Trung Quốc (bắt nguồn từ mã UN M49 `'156'`, nguyên gốc FAO là *China, mainland*). Tên hiển thị đã được chuẩn hóa thống nhất là `"China"`.
   - Các vùng tổng hợp gây nhiễu của FAO như mã M49 `'159'` (*China aggregate*) đã được bóc tách hoàn toàn vào danh sách 52 vùng tổng hợp riêng (`aggregates_separated` trong file `bao_cao_chat_luong.json`).
   - Các lãnh thổ Hồng Kông (`HKG`), Ma Cao (`MAC`), Đài Loan (`TWN`) được cấp mã ISO-3 độc lập, không bị gộp trùng.
3. **Mã ngoại lệ không có châu lục:**
   - Có 3 mã quốc gia/lãnh thổ có `continent = null` trong bảng gốc do tính chất địa lý đặc thù: `ATA` (Nam Cực), `ATF` (Vùng đất phía Nam thuộc Pháp), `SJM` (Quần đảo Svalbard và Jan Mayen). Khi ghép lên dashboard, Khang có thể gán `ATA` vào `"Antarctica"` và `SJM` vào `"Europe"`.
4. **Giá trị khuyết:** Tỷ lệ khuyết cột `temperature_anomaly` ở bảng quốc gia là **3.48%** (chủ yếu ở các đảo quốc rất nhỏ hoặc năm gần nhất chưa tổng hợp xong). Tuân thủ nguyên tắc: **giữ giá trị null**, không thay thế bằng số 0.
5. **Đầu ra bàn giao đầy đủ tại:**
   - Bảng dữ liệu sạch: `processed/duc/nhiet_do_toan_cau.csv`, `processed/duc/nhiet_do_quoc_gia.csv`
   - Báo cáo chất lượng: `processed/duc/bao_cao_chat_luong.json`
   - Biểu đồ tĩnh: `eda/duc/bieu_do_tinh/*.png` (6 biểu đồ)
   - Biểu đồ tương tác: `eda/duc/bieu_do_tuong_tac/*.html` (Bản đồ 03 và Hồi quy 06)
   - Script tự động: `scripts/duc/lam_sach_du_lieu.py`
