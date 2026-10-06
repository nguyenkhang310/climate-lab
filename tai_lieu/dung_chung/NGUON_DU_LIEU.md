# Nguồn dữ liệu Climate Lab

Phân công, cây thư mục và lệnh chạy xem [README](../../README.md).

- Dữ liệu gốc: `data/du_lieu_goc/<thanh_vien>`.
- Dữ liệu đã xử lý: `data/du_lieu_da_xu_ly/<thanh_vien>`.
- Kết quả mô hình: `data/ket_qua_mo_hinh/nguyen_khang`.
- Danh mục UN M49, châu lục và từ điển OWID: `data/du_lieu_goc/dung_chung`.
- Mỗi phần có báo cáo JSON ghi đơn vị, tỷ lệ thiếu và chất lượng dữ liệu.

Giữ CSV nguồn và CSV sạch vì chúng phục vụ các bước khác nhau; không sửa dữ liệu gốc.
Hai CSV tra cứu FAOSTAT không dùng đã bỏ khỏi cây dự án: pipeline đối chiếu bằng
`un_m49_iso3.csv`; cờ nguồn vẫn giữ ở cột `source_flag`. Có thể lấy lại hai bảng tra cứu
từ ZIP FAOSTAT bên dưới.

Bản đồ dashboard dùng `world_110m.json` tải từ [Plotly](https://cdn.plot.ly/world_110m.json),
lưu tại `bang_dieu_khien/nguyen_khang/tai_nguyen` để không phụ thuộc mạng khi mở địa cầu.

## Nguồn và mục đích sử dụng

| Tệp                                             | Dùng cho                                                                   | Nguồn chính thức                                           | Link tải                                                                                                                                                                                                                 |
| ------------------------------------------------ | --------------------------------------------------------------------------- | ------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `nasa_nhiet_do_toan_cau_1880_2026.csv`         | Xu hướng và nhiệt độ toàn cầu theo thập kỷ                        | NASA GISS — GISTEMP v4                                       | [Tải CSV](https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.csv) · [Phương pháp](https://data.giss.nasa.gov/gistemp/)                                                                                        |
| `faostat_nhiet_do_quoc_gia_1961_2025.csv`      | Bản đồ, heatmap, boxplot và so sánh quốc gia                          | FAOSTAT Temperature Change on Land, xây dựng từ NASA–GISS | [Tải ZIP](https://bulks-faostat.fao.org/production/Environment_Temperature_change_E_All_Data_%28Normalized%29.zip) · [Trang dữ liệu](https://www.fao.org/faostat/en/#data/ET)                                           |
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

Biểu đồ **Chênh nhiệt độ theo tháng** dùng bảng riêng `duc/nhiet_do_theo_thang.csv`, khóa `(iso_alpha, year, month)`. Toàn cầu (`WLD`) lấy 12 cột `Jan`–`Dec` của NASA; quốc gia lấy `January`–`December` và `Element = Temperature change` của FAOSTAT, giữ cờ `Flag`. Không dùng dòng mùa hoặc suy ra số liệu tháng từ trung bình năm. Giá trị là chênh lệch so với cùng tháng trong giai đoạn **1951–1980**. Bộ lọc châu lục lấy trung bình các nước có số liệu từng tháng–năm, sau đó trung bình các năm trong kỳ; đây không phải trung bình có trọng số diện tích. Không thay số liệu thiếu bằng 0 và không dùng năm 2026.

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
