# Insight phần Quân — CO₂, ngành phát thải, năng lượng tái tạo

Nguồn: các CSV trong `processed/quan/` + biểu đồ tương tác
`eda/quan/bieu_do_tuong_tac/*.html` + EDA tĩnh `eda/quan/bieu_do_tinh/*.png`.
Đơn vị: OWID `co2` = Mt/năm (không gồm thay đổi sử dụng đất), `co2_per_capita` = tấn/người;
EDGAR `Substance = CO2` = Mt CO₂; `renewable_percent` = % tái tạo trong **tổng tiêu thụ
năng lượng cuối cùng** (không phải % điện tái tạo).

## 1. Xu hướng toàn cầu (1970–2024, dòng World trực tiếp)
- CO₂ toàn cầu tăng từ ~14.899 Mt (1970) lên ~38.599 Mt (2024), gấp **~2,6 lần**.
- Đường tăng liên tục, không có điểm đảo chiều bền vững trong giai đoạn này.

## 2. Tập trung phát thải (2023)
- Top 5: Trung Quốc (~12.172 Mt) > Mỹ (~4.918) > Ấn Độ (~3.063) > Nga (~1.733) > Nhật (~987).
- Trung Quốc một mình gấp ~2,5 lần Mỹ; tổng top 5 chiếm hơn 60% toàn cầu.
- Xếp hạng theo tổng CO₂ và theo CO₂/người cho thứ tự khác nhau, dashboard cần cả hai
  chế độ (đã có trong biểu đồ mẫu 02/03).

## 3. Cơ cấu ngành (EDGAR 2024, toàn cầu)
- Điện năng (Power Industry) **~40,8%** — đầu mối giảm phát thải.
- Giao thông ~18,7% + đốt công nghiệp ~16,0% = ~35% tiếp theo.
- Nông nghiệp (0,4%) + chất thải (0,1%) trong EDGAR chỉ tính CO₂ (không gồm CH₄/N₂O)
  nên tỷ trọng thấp — **không đọc thành "nông nghiệp không đáng kể"** khi nói về KNK tổng.
- Không dùng sheet `GHG_totals_by_country` dưới nhãn CO₂ (đó là CO₂-tương-đương).

## 4. CO₂/người và năng lượng tái tạo (2023, n = 212, r ≈ −0,49)
- Tương quan âm vừa: quốc gia có tỷ trọng tái tạo cao thường có CO₂/người thấp hơn,
  nhưng phân tán rộng — tái tạo chỉ là một mảnh ghép (cấu trúc kinh tế, khí hậu, mức
  sống đều ảnh hưởng). Trung bình tái tạo 2023 ~27,3%, trung vị ~18,3% (lệch phải:
  nhiều nước nhỏ dùng sinh khối truyền thống ở mức rất cao).
- Đây là mối liên hệ mô tả, không phải nhân–quả.

## 5. Lưu ý chất lượng khi ghép dashboard
- Ghép bằng `iso_alpha + year`; năm 2024 thiếu năng lượng tái tạo (84/225 nước) nên bộ lọc
  mặc định có tái tạo dùng **1990–2023**.
- `ATA` (OWID) và `SCG` (EDGAR, Serbia and Montenegro lịch sử) có `continent = null`;
  giữ lại để left-join từ danh mục quốc gia rồi quyết định hiển thị.
- Kosovo không có mã ISO ở cả OWID và tái tạo nên tách riêng, không có trong các CSV.
- Năm 2025 của EDGAR là số sơ bộ, biểu đồ chốt ở 2024.
- Chi tiết đầy đủ: `processed/quan/bao_cao_chat_luong.json` (từ điển dữ liệu, missing,
  quy tắc outlier, độ phủ theo năm).
