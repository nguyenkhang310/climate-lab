# Insight phần Quân - CO₂, ngành phát thải, năng lượng tái tạo

Nguồn: các CSV trong `data/du_lieu_da_xu_ly/quan/` + biểu đồ tương tác
`bieu_do/tuong_tac/*.html` + EDA tĩnh `bieu_do/tinh/*.png` (cùng thư mục Quân).
Dashboard và biểu đồ tương tác hiện mở lịch sử CO₂ từ 1850 đến 2024. Những nhận
định 1970–2024 bên dưới vẫn nói riêng về giai đoạn đó; EDGAR không có trước 1970.
Đơn vị: OWID `co2` = Mt/năm (không gồm thay đổi sử dụng đất), `co2_per_capita` = tấn/người;
EDGAR `Substance = CO2` = Mt CO₂; `renewable_percent` = % tái tạo trong **tổng tiêu thụ
năng lượng cuối cùng** (không phải % điện tái tạo).

## 0. Big Idea và 3 câu hỏi của story

**Big Idea:** CO₂ toàn cầu tăng ~2,6 lần sau 50 năm và tập trung vào vài nước/ngành,
nên dashboard phải cho xem cả tổng thải lẫn CO₂/người và drill-down theo ngành,
đồng thời ghi rõ giới hạn số liệu (2024 tái tạo sơ bộ, EDGAR chỉ tính CO₂).

Ba câu hỏi dẫn mạch bên dưới: (1) Khí thải đã tăng bao nhiêu? (2) Ai thải và từ
ngành nào? (3) Tái tạo có đi cùng CO₂/người thấp hơn không - và số liệu nào chưa
đủ chắc để kết luận?

**3-minute story:** CO₂ toàn cầu tăng liên tục từ ~14.899 Mt (1970) lên ~38.599 Mt
(2024) mà không đảo chiều. Phát thải tập trung nặng: riêng Trung Quốc gấp ~2,5 lần
Mỹ, top 5 chiếm hơn 60%, và ngành điện một mình chiếm ~40,8% CO₂ năm 2024 - đó là
đầu mối cần nhìn trước. Ở góc đối chiếu, nước có tỷ trọng tái tạo cao thường có
CO₂/người thấp hơn (r ≈ -0,49, n = 212) nhưng điểm phân tán rộng nên không đọc thành
nhân-quả. Hai giới hạn phải nhớ khi dùng dashboard: tái tạo 2024 còn sơ bộ (84/225
nước) và EDGAR ở đây chỉ tính CO₂, không phải tổng khí nhà kính.

## 1. Xu hướng toàn cầu (1970-2024, dòng World trực tiếp)
- CO₂ toàn cầu tăng từ ~14.899 Mt (1970) lên ~38.599 Mt (2024), gấp **~2,6 lần**.
- Đường tăng liên tục, không có điểm đảo chiều bền vững trong giai đoạn này.
- Nhìn chart `01_line_co2_toan_cau`: takeaway một dòng - tăng liên tục, chưa đảo chiều.

## 2. Tập trung phát thải (2023)
- Top 5: Trung Quốc (~12.172 Mt) > Mỹ (~4.918) > Ấn Độ (~3.063) > Nga (~1.733) > Nhật (~987).
- Trung Quốc một mình gấp ~2,5 lần Mỹ; tổng top 5 chiếm hơn 60% toàn cầu.
- Xếp hạng theo tổng CO₂ và theo CO₂/người cho thứ tự khác nhau, dashboard cần cả hai
  chế độ (đã có trong biểu đồ mẫu 02/03).
- Nhìn chart `02_bar_top15`: ai thải nhiều nhất đã rõ.
  Nhìn chart `03_choropleth_co2pc`: xếp hạng theo đầu người đảo lộn so với tổng thải.

## 3. Cơ cấu ngành (EDGAR 2024, toàn cầu)
- Điện năng (Power Industry) **~40,8%** - đầu mối giảm phát thải.
- Giao thông ~18,7% + đốt công nghiệp ~16,0% = ~35% tiếp theo.
- Nông nghiệp (0,4%) + chất thải (0,1%) trong EDGAR chỉ tính CO₂ (không gồm CH₄/N₂O)
  nên tỷ trọng thấp - **không đọc thành "nông nghiệp không đáng kể"** khi nói về KNK tổng.
- Không dùng sheet `GHG_totals_by_country` dưới nhãn CO₂ (đó là CO₂-tương-đương).
- Chart `04_stacked_area_chau_luc` cho thấy diễn biến CO₂ theo châu lục;
  `05_treemap_nganh` cho thấy điện là đầu mối, tiếp theo là giao thông và công nghiệp.

## 4. CO₂/người và năng lượng tái tạo (2023, n = 212, r ≈ -0,49)
- Tương quan âm vừa: quốc gia có tỷ trọng tái tạo cao thường có CO₂/người thấp hơn,
  nhưng phân tán rộng - tái tạo chỉ là một mảnh ghép (cấu trúc kinh tế, khí hậu, mức
   sống đều ảnh hưởng). Trong đúng 212 quốc gia của biểu đồ, trung bình tái tạo 2023
   ~28,8% và trung vị ~20,0% (lệch phải:
   nhiều nước nhỏ dùng sinh khối truyền thống ở mức rất cao).
- Đây là mối liên hệ mô tả, không phải nhân-quả.
- Nhìn chart `06_scatter_co2pc_renewable`: tái tạo cao đi cùng CO₂/người thấp hơn
  nhưng phân tán rộng - mỗi điểm là một quốc gia, đừng đọc đường xu hướng thành
  nguyên nhân.

## 5. Lưu ý chất lượng khi ghép dashboard
- Ghép bằng `iso_alpha + year`; năm 2024 thiếu năng lượng tái tạo (84/225 nước) nên bộ lọc
  mặc định có tái tạo dùng **1990-2023**.
- `ATA` được phân loại Antarctica. EDGAR chuẩn hóa riêng mã `ANT` có tên Curaçao
  thành `CUW`, giữ mã nguồn ở `source_iso_alpha`. `SCG` được giữ là thực thể gộp
  Serbia và Montenegro ở Europe; chỉ tính khi phạm vi có cả hai nước, không gán
  toàn bộ phát thải chung cho từng nước riêng.
- Tỷ trọng ngành tính trên tổng các ngành có số liệu; `sectors_available` và
  `sectors_expected` cho biết nhóm quốc gia–năm còn thiếu giá trị ngành. Tỷ trọng
  cộng lại 100% không đồng nghĩa có đủ dữ liệu tất cả ngành.
- Kosovo không có mã ISO ở cả OWID và tái tạo nên tách riêng, không có trong các CSV.
- Năm 2025 của EDGAR là số sơ bộ, biểu đồ chốt ở 2024.
- Chi tiết đầy đủ: `data/du_lieu_da_xu_ly/quan/bao_cao_chat_luong.json` (từ điển dữ liệu, missing,
  quy tắc outlier, độ phủ theo năm).
- Nhìn chart `05_line_do_phu_du_lieu`: đường cam bắt đầu 1990 theo đúng phạm vi nguồn;
  điểm 2024 chỉ 84/225 nước (sơ bộ) - đoạn cắm đầu không phải sụp đổ mà là thiếu số liệu.

## 6. Kết: 3 takeaway và 3 giới hạn

Takeaway: (1) CO₂ tăng ~2,6 lần và tập trung - top 5 hơn 60%, điện ~40,8%.
(2) Phải xem song song tổng thải và CO₂/người vì hai xếp hạng đảo lộn nhau.
(3) Tái tạo liên quan nghịch vừa với CO₂/người (r ≈ -0,49) nhưng chỉ là một mảnh ghép.

Giới hạn: (1) Tái tạo 2024 sơ bộ (84 nước) - phân tích có tái tạo dùng 1990-2023.
(2) EDGAR trong phần này chỉ tính CO₂, không suy ra kết luận về tổng khí nhà kính.
(3) Mọi tương quan là mô tả, không phải nhân-quả.
