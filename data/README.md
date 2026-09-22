# Bộ dữ liệu Climate Lab

**Chủ đề:** Trực quan hóa sự nóng lên toàn cầu — biến đổi nhiệt độ và lượng khí thải CO₂ qua các thập kỷ.

Đây là dữ liệu thô để thành viên phụ trách làm sạch. Không sửa trực tiếp các tệp trong thư mục này; dữ liệu sau xử lý nên được xuất sang thư mục `processed/` cùng với script làm sạch.

## Cấu trúc thư mục

```text
data/
├── README.md / README.pdf          # Tài liệu mô tả nguồn và phân công
└── raw/                            # Dữ liệu gốc, không sửa trực tiếp
    ├── 01_duc_nhiet_do/
    │   ├── nasa_nhiet_do_toan_cau_1880_2026.csv
    │   ├── faostat_nhiet_do_quoc_gia_1961_2025.csv
    │   ├── faostat_ma_quoc_gia_va_khu_vuc.csv
    │   └── faostat_giai_thich_co_du_lieu.csv
    ├── 02_quan_phat_thai_co2/
    │   ├── owid_phat_thai_co2_1750_2024.csv
    │   ├── owid_tu_dien_du_lieu_co2.csv
    │   └── edgar_phat_thai_theo_nganh_1970_2025.xlsx
    ├── 03_quan_nang_luong_tai_tao/
    │   └── un_ty_trong_nang_luong_tai_tao_1990_2024.csv
    └── 04_dung_chung_danh_muc_quoc_gia/
        └── owid_quoc_gia_chau_luc.csv
```

Các sản phẩm đã làm sạch được tách theo người phụ trách:

```text
notebooks/duc/                    # Notebook làm sạch và EDA nhiệt độ
processed/duc/                    # Hai bảng nhiệt độ sạch
processed/quan/                   # CO₂, ngành, năng lượng tái tạo, quality report
processed/nguyen_khang/           # Bảng ghép dashboard và chuỗi toàn cầu
scripts/quan/                     # Pipeline tái lập phần Quân
scripts/nguyen_khang/             # Pipeline ghép dữ liệu dashboard
models/nguyen_khang/              # Mã huấn luyện mô hình
outputs/nguyen_khang/             # Chỉ số đánh giá và ba kịch bản đến 2050
eda/duc/bieu_do_tinh/             # PNG EDA nhiệt độ của Đức
eda/duc/bieu_do_tuong_tac/        # HTML tương tác của Đức
eda/quan/bieu_do_tinh/            # PNG EDA CO₂/năng lượng của Quân
eda/quan/bieu_do_tuong_tac/       # HTML Plotly tương tác của Quân
reports/quan/                     # Insight và diễn giải kết quả của Quân
```

Chạy lại toàn bộ phần đã tích hợp theo thứ tự:

```bash
python scripts/quan/lam_sach_du_lieu.py
python scripts/nguyen_khang/chuan_bi_du_lieu_dashboard.py
python models/nguyen_khang/mo_hinh_nhiet_do.py
python app.py
```

## Phân công thành viên

Đức và Quân phụ trách trọn luồng dữ liệu của mình: **làm sạch → EDA tĩnh → dựng biểu đồ Plotly mẫu → viết insight**. Nguyên Khang nhận các bảng đã kiểm tra để tích hợp dashboard, xây dựng tương tác và mô hình dự báo.

### Đức — Dữ liệu và trực quan hóa nhiệt độ

**Dữ liệu phụ trách**

- Toàn bộ thư mục `01_duc_nhiet_do/`.
- Dùng thêm `04_dung_chung_danh_muc_quoc_gia/owid_quoc_gia_chau_luc.csv` để chuẩn hóa quốc gia và châu lục.

**Công việc làm sạch**

1. Làm sạch chuỗi NASA toàn cầu, giữ dữ liệu năm đầy đủ đến 2025 và tạo cột `decade`.
2. Lọc FAOSTAT còn `Temperature change + Meteorological year`.
3. Đổi mã M49 sang ISO3, gắn châu lục và tách quốc gia khỏi các vùng tổng hợp.
4. Lập báo cáo missing, cờ chất lượng, mã không ghép được và số dòng trước/sau làm sạch.
5. Tạo bảng nhiệt độ quốc gia–năm và bảng nhiệt độ toàn cầu–năm/thập kỷ.

**Trực quan hóa phụ trách**

- Line chart: nhiệt độ toàn cầu qua thời gian.
- Bar chart: nhiệt độ trung bình theo thập kỷ.
- Choropleth map: độ lệch nhiệt độ theo quốc gia và năm.
- Heatmap: nhiệt độ theo châu lục và thập kỷ.
- Boxplot: phân bố nhiệt độ giữa các quốc gia.

**Đầu ra bàn giao**

```text
processed/duc/nhiet_do_toan_cau.csv
processed/duc/nhiet_do_quoc_gia.csv
eda/duc/bieu_do_tinh/            # PNG của tối thiểu 3 biểu đồ tĩnh
eda/duc/bieu_do_tuong_tac/       # Biểu đồ HTML tương tác
```

Hai CSV tối thiểu phải có:

```text
# nhiet_do_toan_cau.csv
year, decade, temperature_anomaly

# nhiet_do_quoc_gia.csv
country, iso_alpha, continent, year, decade, temperature_anomaly, source_flag
```

### Quân — CO₂, ngành phát thải và năng lượng tái tạo

**Dữ liệu phụ trách**

- Toàn bộ `02_quan_phat_thai_co2/`.
- Toàn bộ `03_quan_nang_luong_tai_tao/`.
- Dùng thêm bảng quốc gia–châu lục trong `04_dung_chung_danh_muc_quoc_gia/`.

**Công việc làm sạch**

1. Từ OWID giữ các trường quốc gia, ISO3, năm, CO₂, CO₂/người và dân số; tách các vùng tổng hợp.
2. Chuyển EDGAR từ cột năm sang dòng năm, lọc `Substance = CO2` và loại các dòng tổng hợp/quốc tế.
3. Làm sạch dữ liệu năng lượng tái tạo, chuẩn hóa tên cột và kiểm tra độ phủ theo năm.
4. Gắn châu lục, tạo `decade`, mức tăng CO₂ theo năm và tỷ trọng ngành trong tổng CO₂.
5. Lập báo cáo missing, outlier, mã không ghép được và số dòng trước/sau làm sạch.

**Trực quan hóa phụ trách**

- Line/area chart: phát thải CO₂ toàn cầu qua thời gian.
- Horizontal bar chart: xếp hạng quốc gia phát thải cao nhất.
- Choropleth map: CO₂ tổng hoặc CO₂/người theo quốc gia.
- Stacked area/bar: cơ cấu phát thải theo ngành và thời gian.
- Treemap: tỷ trọng phát thải theo ngành hoặc châu lục.
- Scatter plot: CO₂/người so với tỷ trọng năng lượng tái tạo.

**Đầu ra bàn giao**

```text
processed/quan/co2_quoc_gia.csv
processed/quan/co2_toan_cau.csv
processed/quan/co2_theo_nganh.csv
processed/quan/nang_luong_tai_tao.csv
processed/quan/bao_cao_chat_luong.json
eda/quan/bieu_do_tinh/            # PNG của tối thiểu 3 biểu đồ tĩnh
eda/quan/bieu_do_tuong_tac/       # Biểu đồ HTML tương tác
reports/quan/INSIGHTS.md           # Insight/storytelling
```

Bốn CSV chính có:

```text
# co2_quoc_gia.csv
country, iso_alpha, continent, year, decade, co2, co2_per_capita, population

# co2_toan_cau.csv
year, decade, co2, co2_per_capita, population, cumulative_co2

# co2_theo_nganh.csv
country, iso_alpha, year, sector, co2, sector_share_percent

# nang_luong_tai_tao.csv
country, iso_alpha, year, renewable_percent
```

### Nguyên Khang — Dashboard và mô hình hóa

**Dữ liệu nhận bàn giao**

- Hai bảng nhiệt độ đã làm sạch của Đức; mô hình dùng chuỗi nhiệt độ toàn cầu.
- Bốn bảng của Quân; mô hình dùng bảng toàn cầu với `co2` và `cumulative_co2`, còn dữ liệu quốc gia/ngành dùng cho dashboard và phân tích giải thích.
- Báo cáo chất lượng dữ liệu, danh sách mã không ghép được và các biểu đồ mẫu của hai người.

**Dashboard Dash**

1. Ghép bảng nhiệt độ và CO₂ theo `iso_alpha + year`, kiểm tra trùng khóa và tỷ lệ ghép thành công.
2. Thay toàn bộ dữ liệu mô phỏng trong ứng dụng bằng dữ liệu thật đã làm sạch.
3. Hoàn thiện bộ lọc năm, châu lục, quốc gia và chỉ số; đồng bộ bộ lọc giữa các biểu đồ.
4. Hoàn thiện drill-down từ bản đồ/quốc gia xuống chuỗi thời gian và cơ cấu phát thải theo ngành.
5. Tích hợp tooltip, cross-filtering, nút tải CSV, trạng thái không có dữ liệu và ghi nguồn trên dashboard.
6. Kiểm tra giao diện desktop/mobile, hiệu năng callback và tính nhất quán của đơn vị.

**Mô hình hóa**

1. Ghép nhiệt độ toàn cầu của Đức với CO₂ toàn cầu của Quân theo `year`, dùng giai đoạn chung 1970–2024.
2. Xây mô hình nền `temperature_anomaly ~ year` để có mốc so sánh.
3. Xây mô hình chính `temperature_anomaly ~ cumulative_co2`. CO₂ hằng năm được dùng để tạo các giả định phát thải tương lai rồi cộng dồn thành `cumulative_co2`.
4. Chia train/test theo thời gian, dự kiến train 1970–2014 và test 2015–2024; không xáo trộn ngẫu nhiên chuỗi năm.
5. So sánh các mô hình bằng MAE, RMSE và R² trên cùng tập kiểm tra; chỉ chọn mô hình sau khi xem kết quả ngoài mẫu.
6. Tạo ít nhất ba kịch bản đến năm 2050: phát thải tiếp tục theo xu hướng, giữ ổn định ở mức gần nhất và giảm phát thải theo tỷ lệ người dùng chọn.
7. Với mỗi kịch bản, xuất CO₂ hằng năm giả định, CO₂ tích lũy và nhiệt độ dự báo. Ghi rõ đây là mô phỏng thống kê theo giả định, không phải kịch bản khí hậu chính thức của IPCC.
8. Tích hợp biểu đồ gồm dữ liệu lịch sử, dự đoán trên tập test, các đường kịch bản tương lai, ranh giới dự báo và thông tin đánh giá mô hình.

Mô hình chính trả lời câu hỏi: **nếu quỹ đạo phát thải CO₂ toàn cầu thay đổi theo từng giả định, xu hướng độ lệch nhiệt độ toàn cầu đến năm 2050 khác nhau ra sao?** Không diễn giải hệ số hồi quy như bằng chứng nhân quả tuyệt đối vì cả nhiệt độ và CO₂ đều có xu hướng mạnh theo thời gian.

**Đầu ra bàn giao**

```text
processed/nguyen_khang/dashboard_quoc_gia_nam.csv
processed/nguyen_khang/khi_hau_toan_cau_nam.csv
processed/nguyen_khang/bao_cao_ghep_du_lieu.json
models/nguyen_khang/mo_hinh_nhiet_do.py
outputs/nguyen_khang/so_sanh_mo_hinh.json
outputs/nguyen_khang/du_doan_tap_kiem_tra.csv
outputs/nguyen_khang/kich_ban_nhiet_do_2050.csv
app.py
charts.py
```

Trang **Dự báo** hiển thị dữ liệu lịch sử, dự đoán trên tập kiểm tra, ba kịch bản phát thải, MAE/RMSE/R² và bảng so sánh kết quả năm 2050.

Nguyên Khang chịu trách nhiệm phần **Mô hình dự báo** trong báo cáo: lý do chọn CO₂ tích lũy, cách xây kịch bản, chia dữ liệu theo thời gian, công thức hồi quy, so sánh mô hình, chỉ số đánh giá, giới hạn và cách đọc biểu đồ.

### Bước ghép chung sau khi Đức và Quân hoàn thành

Nguyên Khang ghép bảng của Đức và Quân bằng `iso_alpha + year` theo **full outer join** để giữ mọi mã quốc gia/lãnh thổ có ít nhất một nguồn dữ liệu. Giá trị thiếu tiếp tục là `null`, không được thay bằng 0. Tạo:

```text
processed/nguyen_khang/dashboard_quoc_gia_nam.csv
```

Các cột tối thiểu:

```text
country, iso_alpha, continent, year, decade,
temperature_anomaly, co2, co2_per_capita,
population, renewable_percent
```

 Ba người cùng kiểm tra số dòng, trùng khóa, tỷ lệ ghép thành công và missing sau join. Đức xác nhận nhiệt độ và mốc tham chiếu; Quân xác nhận CO₂, đơn vị và phạm vi phát thải; Nguyên Khang xác nhận logic ghép, mô hình và cách hiển thị. Chỉ đưa vào dashboard chính thức sau khi cả ba xác nhận.

## Nguồn và mục đích sử dụng

| Tệp                                             | Dùng cho                                                                   | Nguồn chính thức                                           | Link tải                                                                                                                                                                                                                 |
| ------------------------------------------------ | --------------------------------------------------------------------------- | ------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `nasa_nhiet_do_toan_cau_1880_2026.csv`         | Xu hướng và nhiệt độ toàn cầu theo thập kỷ                        | NASA GISS — GISTEMP v4                                       | [Tải CSV](https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.csv) · [Phương pháp](https://data.giss.nasa.gov/gistemp/)                                                                                        |
| `faostat_nhiet_do_quoc_gia_1961_2025.csv`      | Bản đồ, heatmap, boxplot và so sánh quốc gia                          | FAOSTAT Temperature Change on Land, xây dựng từ NASA–GISS | [Tải ZIP](https://bulks-faostat.fao.org/production/Environment_Temperature_change_E_All_Data_%28Normalized%29.zip) · [Trang dữ liệu](https://www.fao.org/faostat/en/#data/ET)                                           |
| `faostat_ma_quoc_gia_va_khu_vuc.csv`           | Đối chiếu mã M49 và tên quốc gia/khu vực                            | FAOSTAT                                                       | Nằm trong cùng ZIP FAOSTAT phía trên                                                                                                                                                                                  |
| `faostat_giai_thich_co_du_lieu.csv`            | Giải thích cờ chất lượng và lý do thiếu dữ liệu                  | FAOSTAT                                                       | Nằm trong cùng ZIP FAOSTAT phía trên                                                                                                                                                                                  |
| `owid_phat_thai_co2_1750_2024.csv`             | CO₂ tổng, CO₂/người, dân số, xếp hạng và bản đồ                | Our World in Data; CO₂ chính lấy từ Global Carbon Project | [Tải CSV](https://raw.githubusercontent.com/owid/co2-data/master/owid-co2-data.csv) · [Mô tả nguồn](https://github.com/owid/co2-data)                                                                                  |
| `owid_tu_dien_du_lieu_co2.csv`                 | Ý nghĩa, đơn vị và nguồn của từng cột CO₂                        | Our World in Data                                             | [Tải codebook](https://raw.githubusercontent.com/owid/co2-data/master/owid-co2-codebook.csv)                                                                                                                              |
| `edgar_phat_thai_theo_nganh_1970_2025.xlsx`    | Drill-down theo ngành: điện, công nghiệp, giao thông, nông nghiệp… | European Commission Joint Research Centre — EDGAR 2026       | [Trang báo cáo và tải Excel](https://edgar.jrc.ec.europa.eu/report_2026)                                                                                                                                               |
| `un_ty_trong_nang_luong_tai_tao_1990_2024.csv` | Chỉ số bổ sung về tỷ trọng năng lượng tái tạo                    | UN Statistics Division, IEA và IRENA; OWID phân phối lại  | [Tải CSV](https://ourworldindata.org/grapher/share-of-final-energy-consumption-from-renewable-sources.csv) · [Định nghĩa](https://ourworldindata.org/grapher/share-of-final-energy-consumption-from-renewable-sources) |
| `owid_quoc_gia_chau_luc.csv`                   | Gắn quốc gia vào châu lục cho bộ lọc dashboard                       | Our World in Data                                             | [Tải CSV](https://ourworldindata.org/grapher/continents-according-to-our-world-in-data.csv) · [Trang nguồn](https://ourworldindata.org/grapher/continents-according-to-our-world-in-data)                                |

## Cách dùng cho dashboard

### 1. Nhiệt độ toàn cầu

Đọc `nasa_nhiet_do_toan_cau_1880_2026.csv` với dòng thứ hai làm header. Giá trị `***` là thiếu dữ liệu. Dùng cột `J-D` cho nhiệt độ trung bình năm; đơn vị là °C lệch so với trung bình **1951–1980**. Năm 2026 chưa đủ 12 tháng nên không dùng khi so sánh năm hoặc thập kỷ hoàn chỉnh.

### 2. Nhiệt độ theo quốc gia

Trong tệp FAOSTAT, lọc:

- `Element = Temperature change`
- `Months = Meteorological year`

Giữ các cột `Area`, `Area Code (M49)`, `Year`, `Value`, `Unit`, `Flag`. `Value` là độ lệch nhiệt độ trên đất liền so với **1951–1980**. Không trộn các dòng `Standard Deviation`, tháng và mùa vào chuỗi nhiệt độ năm.

### 3. Phát thải CO₂

Trong tệp OWID, ưu tiên các cột:

```text
country, iso_code, year, co2, co2_per_capita, population
```

- `co2`: triệu tấn CO₂ mỗi năm, không gồm thay đổi sử dụng đất.
- `co2_per_capita`: tấn CO₂/người.
- Chỉ giữ quốc gia/lãnh thổ có `iso_code` phù hợp; tách `World`, châu lục và nhóm thu nhập để không cộng trùng.
- `temperature_change_from_co2` là đóng góp của phát thải vào nhiệt độ toàn cầu, không phải nhiệt độ quan sát tại quốc gia.

### 4. Phát thải theo ngành

Trong workbook EDGAR, dùng sheet `GHG_by_sector_and_country`. Nếu dashboard ghi **CO₂**, lọc `Substance = CO2` trước khi tổng hợp theo `EDGAR Country Code + Country + Sector + Year`.

Không dùng trực tiếp sheet `GHG_totals_by_country` dưới nhãn CO₂ vì sheet này là tổng khí nhà kính quy đổi sang **CO₂ tương đương**. Các dòng `GLOBAL TOTAL`, `EU27`, `International Aviation` và `International Shipping` phải được tách khỏi danh sách quốc gia.

### 5. Năng lượng tái tạo

Chỉ số này là tỷ lệ năng lượng tái tạo trong **tổng tiêu thụ năng lượng cuối cùng**, đơn vị %. Đây không phải tỷ lệ điện tái tạo. Năm 2023 có độ phủ quốc gia tốt hơn năm 2024 trong bản hiện tại.

## Quy tắc làm sạch bắt buộc

1. Chuẩn hóa khóa ghép cuối cùng thành `iso_alpha + year`; dùng bảng M49 để đổi mã FAOSTAT sang ISO3.
2. Giữ giá trị thiếu là `null`; không thay bằng 0. Giữ cột `Flag` hoặc tạo cột ghi rõ dữ liệu được nội suy.
3. Giữ riêng các bảng nguồn để chứng minh bước join/merge theo barem. Không inner join tất cả bảng vì sẽ làm mất quốc gia có một chỉ số bị thiếu.
4. Không coi quốc gia phát thải cao là outlier cần xóa. Chỉ xử lý giá trị bất thường khi đã kiểm tra cờ và tài liệu nguồn.
5. Phân tích chính nên dùng giai đoạn **1970–2024**. Nếu bắt buộc có năng lượng tái tạo, kiểm tra độ phủ trong giai đoạn **1990–2023**.
6. Khi tổng hợp theo thập kỷ: nhiệt độ dùng trung bình các năm; CO₂ phải ghi rõ là trung bình phát thải năm hay tổng phát thải cả thập kỷ. Giai đoạn 2020–2024 là giai đoạn chưa đủ 10 năm.
7. Chuỗi toàn cầu dùng trực tiếp NASA cho nhiệt độ và dòng `World` của nguồn CO₂ đã chọn. Không lấy trung bình nhiệt độ các quốc gia theo dân số để gọi là nhiệt độ toàn cầu.

## Bảng đầu ra đề xuất

Sau khi làm sạch, tạo bảng chính cho dashboard:

```text
country, iso_alpha, continent, year,
temperature_anomaly, co2, co2_per_capita,
population, renewable_percent
```

Giữ thêm một bảng riêng cho `sector + substance + country + year` của EDGAR để làm drill-down. Mỗi bảng đầu ra cần có data dictionary, số dòng trước/sau làm sạch, tỷ lệ thiếu theo cột và danh sách mã quốc gia không ghép được.

## Lưu ý về độ phủ

Các nguồn trên có phạm vi toàn cầu nhưng không đảm bảo mọi quốc gia đều có đủ mọi chỉ số trong mọi năm. Ví dụ, OWID thiếu CO₂ năm 2024 cho một số quốc gia rất nhỏ; FAOSTAT có một số quốc gia thiếu nhiệt độ ở năm gần nhất. Báo cáo cần công khai tỷ lệ thiếu và không tự tạo số liệu để lấp toàn bộ bản đồ.
