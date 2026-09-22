# Climate Lab — Trực quan hóa nóng lên toàn cầu

Dashboard Dash phân tích **biến đổi nhiệt độ** và **phát thải CO₂** theo thời gian, khu vực và
quốc gia (1970–2024), kèm mô hình mô phỏng nhiệt độ toàn cầu đến 2050 theo 3 giả định phát thải.
Đồ án môn Thu thập và Xử lý Dữ liệu — HCMUTE, Nhóm 18 (Team Shipcode).

## Chạy nhanh

```bash
pip install -r requirements.txt

# 1. Làm sạch (Đức/Quân) → 2. Ghép bảng (Khang) → 3. Mô hình → 4. Dashboard
python scripts/duc/lam_sach_du_lieu.py
python scripts/quan/lam_sach_du_lieu.py
python scripts/nguyen_khang/chuan_bi_du_lieu_dashboard.py
python models/nguyen_khang/mo_hinh_nhiet_do.py
python app.py                 # mở http://127.0.0.1:8050

# Kiểm thử tích hợp
python -m unittest tests.test_pipeline -v
```

Dữ liệu thô (~81MB) được lưu trong `data/raw/`; nguồn tải và mô tả từng bộ dữ liệu
nằm trong [`data/README.md`](data/README.md). File `processed/` + `outputs/` đã có
sẵn nên có thể chạy `python app.py` ngay sau khi cài requirements.

## Phân công & sở hữu file

| Thành viên | Phụ trách | File sở hữu (không sửa chéo) |
|---|---|---|
| **Đức** | Nhiệt độ: làm sạch NASA + FAOSTAT → EDA tĩnh → biểu đồ mẫu | `data/raw/01_duc_nhiet_do/`, `notebooks/duc/`, `processed/duc/`, `eda/duc/` |
| **Quân** | CO₂ / ngành EDGAR / năng lượng tái tạo: làm sạch → EDA tĩnh → biểu đồ Plotly mẫu + insight | `data/raw/02_quan_phat_thai_co2/`, `data/raw/03_quan_nang_luong_tai_tao/`, `scripts/quan/`, `processed/quan/`, `eda/quan/`, `reports/quan/` |
| **Nguyên Khang** | Ghép bảng dashboard, dashboard Dash, mô hình dự báo | `scripts/nguyen_khang/`, `processed/nguyen_khang/`, `models/nguyen_khang/`, `outputs/nguyen_khang/`, `app.py`, `charts.py`, `climate_data.py` |
| Dùng chung | Danh mục quốc gia–châu lục, tài liệu, kiểm thử | `data/raw/04_dung_chung_danh_muc_quoc_gia/`, `data/README.md`, `docs/`, `tests/`, `assets/` |

Chi tiết luồng làm sạch và quy tắc join (`iso_alpha + year`, full outer join, giữ `null`)
xem [`data/README.md`](data/README.md). Insight phần Quân:
[`reports/quan/INSIGHTS.md`](reports/quan/INSIGHTS.md).

## Cấu trúc

```text
app.py / charts.py / climate_data.py    # Dashboard (Khang): entry + biểu đồ + nạp dữ liệu
assets/                                 # Logo và CSS dùng chung của dashboard
data/                                   # README + raw/ chứa dữ liệu gốc được theo dõi
docs/                                   # Barem và tài liệu dùng chung
notebooks/duc/                          # Notebook làm sạch + EDA nhiệt độ (Đức)
scripts/quan/                           # Pipeline làm sạch + EDA + Plotly (Quân)
scripts/nguyen_khang/                   # Pipeline ghép bảng dashboard (Khang)
processed/{duc,quan,nguyen_khang}/      # Bảng sạch theo chủ sở hữu
eda/{duc,quan}/bieu_do_tinh/            # Biểu đồ PNG theo chủ sở hữu
eda/{duc,quan}/bieu_do_tuong_tac/       # Biểu đồ HTML tương tác theo chủ sở hữu
reports/{duc,quan}/                     # Insight và diễn giải kết quả theo thành viên
models/nguyen_khang/                    # Mô hình hồi quy
outputs/nguyen_khang/                   # Chỉ số đánh giá + dự báo đến 2050
tests/                                  # Unit test + browser smoke test
```

## Dashboard (10 trang)

Tổng quan · Bản đồ khí hậu · Nhiệt độ · Khí thải CO₂ · So sánh quốc gia ·
Tương quan dữ liệu · Dự báo · Nhận định · Dữ liệu (bảng + tải CSV) · Cài đặt.

Trang **Nhiệt độ** chỉ hiển thị EDA của Đức; trang **Khí thải CO₂** chỉ hiển thị EDA
của Quân. Mỗi trang chia rõ **Biểu đồ tĩnh** và **Biểu đồ tương tác Plotly** để dùng khi
báo cáo. Trang **Dự báo** chỉ giữ thêm hai biểu đồ hồi quy tham khảo của Đức, tách biệt
với mô hình chính của Nguyên Khang. Bản đồ khí hậu đọc trực tiếp bảng hợp nhất từ dữ liệu
đã làm sạch của Đức và Quân, giữ nguyên giá trị thiếu thay vì tự điền số.

## Mô hình (trang Dự báo)

- Ghép nhiệt độ toàn cầu (Đức) với CO₂ toàn cầu (Quân) theo `year`, giai đoạn 1970–2024.
- Mô hình nền `nhiệt độ ~ year` vs mô hình chính `nhiệt độ ~ cumulative_co2`
  (OLS một biến, train 1970–2014, test 2015–2024, chọn bằng RMSE test).
- 3 kịch bản đến 2050: tiếp tục xu hướng · giữ ổn định · giảm 3%/năm.
  Đây là **mô phỏng thống kê theo giả định**, không phải kịch bản IPCC;
  hệ số hồi quy không diễn giải như nhân quả tuyệt đối.

## Nguồn dữ liệu chính

NASA GISTEMP · FAOSTAT · OWID/Global Carbon Project · EDGAR · UN/IEA/IRENA —
link tải và từ điển dữ liệu đầy đủ trong [`data/README.md`](data/README.md).
