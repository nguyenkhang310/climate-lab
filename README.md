# Climate Lab — Dashboard khí hậu

Đồ án Thu thập và Xử lý Dữ liệu · HCMUTE · Nhóm 18.
Phân tích nhiệt độ, CO₂ và mô hình dự đoán trên dữ liệu 1970–2024.

## Chạy dashboard

```bash
pip install -r requirements.txt
python app.py
```

Mở http://127.0.0.1:8050. Nếu dùng môi trường ảo: `source .venv/bin/activate` trước.
Dữ liệu sạch và kết quả mô hình đã có sẵn, không cần train mỗi lần mở dashboard.

## Thư mục theo nhiệm vụ → thành viên

Tên thư mục dùng tiếng Việt không dấu để dễ nhập lệnh và import Python.
Notebook, code và nhận định của một người nằm cạnh nhau, không chia riêng theo loại file.

```text
climatelab/
├── app.py                           # Lệnh chạy chung
├── requirements.txt
├── README.md
├── phan_tich_nhiet_do/
│   └── duc/
│       ├── 01_lam_sach_va_eda.ipynb
│       ├── lam_sach_du_lieu.py
│       ├── tao_bieu_do_plotly.py
│       ├── NHAN_DINH.md
│       ├── du_lieu_goc/              # NASA, FAOSTAT
│       ├── du_lieu_sach/             # 2 CSV + báo cáo chất lượng
│       └── bieu_do/                  # tinh/ và tuong_tac/
├── phan_tich_co2/
│   └── quan/
│       ├── lam_sach_du_lieu.py
│       ├── tao_eda.py
│       ├── tao_bieu_do_plotly.py
│       ├── NHAN_DINH.md
│       ├── du_lieu_goc/              # OWID, EDGAR, năng lượng tái tạo
│       ├── du_lieu_sach/             # 4 CSV + báo cáo chất lượng
│       └── bieu_do/                  # tinh/ và tuong_tac/
├── mo_hinh_du_doan/
│   └── nguyen_khang/
│       ├── ghep_du_lieu.py
│       ├── mo_hinh_nhiet_do.py
│       ├── GIAI_THICH.md
│       ├── du_lieu/                  # Bảng quốc gia/năm, chuỗi toàn cầu
│       └── ket_qua/                  # Kiểm định, kịch bản, thông số mô hình
├── bang_dieu_khien/
│   └── nguyen_khang/
│       ├── ung_dung.py               # Bố cục và tương tác Dash
│       ├── bieu_do.py                # Các hàm vẽ Plotly dùng chung
│       ├── du_lieu.py                # Nạp và lọc dữ liệu
│       ├── tai_nguyen/               # CSS, logo, bản đồ nền cục bộ
│       └── kiem_thu/                 # Kiểm tra dữ liệu và trình duyệt
└── tai_lieu/
    └── dung_chung/                   # Barem, nguồn, danh mục quốc gia
```

## Chạy lại xử lý dữ liệu

Chạy từ thư mục `climatelab`, theo thứ tự:

```bash
python phan_tich_nhiet_do/duc/lam_sach_du_lieu.py
python phan_tich_co2/quan/lam_sach_du_lieu.py
python mo_hinh_du_doan/nguyen_khang/ghep_du_lieu.py
python mo_hinh_du_doan/nguyen_khang/mo_hinh_nhiet_do.py
```

Đức dùng notebook để xem các bước làm sạch và EDA; notebook gọi lại hàm làm sạch và vẽ HTML
trong `.py` cùng thư mục, không duy trì hai bản code. Chạy `tao_bieu_do_plotly.py` để xuất lại HTML;
Quân dùng thêm `tao_eda.py` để xuất PNG. Hình EDA và báo cáo không phải file rác.

Giữ các bảng CSV sạch riêng để tái lập bước ghép, không thay dữ liệu thiếu bằng 0.
Chi tiết đơn vị, nguồn tải và quy tắc dữ liệu: [Nguồn dữ liệu](tai_lieu/dung_chung/NGUON_DU_LIEU.md).

## Kiểm thử

```bash
python -m unittest discover -s bang_dieu_khien/nguyen_khang/kiem_thu -v
```

Kiểm tra trình duyệt cần Playwright, Chrome và dashboard đang chạy:

```bash
python bang_dieu_khien/nguyen_khang/kiem_thu/browser_smoke.py
```

Dashboard có 7 mục: Tổng quan, Bản đồ khí hậu, Nhiệt độ, Khí thải CO₂,
Mô hình dự đoán, Nhận định và Dữ liệu. Mô hình dùng hồi quy tuyến tính giữa
CO₂ tích lũy và nhiệt độ trung bình trượt 5 năm, kiểm định theo thời gian.
Kết quả là mô phỏng theo giả định, không phải dự báo khí hậu chính thức.

Bộ lọc áp dụng cho Tổng quan, Bản đồ khí hậu, Nhận định và Dữ liệu. Hai tab EDA giữ phạm vi
ghi trên từng biểu đồ; tab mô hình luôn dùng chuỗi toàn cầu 1970–2024. Nhiệt độ toàn cầu lấy
từ NASA, nhiệt độ quốc gia từ FAOSTAT. Tổng CO₂ dùng OWID/GCP; cơ cấu ngành dùng EDGAR,
không gồm vận tải quốc tế nên không dùng tổng ngành để thay thế tổng OWID.
