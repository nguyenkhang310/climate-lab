# Thư mục dữ liệu

```text
data/
├── du_lieu_goc/
│   ├── duc/             NASA, FAOSTAT
│   ├── quan/            OWID, EDGAR, dữ liệu năng lượng
│   └── dung_chung/      Mã ISO3 và bảng tra cứu
├── du_lieu_da_xu_ly/
│   ├── duc/             Bảng nhiệt độ đã làm sạch
│   ├── quan/            Bảng CO₂ và năng lượng đã làm sạch
│   └── nguyen_khang/    Bảng ghép và cơ sở dữ liệu SQLite
└── ket_qua_mo_hinh/
    └── nguyen_khang/    Dự đoán, kịch bản và chỉ số đánh giá
```

Dữ liệu gốc chỉ dùng làm đầu vào và không chỉnh sửa thủ công. Dữ liệu đã xử lý được tạo lại bằng các script ghi trong [README chính](../README.md). Các bảng quốc gia nối bằng khóa `iso_alpha, year`; bảng theo ngành dùng thêm `sector`.

Châu lục ưu tiên phân loại OWID; các mã còn thiếu được bổ sung từ `du_lieu_goc/dung_chung/un_m49_iso3.csv`. Các bước làm sạch, bảng ghép và SQLite gán riêng `ATA` vào `Antarctica`; không thay đổi số liệu các chỉ tiêu.

Bảng `du_lieu_da_xu_ly/duc/nhiet_do_theo_thang.csv` dùng riêng cho biểu đồ 12 tháng, khóa `iso_alpha, year, month`. Mã `WLD` là chuỗi toàn cầu NASA; các mã quốc gia dùng FAOSTAT. Không ghép bảng tháng vào bảng năm để tránh nhân bản dòng.

`duc/nhiet_do_quoc_gia.csv` giữ năm khí tượng FAOSTAT (tháng 12 năm trước đến tháng 11), phục vụ trang Nhiệt độ. `duc/nhiet_do_quoc_gia_nam_lich.csv` lấy trung bình tháng 1–12 khi đủ 12 giá trị để ghép với CO₂; thiếu tháng giữ null. Cả hai giữ 1961–2025. NASA giữ 1880–2025. Bảng quốc gia ghép mở 1850–2024 phục vụ CO₂, còn Tổng quan chọn 1961–2024. Bảng toàn cầu ghép NASA + CO₂ giữ 1880–2024 cho mô hình. Không gán nhiệt độ toàn cầu cho từng nước hay điền nhiệt độ trước 1961.

EDGAR chuẩn hóa riêng mã nguồn `ANT` có tên `Curaçao` thành `CUW`, lưu mã gốc ở `source_iso_alpha`. `SCG` giữ thành thực thể gộp Serbia và Montenegro, không gán phát thải chung cho từng nước. Số ngành có dữ liệu được lưu để nhận biết tổng và tỷ trọng ngành chưa đầy đủ.
