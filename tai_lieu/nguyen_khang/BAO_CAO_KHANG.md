# CLIMATE LAB — NỘI DUNG BÁO CÁO PHẦN KHANG

**Đồ án môn Tương tác dữ liệu trực quan — Nhóm 18**  
**Nội dung:** Tích hợp dữ liệu, thiết kế dashboard và mô hình dự đoán.  
**Phiên bản đối chiếu:** mã nguồn tại commit `1ee9746` và các tệp dữ liệu đi kèm; kiểm tra ngày 06/10/2026.

Các số liệu trong tài liệu được tính từ bộ dữ liệu lưu trong dự án, không thay bằng dữ liệu mới tải từ Internet. Dấu chấm được dùng để phân cách hàng nghìn và dấu phẩy biểu thị phần thập phân trong phần trình bày; tên cột, SQL và mã nguồn giữ nguyên quy ước của chương trình.

## 1.3. Đối tượng và phạm vi nghiên cứu (Khang)

### 1.3.1. Đối tượng nghiên cứu

Đề tài nghiên cứu sự thay đổi của các chỉ tiêu khí hậu và lượng CO₂ theo thời gian, đồng thời xây dựng một dashboard để quan sát sự khác biệt giữa các quốc gia, khu vực và phạm vi toàn cầu. Các nhóm chỉ tiêu được sử dụng gồm chênh lệch nhiệt độ, lượng CO₂ hằng năm, CO₂ bình quân đầu người, CO₂ theo ngành và tỷ trọng năng lượng tái tạo.

Chỉ tiêu nhiệt độ được sử dụng là **chênh lệch so với mức trung bình của thời kỳ cơ sở 1951–1980**, đơn vị °C. Chẳng hạn, giá trị `+1,29 °C` thể hiện mức cao hơn thời kỳ cơ sở 1,29 °C, không phải nhiệt độ tuyệt đối bằng 1,29 °C. Giá trị âm thể hiện mức thấp hơn thời kỳ cơ sở, không đồng nghĩa nhiệt độ thực tế dưới 0 °C. Chuỗi toàn cầu của NASA GISTEMP kết hợp thông tin trên đất liền và đại dương; chuỗi quốc gia trong FAOSTAT phản ánh thay đổi nhiệt độ trên đất liền. Vì vậy, hai chuỗi được sử dụng ở những cấp phân tích khác nhau. [NASA GISTEMP](https://data.giss.nasa.gov/gistemp/)

Về lượng CO₂, đề tài phân biệt ba đại lượng:

- **CO₂ hằng năm:** lượng CO₂ trong một năm, lưu bằng triệu tấn, còn gọi là Mt CO₂.
- **CO₂ bình quân đầu người:** lượng CO₂ chia theo dân số, đơn vị tấn/người.
- **CO₂ tích lũy:** tổng lượng CO₂ cộng dồn trong lịch sử của chuỗi nguồn, lưu bằng triệu tấn và được đổi sang tỷ tấn khi đưa vào mô hình.

CO₂ tích lũy không phải nồng độ CO₂ trong khí quyển; dự án không sử dụng đơn vị ppm cho biến này. Dân số được dùng làm thông tin bổ sung và phục vụ tính chỉ tiêu bình quân đầu người, không phải biến đầu vào của mô hình dự đoán nhiệt độ.

### 1.3.2. Phạm vi không gian và đơn vị quan sát

Dữ liệu được tổ chức ở ba cấp: quốc gia hoặc vùng lãnh thổ, châu lục và toàn cầu. Bảng ghép dùng cho dashboard có **244 mã quốc gia/vùng lãnh thổ**. Con số này biểu thị các mã xuất hiện trong bảng ghép, không có nghĩa cả 244 đối tượng đều có đầy đủ mọi chỉ tiêu ở mọi năm.

Đơn vị quan sát của bảng chính là **một quốc gia hoặc vùng lãnh thổ trong một năm**, xác định bằng cặp khóa `(iso_alpha, year)`. Bảng CO₂ theo ngành sử dụng thêm `sector`; bảng nhiệt độ theo tháng sử dụng thêm `month`. Các cấp chi tiết được giữ riêng để tránh làm lặp dữ liệu khi kết nối bảng.

Khi lựa chọn phạm vi toàn cầu, hệ thống dùng trực tiếp chuỗi NASA cho nhiệt độ và dòng `World` của OWID cho CO₂. Khi lựa chọn một quốc gia, hệ thống sử dụng số liệu của quốc gia đó. Khi lựa chọn một châu lục, các chỉ tiêu được tổng hợp từ các quốc gia có dữ liệu trong phạm vi đang chọn, theo quy tắc riêng cho từng đại lượng.

### 1.3.3. Phạm vi thời gian

Phạm vi năm của từng nguồn không hoàn toàn giống nhau. Đề tài giữ dữ liệu sạch theo phạm vi nguồn, nhưng chọn **1970–2024** làm giai đoạn phân tích chung trên dashboard.

| Nhóm dữ liệu sạch | Phạm vi trong dự án | Cách sử dụng |
| --- | --- | --- |
| Nhiệt độ toàn cầu NASA | 1880–2025 | EDA toàn bộ chuỗi; dashboard chung lấy 1970–2024 |
| Nhiệt độ quốc gia FAOSTAT | 1961–2025 | So sánh quốc gia; dashboard chung lấy 1970–2024 |
| Nhiệt độ theo tháng | NASA 1880–2025, FAOSTAT 1961–2025 | Phân tích chênh nhiệt độ của 12 tháng; lọc theo phạm vi đang xem |
| CO₂ toàn cầu và quốc gia OWID | 1750–2024 | Dashboard và mô hình lấy giai đoạn chung 1970–2024 |
| CO₂ theo ngành EDGAR | 1970–2025 | Dashboard sử dụng đến năm 2024 |
| Năng lượng tái tạo | 1990–2024 | Chỉ phân tích các quan sát có dữ liệu; kiểm tra độ phủ từng năm |
| Mẫu dùng để xây dựng hồi quy | 1974–2024 | 51 quan sát sau khi tính trung bình trượt 5 năm |
| Kết quả kịch bản | 2025–2050 | Mô phỏng theo giả định về tốc độ thay đổi CO₂ hằng năm |

Mốc 2024 được chọn để thống nhất chuỗi phân tích chung, không phải vì tất cả nguồn đều kết thúc ở năm này. Dữ liệu nhiệt độ năm 2026 trong tệp gốc không được dùng do năm chưa hoàn chỉnh. Các HTML phân tích độc lập có thể sử dụng khoảng năm dài hơn dashboard, theo cấu hình của script xuất biểu đồ.

### 1.3.4. Phạm vi phương pháp và giới hạn nghiên cứu

Đề tài tập trung vào tiền xử lý dữ liệu, kết nối bảng, phân tích mô tả, trực quan hóa và hồi quy tuyến tính đơn biến. Mô hình sử dụng CO₂ tích lũy toàn cầu để ước tính chênh lệch nhiệt độ trung bình trượt 5 năm.

Nghiên cứu không xây dựng mô hình khí hậu vật lý, không dự báo thời tiết hằng ngày và không dự đoán nhiệt độ tuyệt đối tại một địa điểm cụ thể. Các kịch bản đến năm 2050 phục vụ so sánh kết quả dưới những giả định khác nhau, không được xem là dự báo khí hậu chính thức.

Đối với nguồn OWID, trường `co2` được sử dụng không bao gồm CO₂ do thay đổi sử dụng đất. Dữ liệu EDGAR được lọc riêng `Substance = CO2`, không trộn tổng khí nhà kính quy đổi CO₂ tương đương vào chỉ tiêu CO₂. Tỷ trọng năng lượng tái tạo là tỷ lệ trong **tổng tiêu thụ năng lượng cuối cùng**, không phải riêng tỷ lệ điện tái tạo. [Nguồn CO₂ OWID](https://github.com/owid/co2-data), [định nghĩa chỉ tiêu năng lượng tái tạo](https://ourworldindata.org/grapher/share-of-final-energy-consumption-from-renewable-sources)

## 2.1. Quy trình xử lý dữ liệu (Khang)

### 2.1.1. Tổ chức quy trình

Quy trình xử lý được chia theo nguồn và nhiệm vụ. Đức phụ trách dữ liệu nhiệt độ; Quân phụ trách dữ liệu CO₂ và năng lượng; Khang thực hiện ghép dữ liệu, tổ chức cơ sở dữ liệu, xây dựng mô hình và tích hợp dashboard. Các bước xử lý có tệp đầu vào, đầu ra riêng để thuận tiện kiểm tra và tái tạo kết quả.

```text
Dữ liệu gốc và bảng tra cứu mã quốc gia
                  ↓
Làm sạch riêng nhiệt độ, CO₂, ngành và năng lượng
                  ↓
Chuẩn hóa tên cột, mã quốc gia, năm và đơn vị
                  ↓
        ┌─────────┴───────────┐
        ↓                     ↓
Ghép quốc gia–năm       Ghép chuỗi toàn cầu
        ↓                     ↓
Kiểm tra khóa,         Kiểm tra chuỗi năm,
giá trị thiếu          tạo biến cho hồi quy
        ↓                     ↓
CSV và SQLite         Đánh giá và tạo kịch bản
        └─────────┬───────────┘
                  ↓
      Dashboard, biểu đồ và xuất CSV
```

SQLite là một đầu ra phục vụ trình bày quan hệ giữa các bảng và kiểm chứng kết quả JOIN. **Dashboard hiện đọc các CSV đã xử lý, không truy vấn SQLite trực tiếp khi người dùng thay đổi bộ lọc.** Cả hai dạng lưu trữ được tạo từ cùng các bảng sạch và được đối chiếu bằng kiểm thử.

### 2.1.2. Tiếp nhận và phân loại dữ liệu

Dự án tách dữ liệu thành ba nhóm thư mục:

| Nhóm | Thư mục | Vai trò |
| --- | --- | --- |
| Dữ liệu gốc | `data/du_lieu_goc/<thanh_vien>/` | Lưu bản nguồn dùng để tái tạo quá trình xử lý |
| Dữ liệu sạch và bảng ghép | `data/du_lieu_da_xu_ly/<thanh_vien>/` | Lưu bảng chuẩn hóa, báo cáo chất lượng và SQLite |
| Kết quả mô hình | `data/ket_qua_mo_hinh/nguyen_khang/` | Lưu dự đoán kiểm tra, kịch bản và thông số hồi quy |

Các bảng tra cứu dùng chung nằm trong `data/du_lieu_goc/dung_chung/`, gồm bảng chuyển mã UN M49 sang ISO3, danh mục quốc gia–châu lục và từ điển dữ liệu CO₂. Dữ liệu gốc không được chỉnh sửa thủ công để làm thay đổi kết quả phân tích.

### 2.1.3. Chuẩn hóa dữ liệu trước khi ghép

Với NASA, chương trình đọc đúng dòng tiêu đề, nhận diện ký hiệu `***` là giá trị thiếu và lấy cột `J-D` làm chênh lệch nhiệt độ năm. Dữ liệu tháng được lấy từ các cột `Jan` đến `Dec`, không suy ra từ số liệu năm.

Với FAOSTAT, bảng năm chỉ giữ `Element = Temperature change` và `Months = Meteorological year`. Bảng tháng chỉ giữ 12 tháng cụ thể. Cách lọc này tránh trộn số liệu tháng, mùa, năm khí tượng và độ lệch chuẩn vào một chuỗi. Mã M49 được chuẩn hóa rồi ánh xạ sang ISO3; cờ nguồn được giữ ở `source_flag`.

Với OWID, chuỗi `World` được tách riêng khỏi bảng quốc gia. Tên cột `iso_code` được đổi thành `iso_alpha`. Các trường CO₂, CO₂/người và dân số được giữ theo đơn vị của nguồn. Tăng trưởng CO₂ chỉ được tính khi có năm liền trước phù hợp; trường hợp mẫu số bằng 0 hoặc thiếu dữ liệu không được để lại giá trị vô cực.

Với EDGAR, chương trình lọc chất CO₂ và chuyển các cột năm sang dạng bảng dài, mỗi dòng tương ứng với một quốc gia–năm–ngành. Các dòng tổng hợp và vận tải quốc tế được loại khỏi nhóm quốc gia trước khi cộng số liệu, tránh cộng trùng. Đây là quy tắc của pipeline trong dự án, không có nghĩa tổng EDGAR sau lọc phải bằng dòng `World` của OWID.

Với năng lượng tái tạo, tên cột được chuẩn hóa thành `country`, `iso_alpha`, `year`, `renewable_percent`; các dòng vùng tổng hợp được tách khỏi bảng quốc gia. Số liệu thiếu không được tự thay bằng số 0.

### 2.1.4. Tổ chức các bảng sạch

| Tệp dữ liệu | Số dòng | Cấp chi tiết | Khóa kiểm tra |
| --- | ---: | --- | --- |
| `duc/nhiet_do_toan_cau.csv` | 146 | Toàn cầu–năm | `year` |
| `duc/nhiet_do_quoc_gia.csv` | 14.263 | Quốc gia–năm | `iso_alpha, year` |
| `duc/nhiet_do_theo_thang.csv` | 172.908 | Quốc gia/toàn cầu–năm–tháng | `iso_alpha, year, month` |
| `quan/co2_toan_cau.csv` | 275 | Toàn cầu–năm | `year` |
| `quan/co2_quoc_gia.csv` | 42.480 | Quốc gia–năm | `iso_alpha, year` |
| `quan/co2_theo_nganh.csv` | 82.040 | Quốc gia–năm–ngành | `iso_alpha, year, sector` |
| `quan/nang_luong_tai_tao.csv` | 7.673 | Quốc gia–năm | `iso_alpha, year` |

Đường dẫn trong bảng được tính từ `data/du_lieu_da_xu_ly/`. Bảng nhiệt độ tháng gồm mã `WLD` cho chuỗi toàn cầu NASA và các mã quốc gia của FAOSTAT. Bảng này được dùng riêng cho biểu đồ theo tháng, không đưa trực tiếp vào bảng ghép năm hoặc tám bảng của SQLite hiện tại.

### 2.1.5. Ghép, kiểm tra và cung cấp dữ liệu cho hệ thống

Sau khi có các bảng sạch, script `ghep_du_lieu.py` tạo hai đầu ra chính:

1. `dashboard_quoc_gia_nam.csv`: bảng ghép nhiệt độ, CO₂, dân số và năng lượng tái tạo theo quốc gia–năm.
2. `khi_hau_toan_cau_nam.csv`: chuỗi năm toàn cầu phục vụ biểu đồ tổng quan và mô hình dự đoán.

Script `tao_co_so_du_lieu.py` tạo tám bảng và hai view trong SQLite. Script `mo_hinh_nhiet_do.py` đọc chuỗi toàn cầu, chia tập huấn luyện–kiểm tra, tính các chỉ số đánh giá và tạo ba kịch bản mặc định. Dashboard chỉ tải các đầu ra đã chuẩn bị, thay vì làm sạch toàn bộ nguồn hoặc huấn luyện lại mô hình trong mỗi thao tác lọc.

Việc lưu riêng dữ liệu và kết quả cho phép lần lượt kiểm tra các bước: số liệu nguồn, kết quả ghép, giá trị tổng hợp, dữ liệu đưa vào biểu đồ và kết quả mô hình. Khi thay đổi nguồn dữ liệu, các đầu ra liên quan cần được tạo lại theo cùng quy trình.

## 2.4. Ghép dữ liệu theo quốc gia và năm (Khang)

### 2.4.1. Lựa chọn khóa ghép

Tên quốc gia có thể khác nhau giữa các nguồn về ngôn ngữ, cách viết hoặc quy ước đặt tên. Do đó, đề tài sử dụng mã quốc gia `iso_alpha` thay cho tên quốc gia làm khóa kết nối. Mã này được ghép với `year` để xác định thời điểm quan sát.

Ví dụ, cặp `(VNM, 2024)` chỉ một bản ghi của Việt Nam trong năm 2024. Nhiệt độ, CO₂ và năng lượng tái tạo của những năm khác không được ghép vào bản ghi này. Trước khi kết nối, hàm `_assert_unique()` kiểm tra khóa `(iso_alpha, year)` của từng bảng năm. Nếu có khóa trùng, chương trình dừng và báo lỗi, tránh tạo kết quả ghép nhiều–nhiều ngoài dự kiến.

### 2.4.2. Kết nối các bảng quốc gia bằng phép ghép ngoài

Ba bảng tham gia ghép là nhiệt độ quốc gia, CO₂ quốc gia và năng lượng tái tạo. Chương trình ghép nhiệt độ với CO₂ bằng `outer`, sau đó ghép tiếp năng lượng tái tạo cũng bằng `outer` trên cùng cặp khóa.

Về tập khóa, nếu gọi các tập khóa của ba bảng lần lượt là Kₜ, K꜀ và Kᵣ thì tập khóa đầu ra là:

```text
K = Kₜ ∪ K꜀ ∪ Kᵣ
```

Phép ghép ngoài giữ lại một quốc gia–năm nếu khóa đó xuất hiện ở ít nhất một bảng. Các chỉ tiêu không có dữ liệu tương ứng được giữ là giá trị thiếu. Nếu dùng `inner join` cho cả ba bảng, nhiều quan sát nhiệt độ và CO₂ sẽ bị mất chỉ vì không có năng lượng tái tạo cùng năm. Theo định nghĩa của pandas, phép ghép `outer` giữ hợp các khóa của hai bảng. [pandas.DataFrame.merge](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.merge.html)

Sau ghép, tên quốc gia được ưu tiên từ bảng nhiệt độ, nếu thiếu thì lấy từ CO₂, sau đó từ năng lượng tái tạo. Châu lục được lấy từ bảng nhiệt độ và bổ sung bằng bảng CO₂ khi cần. Mã `ATA` được gán là `Antarctica`. Các mã còn chưa ánh xạ được không được tự gán vào một châu lục tùy ý.

Chương trình tính `decade = (year // 10) × 10`, giới hạn năm trong 1970–2024, sắp xếp theo mã quốc gia và năm, rồi kiểm tra lại tính duy nhất của khóa đầu ra.

### 2.4.3. Cấu trúc bảng sau ghép

Bảng `dashboard_quoc_gia_nam.csv` có **13.296 dòng và 11 cột**.

| Cột | Ý nghĩa | Đơn vị hoặc kiểu nội dung |
| --- | --- | --- |
| `country` | Tên quốc gia/vùng lãnh thổ | Văn bản |
| `iso_alpha` | Mã định danh quốc gia | Văn bản, dùng trong khóa ghép |
| `continent` | Châu lục | Văn bản; có thể thiếu |
| `year` | Năm quan sát | Số nguyên |
| `decade` | Năm bắt đầu thập kỷ | Số nguyên |
| `temperature_anomaly` | Chênh nhiệt độ quốc gia so với 1951–1980 | °C |
| `co2` | CO₂ trong năm | Triệu tấn CO₂ |
| `co2_per_capita` | CO₂ bình quân đầu người | Tấn/người |
| `population` | Dân số | Người |
| `renewable_percent` | Tỷ trọng năng lượng tái tạo trong tiêu thụ năng lượng cuối cùng | % |
| `source_flag` | Cờ nguồn của nhiệt độ FAOSTAT | Văn bản; có thể thiếu |

Ví dụ thực tế sau ghép đối với Việt Nam năm 2024:

| Thuộc tính | Giá trị |
| --- | ---: |
| Mã quốc gia | `VNM` |
| Châu lục | `Asia` |
| Chênh nhiệt độ | +1,914 °C |
| CO₂ | 370,931 triệu tấn |
| CO₂/người | 3,673 tấn/người |
| Dân số | 100.987.685 người |
| Năng lượng tái tạo | Thiếu dữ liệu |
| Cờ nhiệt độ | `E` |

Bản ghi này vẫn được giữ dù thiếu năng lượng tái tạo. Tuy nhiên, nó không tham gia biểu đồ phân tán CO₂/người–năng lượng tái tạo của năm 2024 vì biểu đồ đó cần đủ cả hai biến.

### 2.4.4. Ghép chuỗi toàn cầu

Chuỗi nhiệt độ toàn cầu NASA được ghép với bảng CO₂ toàn cầu OWID bằng các cột `year` và `decade`, sử dụng `inner join`, sau đó giới hạn 1970–2024. `decade` là trường suy ra từ năm; việc ghép trên cả hai cột phù hợp với cách triển khai hiện tại.

Khác với bảng quốc gia, mục tiêu ở đây là thu được những năm đồng thời có dữ liệu toàn cầu từ hai nguồn để xây dựng mô hình. Kết quả gồm **55 dòng và 7 cột**: `year`, `decade`, `temperature_anomaly`, `co2`, `co2_per_capita`, `population`, `cumulative_co2`.

Chuỗi CO₂ tích lũy vẫn giữ giá trị cộng dồn lịch sử từ nguồn OWID; không đặt lại bằng 0 ở năm 1970. Khoảng năm được cắt chỉ giới hạn các quan sát dùng trong phân tích, không thay đổi định nghĩa của biến tích lũy.

### 2.4.5. Tổ chức khóa chính và khóa ngoại trong SQLite

Cơ sở dữ liệu `climate_lab.db` tổ chức các bảng danh mục và bảng chỉ tiêu như sau:

| Bảng | Số dòng | Khóa chính | Khóa ngoại |
| --- | ---: | --- | --- |
| `quoc_gia` | 246 | `iso_alpha` | Không có |
| `nam` | 276 | `year` | Không có |
| `nhiet_do_quoc_gia` | 14.263 | `(iso_alpha, year)` | `iso_alpha → quoc_gia`; `year → nam` |
| `co2_quoc_gia` | 42.480 | `(iso_alpha, year)` | `iso_alpha → quoc_gia`; `year → nam` |
| `nang_luong_tai_tao` | 7.673 | `(iso_alpha, year)` | `iso_alpha → quoc_gia`; `year → nam` |
| `co2_theo_nganh` | 82.040 | `(iso_alpha, year, sector)` | `iso_alpha → quoc_gia`; `year → nam` |
| `nhiet_do_toan_cau` | 146 | `year` | `year → nam` |
| `co2_toan_cau` | 275 | `year` | `year → nam` |

Mỗi quốc gia có thể liên kết với không hoặc nhiều dòng trong một bảng chỉ tiêu quốc gia. Mỗi năm có thể liên kết với không hoặc nhiều dòng quốc gia, nhưng có tối đa một dòng trong từng bảng chỉ tiêu toàn cầu. Cột `sector` phân biệt các ngành trong cùng quốc gia–năm; phiên bản hiện tại không có bảng danh mục ngành riêng nên `sector` không được khai báo là khóa ngoại.

Danh mục `quoc_gia` có 246 mã vì được tạo từ toàn bộ các bảng sạch, kể cả bảng ngành và phạm vi ngoài dashboard. Bảng ghép dashboard chỉ có 244 mã trong phạm vi và các nguồn tham gia phép ghép năm. Hai số lượng này phản ánh hai phạm vi khác nhau, không phải lỗi thiếu dòng.

![Sơ đồ quan hệ các bảng dữ liệu Climate Lab](../dung_chung/SO_DO_ERD.svg)

*Hình 2.1. Sơ đồ quan hệ giữa các bảng. Bảng `nam` được biểu diễn ở hai cụm để dễ đọc, nhưng chỉ tồn tại một lần trong SQLite.*

### 2.4.6. Câu lệnh JOIN và kiểm soát cấp chi tiết

View `dashboard_quoc_gia_nam` thực hiện cùng nguyên tắc giữ hợp khóa như phép ghép ngoài trong pandas:

```sql
WITH khoa AS (
    SELECT iso_alpha, year FROM nhiet_do_quoc_gia
    UNION SELECT iso_alpha, year FROM co2_quoc_gia
    UNION SELECT iso_alpha, year FROM nang_luong_tai_tao
)
SELECT q.country, k.iso_alpha, q.continent, k.year, n.decade,
       t.temperature_anomaly, c.co2, c.co2_per_capita, c.population,
       r.renewable_percent, t.source_flag
FROM khoa k
JOIN quoc_gia q USING (iso_alpha)
JOIN nam n USING (year)
LEFT JOIN nhiet_do_quoc_gia t USING (iso_alpha, year)
LEFT JOIN co2_quoc_gia c USING (iso_alpha, year)
LEFT JOIN nang_luong_tai_tao r USING (iso_alpha, year)
WHERE k.year BETWEEN 1970 AND 2024;
```

`UNION` tạo tập khóa không trùng. Hai phép JOIN với bảng danh mục bổ sung tên quốc gia, châu lục và thập kỷ. Các phép `LEFT JOIN` sau đó bổ sung chỉ tiêu mà không loại bỏ khóa chỉ vì một nguồn thiếu dữ liệu.

Bảng ngành và bảng tháng không được ghép trực tiếp vào bảng năm. Nếu một quốc gia có nhiều ngành trong một năm, phép nối trực tiếp sẽ lặp lại nhiệt độ và dân số theo từng ngành. Khi tính tổng sau đó, các đại lượng này có thể bị cộng nhiều lần. Hệ thống vì vậy lọc bảng ngành, bảng tháng riêng theo mã quốc gia và khoảng năm của phạm vi đang chọn.

## 2.5. Kiểm tra chất lượng dữ liệu sau ghép (Khang)

### 2.5.1. Kiểm tra cấu trúc và khóa

Các nội dung kiểm tra gồm số dòng, số cột, phạm vi năm, số mã quốc gia, khóa bị thiếu và khóa trùng. Kết quả của bảng dashboard tại phiên bản báo cáo:

| Nội dung kiểm tra | Kết quả |
| --- | ---: |
| Số dòng | 13.296 |
| Số cột | 11 |
| Số mã quốc gia/vùng lãnh thổ | 244 |
| Số mốc năm | 55 |
| Phạm vi năm | 1970–2024 |
| Dòng trùng `(iso_alpha, year)` | 0 |
| Dòng thiếu `iso_alpha`, `year` hoặc `country` | 0 |

Số dòng không bằng `244 × 55 = 13.420` vì không phải mọi mã đều xuất hiện trong cả 55 năm. Chương trình giữ hợp các khóa có trong nguồn, không tự tạo toàn bộ tích kết hợp giữa danh sách quốc gia và danh sách năm.

### 2.5.2. Kiểm tra giá trị thiếu

Độ phủ theo cột được tính bằng số dòng có giá trị chia cho tổng 13.296 dòng của bảng ghép:

```text
Độ phủ (%) = Số dòng không thiếu giá trị / Tổng số dòng × 100
```

| Chỉ tiêu | Có dữ liệu | Thiếu dữ liệu | Độ phủ |
| --- | ---: | ---: | ---: |
| Chênh nhiệt độ | 11.743 | 1.553 | 88,32% |
| CO₂ hằng năm | 11.531 | 1.765 | 86,73% |
| CO₂/người | 11.448 | 1.848 | 86,10% |
| Dân số | 11.880 | 1.416 | 89,35% |
| Năng lượng tái tạo | 7.673 | 5.623 | 57,71% |
| Châu lục | 13.090 | 206 | 98,45% |

Độ phủ thấp hơn của năng lượng tái tạo có liên quan đến việc chuỗi chỉ bắt đầu từ 1990 và thiếu số liệu ở một số quốc gia–năm. Đây không phải tỷ lệ lỗi do phép ghép. Chỉ có **6.709 dòng** đồng thời đầy đủ cả năm chỉ tiêu số nêu trong bảng; hệ thống không giới hạn toàn bộ dashboard vào số dòng này vì sẽ loại bỏ nhiều quan sát vẫn dùng được cho phân tích nhiệt độ hoặc CO₂ riêng lẻ.

Trong toàn giai đoạn, có 236 mã có ít nhất một giá trị nhiệt độ, 215 mã có CO₂, 213 mã có CO₂/người, 216 mã có dân số và 230 mã có năng lượng tái tạo. Số mã này không đồng nghĩa số quốc gia có dữ liệu ở riêng năm 2024.

### 2.5.3. Kiểm tra độ phủ theo năm và phạm vi

Ở năm 2024, bảng ghép có 244 dòng, trong đó 223 dòng có nhiệt độ, 215 dòng có CO₂, 213 dòng có CO₂/người, 216 dòng có dân số và 84 dòng có năng lượng tái tạo. Năm 2023 có 225 mã có số liệu năng lượng tái tạo, cao hơn đáng kể so với năm 2024.

Nếu cần đồng thời CO₂/người và năng lượng tái tạo, năm 2024 chỉ còn **72 cặp quan sát hợp lệ**. Do đó, số điểm trên biểu đồ phân tán có thể nhỏ hơn số quốc gia trong bộ lọc. Không được diễn giải phần điểm vắng mặt là những quốc gia có năng lượng tái tạo bằng 0%.

Sau khi bổ sung Nam Cực, 206 dòng còn thiếu châu lục thuộc các mã `ATF`, `BLM`, `GUM`, `MAF`, `MNP`, `SJM`. Những dòng này vẫn có trong bảng tổng và có thể được chọn khi phạm vi châu lục là “Tất cả châu lục”, nhưng không thuộc kết quả lọc của một châu lục cụ thể. Đây là giới hạn còn lại của bảng ánh xạ châu lục trong phiên bản hiện tại.

### 2.5.4. Giữ đúng ý nghĩa của số 0, giá trị thiếu và cờ nguồn

Giá trị thiếu được giữ là `NaN` trong pandas, `NULL` trong SQLite và ô trống khi xuất CSV. Trên giao diện bảng, giá trị thiếu hiển thị bằng dấu “—”; trên bản đồ, các bản ghi thiếu chỉ tiêu được tô xám và có thông báo chưa có số liệu khi rê chuột.

Số 0 có sẵn trong nguồn vẫn là một quan sát hợp lệ, không tự chuyển thành thiếu dữ liệu. Với nhiệt độ, số 0 còn có ý nghĩa rõ ràng là bằng mức trung bình thời kỳ cơ sở. Vì vậy, thay mọi giá trị thiếu bằng 0 sẽ làm sai cả phân bố dữ liệu lẫn ý nghĩa bản đồ.

Cột `source_flag` chỉ phản ánh cờ của nguồn nhiệt độ FAOSTAT, không phải cờ chất lượng chung cho CO₂ hoặc năng lượng. Trong bảng ghép hiện tại, 11.743 giá trị nhiệt độ có số liệu mang cờ `E`. Việc giữ cờ nguồn giúp phân biệt số liệu nguồn cung cấp với số liệu được nhóm tự suy đoán hoặc nội suy. Nhóm không tự nội suy những khoảng trống trong bảng ghép. Cờ trống không được dùng riêng để kết luận một giá trị chắc chắn là quan trắc trực tiếp.

### 2.5.5. Đối chiếu CSV, SQLite và dữ liệu dashboard

Chất lượng ghép không chỉ được kiểm tra bằng số dòng. Bảng ghép được tái tính từ các bảng sạch rồi đối chiếu với CSV đang dùng. Các view SQLite được đọc, sắp xếp theo khóa và so sánh giá trị với CSV tương ứng, có xét sự tương đương giữa các cách biểu diễn giá trị thiếu.

Kết quả đối chiếu:

- `dashboard_quoc_gia_nam`: 13.296 dòng, khớp bảng CSV quốc gia–năm.
- `khi_hau_toan_cau_nam`: 55 dòng, khớp chuỗi CSV toàn cầu.
- `PRAGMA integrity_check`: trả về `ok`.
- `PRAGMA foreign_key_check`: không có bản ghi vi phạm.
- Chuỗi toàn cầu 1970–2024 có mỗi năm đúng một quan sát; các biến nhiệt độ, CO₂ và CO₂ tích lũy dùng cho mô hình đều có giá trị hữu hạn.

Bộ kiểm thử của dự án còn đối chiếu số liệu sau lọc, cách tổng hợp CO₂/người, dữ liệu ngành, biểu đồ thành viên và kết quả mô hình. Tại thời điểm kiểm tra phiên bản này, **51/51 kiểm thử tự động đạt**. Kết quả này xác nhận các điều kiện đã được kiểm thử, không thay thế việc đánh giá độ tin cậy của từng nguồn hoặc chứng minh hệ thống không thể phát sinh lỗi trong mọi tình huống.

### 2.5.6. Kết luận về dữ liệu sau ghép

Bảng ghép đáp ứng yêu cầu liên kết nhiều bảng theo quốc gia và năm, giữ được dữ liệu có ở từng nguồn và không tạo khóa trùng. Các giá trị thiếu vẫn được thể hiện rõ để từng biểu đồ chọn đúng tập quan sát cần thiết. Những giới hạn về độ phủ, châu lục chưa ánh xạ và khác biệt phạm vi nguồn được giữ lại trong báo cáo thay vì che khuất bằng cách tự điền giá trị.

## 3.1. Cấu trúc giao diện và các trang chức năng (Khang)

### 3.1.1. Bố cục chung

Dashboard được xây dựng bằng Dash, sử dụng Plotly để thể hiện biểu đồ tương tác. Giao diện gồm thanh tiêu đề, thanh điều hướng bên trái, khu vực bộ lọc và vùng nội dung chính. Thanh điều hướng có thể thu gọn để tăng diện tích quan sát biểu đồ.

Thanh tiêu đề cung cấp nhận diện của đồ án và thao tác tải dữ liệu. Phần đầu nội dung của mỗi trang hiển thị tên trang cùng phạm vi đang xem. Bộ lọc nằm ở vị trí thống nhất để người dùng nhận biết dữ liệu đang được giới hạn theo khoảng năm, châu lục hay quốc gia nào.

Nền giao diện sử dụng tông sáng; chỉ số, biểu đồ và bảng được đặt trong các khối có ranh giới rõ ràng. Các khối biểu đồ có tiêu đề, đơn vị và thông tin nguồn hoặc thời gian khi cần. Nội dung được phân cấp từ số liệu khái quát đến biểu đồ chi tiết, hạn chế yêu cầu người dùng đọc nhiều đoạn văn trước khi hiểu kết quả.

### 3.1.2. Các trang chức năng

| Thứ tự trên thanh điều hướng | Trang | Nội dung và vai trò |
| --- | --- | --- |
| 1 | Tổng quan | Kết hợp chỉ số, bản đồ, xu hướng, xếp hạng, cơ cấu ngành và phần giới thiệu mô hình |
| 2 | Bản đồ khí hậu | Khảo sát phân bố theo quốc gia và xem thông tin của đối tượng được chọn |
| 3 | Nhiệt độ | Sáu biểu đồ tương tác về xu hướng năm, thập kỷ, bản đồ, châu lục, phân bố và tháng |
| 4 | Khí thải CO₂ | Sáu biểu đồ tương tác về tổng CO₂, nhóm quốc gia cao nhất, CO₂/người, ngành và năng lượng tái tạo |
| 5 | Mô hình dự đoán | So sánh kịch bản CO₂, đường nhiệt độ đến 2050 và kết quả kiểm tra mô hình |
| 6 | Nhận định | Ba nhóm nhận định định lượng về nhiệt độ, thay đổi CO₂ và ngành chiếm tỷ trọng cao nhất |
| 7 | Dữ liệu | Xem các bản ghi sau lọc và tải CSV để đối chiếu |

Việc tổ chức theo trang giúp tách ba nhiệm vụ: khám phá dữ liệu lịch sử, kiểm tra số liệu chi tiết và xem mô phỏng tương lai. Mô hình dự đoán có bộ điều khiển riêng vì sử dụng chuỗi toàn cầu và các giả định CO₂, không phải bộ dữ liệu quốc gia sau lọc.

### 3.1.3. Tổ chức mã nguồn giao diện

| Tệp hoặc nhóm tệp | Vai trò |
| --- | --- |
| `app.py` | Điểm khởi chạy ứng dụng |
| `bang_dieu_khien/nguyen_khang/ung_dung.py` | Bố cục trang, các thành phần giao diện và hàm cập nhật khi thao tác |
| `bang_dieu_khien/nguyen_khang/du_lieu.py` | Nạp dữ liệu, lọc và tổng hợp theo phạm vi |
| `bang_dieu_khien/nguyen_khang/bieu_do.py` | Biểu đồ tổng quan, bản đồ khí hậu, biểu đồ mô hình và định dạng chung |
| `phan_tich_nhiet_do/duc/tao_bieu_do_plotly.py` | Hàm tạo sáu biểu đồ phân tích nhiệt độ và xuất HTML |
| `phan_tich_co2/quan/tao_bieu_do_plotly.py` | Hàm tạo sáu biểu đồ phân tích CO₂ và xuất HTML |
| `bang_dieu_khien/nguyen_khang/tai_nguyen/` | CSS, xử lý tương tác bổ sung và dữ liệu hình học bản đồ |

Hai trang phân tích thành viên sử dụng trực tiếp hàm `build_figures()` trong tệp của Đức và Quân. Dashboard truyền bảng đã lọc vào hàm, sau đó điều chỉnh kích thước, chú giải và bố cục để phù hợp vùng hiển thị. Cách tổ chức này dùng chung logic vẽ giữa script xuất HTML và dashboard, đồng thời vẫn giữ phần mã tạo biểu đồ trong thư mục của từng thành viên.

### 3.1.4. Bố cục biểu đồ và khả năng thích ứng màn hình

Trên màn hình đủ rộng, các biểu đồ tương tác của trang Nhiệt độ và CO₂ được xếp thành hai cột, mỗi hàng hai biểu đồ. Kích thước chữ, khoảng trống cho trục và vị trí chú giải được điều chỉnh để người dùng có thể quan sát nhiều nội dung mà không cần cuộn qua các biểu đồ quá lớn.

Khi chiều rộng màn hình không quá 1.000 px, các lưới biểu đồ này chuyển thành một cột. Các bố cục Tổng quan và Bản đồ tiếp tục được điều chỉnh ở màn hình nhỏ hơn. Biểu đồ dùng chế độ đáp ứng theo kích thước khung; nút “Mở rộng” cung cấp không gian lớn hơn khi cần đọc chi tiết.

Các hình EDA tĩnh được đặt trong mục thu gọn riêng, ghi rõ **“không áp dụng bộ lọc”**. Nhờ đó, người xem có thể phân biệt kết quả phân tích toàn bộ dữ liệu với biểu đồ tương tác đang cập nhật theo phạm vi chọn.

## 3.2. Bộ lọc và luồng tương tác (Khang)

### 3.2.1. Bộ lọc dùng chung

Bộ lọc chung gồm khoảng năm, châu lục, quốc gia và chỉ tiêu tô màu bản đồ. Mỗi thành phần có phạm vi tác động cụ thể:

| Điều khiển | Lựa chọn hiện có | Phạm vi tác động |
| --- | --- | --- |
| Khoảng năm | 1970–2024; 1990–2023; 2000–2024; 2015–2024 | Sáu trang dữ liệu lịch sử; không thay đổi mô hình |
| Châu lục | Tất cả hoặc một châu lục trong danh mục | Giới hạn quốc gia và dữ liệu lịch sử |
| Quốc gia | Tất cả hoặc một mã quốc gia/vùng lãnh thổ; có tìm kiếm tên | Lọc chi tiết hoặc chọn đối tượng trên bản đồ |
| Màu bản đồ | Nhiệt độ hoặc Khí thải CO₂ | Chỉ hiện ở Tổng quan và Bản đồ khí hậu |
| Năm đang xem | Từng năm trong khoảng lọc | Thanh trượt riêng của trang Tổng quan |

Bộ lọc khoảng năm hiện dùng bốn khoảng định sẵn, không phải trường nhập tùy ý mọi cặp năm. Thanh “Năm đang xem” của Tổng quan có bước một năm; nó chọn lát cắt để quan sát mà không thay thế toàn bộ khoảng thời gian của các đường xu hướng.

### 3.2.2. Quan hệ giữa châu lục và quốc gia

Danh sách quốc gia được tạo lại theo châu lục và khoảng năm đang chọn. Nếu quốc gia hiện tại vẫn có trong tập hợp lệ, lựa chọn được giữ nguyên. Nếu không còn hợp lệ, hệ thống đưa lựa chọn về “Tất cả quốc gia”.

Ví dụ, khi chuyển từ “Tất cả châu lục” sang “Châu Á”, danh sách quốc gia chỉ còn các đối tượng được ánh xạ vào châu Á và xuất hiện trong giai đoạn đang chọn. Cách xử lý này tránh tình trạng tên quốc gia đang chọn không thuộc phạm vi của các biểu đồ.

Các trường bộ lọc chính không cho xóa thành giá trị rỗng. Trường quốc gia hỗ trợ tìm kiếm tên để giảm thao tác khi danh sách dài. Tuy nhiên, một quốc gia xuất hiện trong danh sách chỉ có nghĩa có bản ghi trong bảng ghép, không bảo đảm mọi biểu đồ đều đủ dữ liệu để hiển thị.

### 3.2.3. Quy tắc lọc và tổng hợp dữ liệu

Hàm `loc_du_lieu()` áp dụng lần lượt điều kiện năm, châu lục và mã quốc gia. Kết quả được truyền vào bước tổng hợp hoặc vào hàm vẽ biểu đồ tương ứng.

Đối với chuỗi theo năm, hàm `tong_hop_du_lieu()` phân biệt ba trường hợp:

1. **Toàn cầu:** lấy trực tiếp chuỗi NASA và dòng `World` OWID trong khoảng năm tương ứng.
2. **Một quốc gia:** sử dụng trực tiếp nhiệt độ, CO₂ và CO₂/người của quốc gia đó.
3. **Nhiều quốc gia trong một khu vực:** lấy trung bình nhiệt độ của các nước có số liệu; cộng CO₂ có số liệu; tính CO₂/người từ các cặp CO₂–dân số hợp lệ.

Với tập quốc gia hợp lệ P ở năm t, chỉ tiêu bình quân đầu người của khu vực được tính như sau:

```text
CO₂/người của khu vực = [Σ CO₂(i,t) × 1.000.000] / Σ Dân số(i,t), với i thuộc P
```

P chỉ gồm những bản ghi có đồng thời CO₂ và dân số, trong đó dân số lớn hơn 0. Hệ số 1.000.000 chuyển triệu tấn thành tấn. Không lấy trung bình cộng trực tiếp CO₂/người của các nước vì cách đó đặt quốc gia ít dân và đông dân vào cùng trọng số.

Trung bình nhiệt độ của châu lục trong dashboard là trung bình các nước có số liệu, không phải trung bình có trọng số diện tích. Khi số nước có dữ liệu thay đổi giữa các năm, thành phần tính trung bình cũng có thể thay đổi. Chỉ tiêu này vì vậy được diễn giải là kết quả tổng hợp trong bộ dữ liệu đang có, không thay thế chuỗi khí hậu khu vực chính thức.

### 3.2.4. Phạm vi tác động trên từng trang

| Trang hoặc thành phần | Cách áp dụng lựa chọn |
| --- | --- |
| Nhiệt độ, CO₂, Nhận định, Dữ liệu | Lọc theo khoảng năm, châu lục và quốc gia |
| Bản đồ ở Tổng quan và Bản đồ khí hậu | Giữ các quốc gia trong phạm vi châu lục để so sánh; quốc gia chọn được đánh dấu |
| Thông tin và đường xu hướng cạnh bản đồ | Chuyển sang quốc gia chọn hoặc phạm vi tổng hợp đang xem |
| Xếp hạng CO₂ tại Tổng quan | Giữ nhóm cao nhất trong phạm vi châu lục; bổ sung quốc gia chọn nếu cần |
| Hình EDA tĩnh | Giữ nguyên hình và phạm vi khi xuất, không cập nhật theo bộ lọc |
| Phần mô hình ở Tổng quan | Luôn là mô hình toàn cầu; không biến thành dự đoán riêng cho nước đang chọn |
| Trang Mô hình dự đoán | Ẩn bộ lọc lịch sử; dùng lựa chọn kịch bản, tốc độ CO₂ và mốc so sánh riêng |

Sự khác nhau giữa lọc dữ liệu và đánh dấu đối tượng trên bản đồ là có chủ đích. Nếu loại tất cả các nước khác khi chọn một quốc gia, người xem sẽ mất bối cảnh địa lý và khó so sánh với các nước xung quanh.

### 3.2.5. Luồng thao tác từ tổng quan đến chi tiết

Một luồng khảo sát dữ liệu quốc gia gồm các bước:

1. Mở Tổng quan và chọn khoảng năm cần phân tích.
2. Chọn châu lục để thu hẹp danh sách quốc gia và phạm vi bản đồ.
3. Chọn một quốc gia qua danh sách hoặc bấm vào vùng quốc gia trên bản đồ.
4. Quan sát ba chỉ số chính, hai đường xu hướng và nhóm so sánh.
5. Chuyển sang Nhiệt độ hoặc CO₂ để xem sáu biểu đồ theo cùng trạng thái lọc chung.
6. Mở rộng biểu đồ cần phân tích chi tiết.
7. Chuyển sang Dữ liệu để kiểm tra các dòng tương ứng và tải CSV.

Ở Tổng quan, khi thay đổi năm trên thanh trượt, bản đồ, các chỉ số tại năm chọn, nhóm xếp hạng và cơ cấu ngành cập nhật theo năm đó. Hai đường xu hướng vẫn giữ toàn bộ khoảng năm đang lọc, có đường đánh dấu năm được chọn. Phần dự đoán toàn cầu không bị thay đổi bởi thanh trượt lịch sử.

Có một trường hợp cần phân biệt: nếu quốc gia được chọn không có bản ghi ở năm đang xem, khối thông tin và đường đánh dấu trên chuỗi thời gian dùng năm cuối có trong chuỗi quốc gia sau lọc, đồng thời ghi năm đó trên khối thông tin. Bản đồ vẫn giữ năm đang chọn. Nếu bản ghi tồn tại nhưng thiếu một chỉ tiêu, chỉ tiêu đó hiển thị “—”, không được tự điền bằng số liệu năm khác. Vì vậy, khi đối chiếu với bản đồ, cần căn cứ vào năm thực tế được ghi trên khối thông tin.

Trang Bản đồ khí hậu không có thanh trượt năm riêng ở phiên bản hiện tại. Trang này sử dụng năm cuối của khoảng lọc để tô bản đồ, đồng thời giữ đường xu hướng của cả khoảng năm. Khối thông tin quốc gia áp dụng cùng quy tắc chọn năm nêu trên.

### 3.2.6. Trạng thái thiếu dữ liệu

Khi không có dữ liệu trong phạm vi chọn, hệ thống hiển thị thông báo thay vì cố tạo một biểu đồ bằng các số 0. Nếu bảng lọc vẫn có dòng nhưng thiếu chỉ tiêu mà biểu đồ cần, khung biểu đồ thể hiện trạng thái chưa có dữ liệu. Đối với biểu đồ cần hai biến, chỉ những dòng có đủ cả hai biến mới được sử dụng.

Việc giữ nguyên giá trị thiếu đặc biệt quan trọng với năng lượng tái tạo, vì độ phủ thay đổi mạnh giữa 2023 và 2024. Một biểu đồ ít điểm hơn sau khi đổi năm có thể phản ánh dữ liệu nguồn thưa hơn, không nhất thiết là lỗi bộ lọc.

## 3.3. Thiết kế bản đồ khí hậu (Khang)

### 3.3.1. Mục đích và dữ liệu hiển thị

Bản đồ khí hậu giúp xác định phân bố không gian của chênh nhiệt độ hoặc tổng lượng CO₂ tại một năm. Quốc gia được gắn với hình học bản đồ bằng mã ISO3. Khi rê chuột, người dùng xem tên quốc gia, năm và giá trị của chỉ tiêu đang chọn.

Hệ thống dùng `Choropleth` của Plotly và tệp hình học `world_110m.json` được lưu trong thư mục tài nguyên. Tệp hình học được nạp từ ứng dụng thay vì tải lại từ một máy chủ bản đồ bên ngoài. Dữ liệu này là ranh giới đã đơn giản hóa để thể hiện ở quy mô thế giới, không phải ảnh vệ tinh hoặc bản đồ địa hình chi tiết. Một số lãnh thổ rất nhỏ có thể khó quan sát ở độ phân giải này.

### 3.3.2. Hai chế độ quan sát

Bản đồ hỗ trợ hai phép chiếu:

- **Địa cầu — Orthographic:** thể hiện một bán cầu tại một thời điểm, có thể kéo để đổi góc quan sát.
- **Bản đồ phẳng — Natural Earth:** thể hiện toàn thế giới trong một mặt phẳng, thuận tiện so sánh các khu vực cách xa nhau.

Hai chế độ sử dụng cùng dữ liệu quốc gia và cùng chỉ tiêu. Chuyển chế độ chỉ thay cách thể hiện không gian, không thay đổi phép tính. Nút đặt lại góc nhìn đưa địa cầu về góc mặc định với kinh độ 105° và vĩ độ 15°; nút này không xóa dữ liệu hay trả tất cả bộ lọc về mặc định.

### 3.3.3. Thang màu và cách đọc

Với nhiệt độ, bản đồ sử dụng thang màu phân kỳ: xanh cho chênh lệch âm, màu sáng quanh 0 và cam–đỏ cho chênh lệch dương. Miền màu cố định từ **−6 đến +6 °C** trên bản đồ khí hậu, giúp cùng một giá trị nhiệt độ được thể hiện nhất quán khi đổi năm.

Với CO₂, bản đồ sử dụng thang xanh nhạt đến xanh đậm, trong đó màu đậm thể hiện tổng CO₂ cao hơn trong lát cắt đang xem. Miền màu bắt đầu từ 0 và lấy cận trên theo giá trị lớn nhất có dữ liệu của lát cắt, tối thiểu là 1 để tránh miền màu suy biến.

Do cận trên CO₂ được tính lại, cùng một sắc xanh ở hai năm hoặc hai phạm vi khác nhau không nhất thiết tương ứng cùng lượng CO₂. Việc so sánh định lượng cần dựa trên thanh màu và giá trị khi rê chuột. Ngược lại, thang màu nhiệt độ của bản đồ khí hậu được giữ cố định qua các năm.

Các vùng thiếu dữ liệu được tô xám, tách biệt với màu biểu diễn giá trị 0. Nền đại dương dùng tông xanh chuyển sắc; nền khung giao diện màu trắng. Màu nền biển chỉ có tác dụng thể hiện không gian, không mã hóa dữ liệu nhiệt độ biển.

### 3.3.4. Chọn quốc gia và giữ ổn định góc nhìn

Quốc gia đang chọn được đánh dấu bằng đường viền vàng, dày hơn viền các nước còn lại. Viền chọn được áp dụng cả khi bản ghi của quốc gia đang thiếu chỉ tiêu, nhằm phân biệt trạng thái lựa chọn với trạng thái có số liệu.

Trong quá trình cập nhật trên cùng trang, chương trình giữ lại góc xoay hiện tại. Khi chuyển sang bản đồ phẳng, trạng thái góc xoay địa cầu được lưu riêng; khi quay lại địa cầu, trạng thái này được dùng để không lấy góc của phép chiếu phẳng làm góc xoay cầu. Phạm vi kinh độ, vĩ độ và tỷ lệ chiếu được đặt rõ ràng; không tự phóng theo ranh giới một quốc gia bằng `fitbounds`.

JavaScript bổ sung phân biệt thao tác kéo với thao tác bấm. Nếu con trỏ di chuyển quá ngưỡng trong lúc giữ chuột trên bản đồ, sự kiện bấm tiếp theo của thao tác kéo được chặn để tránh chọn nhầm nước. Việc bấm chọn một quốc gia không được dùng làm lệnh tự động xoay địa cầu đến quốc gia đó trong cùng phiên quan sát.

### 3.3.5. Cập nhật có chọn lọc và hiệu năng

Các thao tác đổi màu bản đồ, đổi phép chiếu hoặc đặt lại góc nhìn chỉ cần cập nhật biểu đồ bản đồ. Những phần không bị ảnh hưởng, chẳng hạn đường xu hướng bên cạnh, được giữ nguyên. Cách cập nhật này hạn chế việc dựng lại toàn bộ trang và giảm thay đổi bố cục không cần thiết.

Hiệu ứng chuyển tiếp của bản đồ được tắt để tránh chuyển động đột ngột khi đổi dữ liệu. Chức năng phóng bằng con lăn được tắt trong cấu hình chung, giúp thao tác cuộn trang không vô tình làm thay đổi tỷ lệ biểu đồ. Tốc độ thực tế còn phụ thuộc trình duyệt, máy người dùng và môi trường triển khai; thiết kế này nhằm giảm thao tác dư thừa, không đồng nghĩa mọi thao tác có thời gian phản hồi bằng 0.

### 3.3.6. Giới hạn khi diễn giải bản đồ

Bản đồ tô theo giá trị thống kê của quốc gia nên không thể hiện sự khác nhau giữa các địa phương bên trong cùng một nước. Bản đồ CO₂ tại Tổng quan và Bản đồ khí hậu thể hiện **tổng CO₂**, khác với biểu đồ CO₂/người ở trang phân tích CO₂. Một quốc gia có tổng CO₂ lớn không nhất thiết có chỉ tiêu bình quân đầu người lớn nhất.

Nền địa cầu chỉ là hình thức trực quan. Màu sắc trên bản đồ không phải ảnh chụp bề mặt Trái Đất và không phải kết quả đo nhiệt độ trực tiếp tại từng điểm ảnh.

## 3.4. Nội dung và ý nghĩa các biểu đồ

Các biểu đồ được lựa chọn theo nhiệm vụ: biểu đồ đường theo dõi thời gian; biểu đồ cột so sánh đối tượng hoặc nhóm; bản đồ thể hiện phân bố không gian; biểu đồ cơ cấu thể hiện tỷ trọng; biểu đồ dự đoán phân biệt quan sát lịch sử với kết quả theo giả định.

Một kết quả trên biểu đồ chỉ được diễn giải đúng khi xác định đồng thời **chỉ tiêu, đơn vị, phạm vi không gian và thời gian**. Những thành phần dùng nguồn khác nhau không được mặc nhiên xem là cùng một tổng, và các hình tĩnh không được xem là đã áp dụng bộ lọc của dashboard.

### 3.4.1. Trang Tổng quan (Khang)

#### 3.4.1.1. Mục tiêu trình bày

Trang Tổng quan cung cấp bức tranh chung trước khi chuyển sang từng chủ đề. Trình tự nội dung đi từ “phạm vi đang xem có giá trị bao nhiêu” đến “giá trị phân bố ở đâu”, “thay đổi qua thời gian thế nào”, “quốc gia và ngành nào đóng góp nhiều”, sau đó giới thiệu phần mô hình toàn cầu.

#### 3.4.1.2. Ba chỉ số chính

Ba thẻ chỉ số gồm chênh lệch nhiệt độ, tổng CO₂ và CO₂/người. Giá trị được lấy tại năm đang chọn trên thanh trượt, theo quốc gia hoặc phạm vi tổng hợp tương ứng; trường hợp quốc gia không có bản ghi của năm đó được xử lý như mục 3.2.5. Năm sử dụng được ghi trên khối thông tin. Các thẻ thể hiện đơn vị riêng để không nhầm triệu tấn với tấn/người.

Ví dụ, khi chọn “Toàn cầu”, khoảng 1970–2024 và năm 2024:

| Chỉ tiêu | Giá trị dữ liệu | Cách hiển thị tại thẻ |
| --- | ---: | --- |
| Chênh lệch nhiệt độ | +1,29 °C | `+1.29` và đơn vị °C so với 1951–1980 |
| CO₂ hằng năm | 38.598,578 triệu tấn | Làm tròn một chữ số thập phân |
| CO₂/người | 4,729 tấn/người | Làm tròn hai chữ số thập phân |

Các số trên là chỉ tiêu năm 2024, không phải trung bình toàn bộ 1970–2024. Riêng chênh lệch nhiệt độ năm trong Tổng quan khác với trung bình trượt 5 năm được dùng trong phần mô hình.

#### 3.4.1.3. Các biểu đồ trên trang

| Biểu đồ | Dữ liệu và hình thức | Ý nghĩa |
| --- | --- | --- |
| Bản đồ thế giới | Quốc gia tại năm đang chọn; tô theo nhiệt độ hoặc tổng CO₂ | Nhận biết phân bố và chọn quốc gia cần khảo sát |
| Xu hướng nhiệt độ | Đường theo năm, đơn vị °C | Quan sát diễn biến chênh nhiệt độ trong toàn khoảng lọc |
| Lượng CO₂ theo thời gian | Đường và vùng nền, đơn vị triệu tấn | Theo dõi mức và xu hướng CO₂ của phạm vi chọn |
| Quốc gia thải CO₂ nhiều nhất | Cột ngang, nhóm 5 quốc gia cao nhất trong phạm vi | So sánh quy mô CO₂ tại năm chọn |
| CO₂ đến từ ngành nào? | Cột ngang theo tỷ trọng ngành, đơn vị % | Xác định cơ cấu và ngành đóng góp lớn nhất trong dữ liệu EDGAR |
| Nhiệt độ toàn cầu đến 2050 | Đường lịch sử và ba đường kịch bản | Giới thiệu kết quả mô hình; liên kết đến trang Mô hình dự đoán |

Hai đường xu hướng giữ toàn bộ khoảng thời gian để tránh việc đổi năm trên bản đồ làm mất bối cảnh dài hạn. Đường dọc đánh dấu vị trí của năm đang xem. Phần diện tích tô nhạt dưới đường chỉ hỗ trợ đọc hình, không phải một khoảng dự đoán hay độ tin cậy thống kê.

#### 3.4.1.4. So sánh quốc gia và cơ cấu ngành

Biểu đồ xếp hạng lấy nhóm 5 quốc gia có CO₂ cao nhất trong phạm vi châu lục đang xem. Nếu một quốc gia được chọn nhưng nằm ngoài nhóm này, hệ thống bổ sung quốc gia đó để vẫn có cơ sở đối chiếu. Vì vậy biểu đồ có thể có sáu cột, không phải luôn cố định năm cột. Việc bổ sung không làm thay đổi thứ hạng hay lượng CO₂ của nhóm cao nhất.

Tỷ trọng ngành được tính bằng CO₂ của ngành chia cho tổng CO₂ các ngành có dữ liệu trong cùng phạm vi và năm. Ở phạm vi toàn cầu năm 2024, tổng EDGAR sau các quy tắc lọc của dự án là khoảng **38.482,140 triệu tấn**, trong đó ngành điện chiếm khoảng **40,81%**.

Tổng này khác **38.598,578 triệu tấn** ở thẻ CO₂ toàn cầu lấy từ OWID/GCP. Hai con số không được ép bằng nhau: chúng thuộc hai hệ thống nguồn và cách xác định phạm vi khác nhau. Biểu đồ ngành mô tả cơ cấu trong tập EDGAR đang sử dụng, không phân rã chính xác từng phần của tổng OWID.

#### 3.4.1.5. Liên kết sang mô hình dự đoán

Phần cuối trang giới thiệu xu hướng nhiệt độ toàn cầu đến 2050 theo ba kịch bản. Liên kết “Khám phá mô hình” đưa người dùng đến trang có các điều khiển và phần đánh giá chi tiết. Phần này luôn là mô hình toàn cầu, kể cả khi phía trên đang chọn một quốc gia hoặc một châu lục.

### 3.4.6. Trang Dữ liệu (Khang)

#### 3.4.6.1. Vai trò của trang

Trang Dữ liệu giúp đối chiếu biểu đồ với các bản ghi cụ thể. Đây là bảng dữ liệu quốc gia–năm sau ghép và sau lọc, không phải bảng tổng hợp toàn cầu và cũng không phải danh sách các điểm dự đoán đến 2050.

Phần đầu bảng hiển thị số bản ghi, số quốc gia, số mốc năm và số dòng đang hiển thị. Các thông tin này giúp người dùng kiểm tra bộ lọc có được áp dụng hay không và nhận biết bảng trên màn hình có đang hiển thị đầy đủ kết quả hay chưa.

#### 3.4.6.2. Các cột hiển thị

Bảng trên giao diện thể hiện chín cột: quốc gia, mã quốc gia, châu lục, năm, chênh nhiệt độ, CO₂, CO₂/người, dân số và tỷ trọng năng lượng tái tạo. Hai cột `decade` và `source_flag` không hiện trong bảng giao diện nhưng vẫn có trong bảng ghép và CSV tải xuống.

Các chỉ tiêu nhiệt độ, CO₂, CO₂/người và năng lượng được làm tròn hai chữ số thập phân khi xem. Dân số hiển thị không có phần thập phân; giá trị thiếu được biểu diễn bằng “—”. Việc định dạng trên màn hình không thay đổi giá trị gốc lưu trong bảng.

#### 3.4.6.3. Thứ tự và giới hạn hiển thị

Các dòng được sắp xếp theo năm giảm dần, sau đó theo tên quốc gia tăng dần. Giao diện chỉ dựng **500 dòng đầu tiên** của kết quả đã sắp xếp nhằm hạn chế số thành phần phải hiển thị trong trình duyệt.

Ở phạm vi đầy đủ, dòng thống kê thể hiện 13.296 bản ghi, 244 quốc gia, 55 mốc năm và 500/13.296 dòng được hiển thị. Giới hạn 500 dòng không phải thao tác xóa dữ liệu, cũng không phải cơ chế lấy mẫu để phân tích. Biểu đồ và tệp CSV vẫn sử dụng phạm vi dữ liệu tương ứng của chúng.

#### 3.4.6.4. Ví dụ đối chiếu

Khi chọn Việt Nam và giai đoạn 2015–2024, người dùng có thể tìm năm 2024 trong bảng để đối chiếu mức chênh nhiệt độ +1,914 °C và lượng CO₂ 370,931 triệu tấn với biểu đồ của quốc gia. Giá trị năng lượng tái tạo năm này hiển thị “—” vì bảng nguồn hiện không có số liệu tương ứng. Việc chọn đầy đủ các năm trong bộ lọc không làm xuất hiện một giá trị năng lượng được tự suy ra.

## 3.5. Chức năng xem và xuất dữ liệu (Khang)

### 3.5.1. Xem chi tiết và mở rộng biểu đồ

Biểu đồ tương tác hỗ trợ rê chuột để đọc giá trị tại điểm, cột hoặc vùng quốc gia. Trên hai trang phân tích thành viên, nút “Mở rộng” mở lại chính biểu đồ đang hiển thị trong một cửa sổ lớn hơn. Nội dung này lấy từ trạng thái biểu đồ hiện tại nên giữ dữ liệu đã lọc, không tải một HTML mặc định với phạm vi khác.

Cửa sổ mở rộng có thể đóng bằng nút đóng, phím Escape hoặc bấm vào vùng nền bên ngoài. Khi chuyển trang hoặc thay đổi bộ lọc, cửa sổ được đóng để tránh giữ lại một biểu đồ thuộc phạm vi cũ. Các hình tĩnh cũng có thể được mở rộng, nhưng dữ liệu trong hình vẫn là dữ liệu cố định khi xuất.

Với các biểu đồ có thanh công cụ Plotly, người dùng có thể tải ảnh biểu đồ. Cấu hình tải ảnh đặt tên `climate-lab` và tỷ lệ xuất bằng 2. Thanh công cụ này không hiển thị trên địa cầu; việc mở rộng biểu đồ không đồng nghĩa mọi thành phần của dashboard đều có cùng bộ công cụ.

### 3.5.2. Xuất dữ liệu lịch sử theo bộ lọc

Nút tải dữ liệu trên phần đầu ứng dụng và nút “Tải CSV đang lọc” ở trang Dữ liệu sử dụng cùng hàm lọc theo khoảng năm, châu lục và quốc gia. Tệp xuất có tên `du-lieu-khi-hau.csv`, gồm đầy đủ các bản ghi thỏa điều kiện, không giới hạn ở 500 dòng trên màn hình.

CSV gồm 11 cột của bảng ghép, có cả `decade` và `source_flag`. Chương trình không ghi thêm cột chỉ số dòng của pandas. Giá trị số được xuất từ bảng dữ liệu, không lấy từ chuỗi ký tự đã làm tròn trong các thẻ chỉ số hoặc trong bảng giao diện.

Cần phân biệt phạm vi xuất với các trạng thái hiển thị riêng:

- Thanh “Năm đang xem” của Tổng quan không giới hạn CSV xuống một năm; CSV vẫn dùng khoảng năm của bộ lọc chung.
- Nút “Màu bản đồ” không loại bớt các cột trong CSV; tệp vẫn có đầy đủ các chỉ tiêu của bảng ghép.
- Khi chọn “Tất cả quốc gia”, CSV là danh sách bản ghi quốc gia–năm, không phải dòng `World` hoặc chuỗi nhiệt độ toàn cầu NASA.
- Khi chọn một quốc gia trên bản đồ, lựa chọn đó cập nhật vào bộ lọc quốc gia và được áp dụng khi xuất CSV lịch sử.

Các quy tắc này bảo đảm tệp tải xuống được xác định bằng những điều kiện lọc rõ ràng, thay vì phụ thuộc vào vị trí cuộn, số dòng đang nhìn thấy hoặc màu đang chọn trên bản đồ.

### 3.5.3. Xuất dữ liệu kịch bản

Trang Mô hình dự đoán có nút CSV riêng, xuất tệp `kich-ban-khi-hau-2025-2050.csv`. Với trạng thái mặc định, tệp chứa ba kịch bản, mỗi kịch bản 26 năm, tương ứng **78 dòng**. Khi người dùng chọn “Tùy chỉnh”, kết quả tùy chỉnh được bổ sung vào ba kịch bản mặc định, tạo **104 dòng**.

Các cột gồm mã và tên kịch bản, tốc độ thay đổi CO₂ hằng năm, năm dự đoán, CO₂ hằng năm, CO₂ tích lũy, nhiệt độ dự đoán và hai cận khoảng dự đoán 90%. Cột `co2` và `cumulative_co2` trong CSV vẫn dùng triệu tấn; việc đổi sang tỷ tấn chỉ được thực hiện khi hiển thị hoặc đưa CO₂ tích lũy vào phương trình hồi quy.

Lựa chọn mốc 2030, 2040 hoặc 2050 chỉ thay điểm nhấn và các chỉ số trên màn hình, không cắt CSV xuống một dòng tại mốc đó. Tệp xuất vẫn bao gồm toàn bộ các năm 2025–2050 của các kịch bản đang được lưu trong trạng thái trang.

### 3.5.4. Quan hệ giữa HTML xuất độc lập và dashboard

Tệp HTML tương tác được tạo bởi `main()` trong script Plotly của từng thành viên, sử dụng dữ liệu và phạm vi năm đã quy định ở script. Dashboard dùng cùng hàm `build_figures()` nhưng truyền dữ liệu sau lọc và điều chỉnh cách trình bày phù hợp giao diện.

Vì vậy, sự thống nhất nằm ở hàm tạo biểu đồ và cách tính với cùng đầu vào, không có nghĩa mọi HTML phải giống hình trên dashboard ở tất cả trạng thái. HTML nhiệt độ độc lập có thể bao phủ 1880–2025 hoặc 1961–2025, trong khi dashboard chung giới hạn 1970–2024. Các hình EDA tĩnh có thể dùng một năm cụ thể khác, chẳng hạn 2023 cho một số phân tích CO₂ và năng lượng.

HTML xuất độc lập hiện không tích hợp bộ lọc chung năm–châu lục–quốc gia của ứng dụng. Khi sử dụng HTML hoặc ảnh trong báo cáo, phạm vi được ghi theo chính dữ liệu đã xuất. Khi trình bày trên dashboard, số liệu chỉ được đối chiếu trực tiếp nếu đồng nhất được chỉ tiêu, nguồn, quốc gia và thời gian.

## 4.3. Đối chiếu dữ liệu nhiệt độ và CO₂ (Khang)

### 4.3.1. Mục đích và cơ sở đối chiếu

Phần đối chiếu xem xét liệu xu hướng nhiệt độ và lượng CO₂ có cùng chiều trong giai đoạn nghiên cứu, đồng thời phân biệt xu hướng dài hạn với biến động từng năm. Chuỗi được sử dụng là `khi_hau_toan_cau_nam.csv`, gồm 55 cặp quan sát toàn cầu từ 1970 đến 2024.

Việc dùng bảng đã ghép theo năm bảo đảm nhiệt độ của một năm được đối chiếu với CO₂ của chính năm đó. Nhiệt độ lấy từ NASA GISTEMP và CO₂ lấy từ dòng `World` của OWID/GCP. Không thay chuỗi nhiệt độ toàn cầu bằng trung bình đơn giản của các quốc gia, cũng không trộn CO₂/người vào chỉ tiêu tổng CO₂.

### 4.3.2. Xu hướng toàn cầu trong giai đoạn 1970–2024

| Năm | Chênh nhiệt độ năm so với 1951–1980 (°C) | CO₂ hằng năm (triệu tấn) | CO₂ tích lũy (triệu tấn) |
| --- | ---: | ---: | ---: |
| 1970 | +0,03 | 14.899,139 | 425.626,469 |
| 1990 | +0,45 | 22.732,145 | 807.091,000 |
| 2000 | +0,39 | 25.511,482 | 1.045.316,812 |
| 2010 | +0,72 | 33.317,672 | 1.342.110,500 |
| 2020 | +1,01 | 35.158,230 | 1.698.036,625 |
| 2024 | +1,29 | 38.598,578 | 1.849.123,875 |

Từ năm 1970 đến 2024, lượng CO₂ hằng năm tăng khoảng **159,07%**, tương đương mức năm 2024 bằng khoảng **2,59 lần** năm 1970. Chênh nhiệt độ năm tăng từ +0,03 °C lên +1,29 °C, tức tăng **1,26 °C** giữa hai mốc. Không tính phần trăm tăng nhiệt độ bằng cách chia cho giá trị +0,03 °C, vì đây là độ lệch theo một mốc cơ sở, có thể gần 0 hoặc âm.

Để giảm ảnh hưởng của một năm riêng lẻ, trang Nhận định so sánh trung bình 5 năm đầu và 5 năm cuối trong khoảng đầy đủ. Trung bình 1970–1974 bằng **+0,010 °C**, còn trung bình 2020–2024 bằng **+1,042 °C**, chênh **+1,032 °C**. Kết quả cho thấy mức nhiệt độ ở cuối giai đoạn cao hơn đầu giai đoạn ngay cả khi không chỉ chọn hai năm đầu–cuối.

Sự gia tăng đồng thời của CO₂ và nhiệt độ tạo nên mạch phân tích chính: nhận diện thay đổi theo thời gian, đối chiếu giữa nguồn, sau đó khảo sát quan hệ thống kê bằng hồi quy. Tuy nhiên, các đường cùng đi lên chưa đủ để xác định mức tác động riêng của CO₂ hay loại trừ các yếu tố khí hậu khác.

### 4.3.3. Phân biệt quan hệ dài hạn và biến động từng năm

Năm 2019, CO₂ toàn cầu là **37.086,566 triệu tấn**, còn chênh nhiệt độ là **+0,98 °C**. Năm 2020, CO₂ giảm xuống **35.158,230 triệu tấn**, tương đương giảm khoảng **5,20%**, trong khi chênh nhiệt độ tăng lên **+1,01 °C**.

Ví dụ này cho thấy hai chỉ tiêu không nhất thiết thay đổi cùng chiều trong từng năm. CO₂ hằng năm giảm cũng không làm CO₂ tích lũy giảm ngay, vì lượng CO₂ của năm đó vẫn lớn hơn 0. Phân tích vì vậy không sử dụng quy tắc “CO₂ năm nay giảm thì nhiệt độ năm nay phải giảm” để kết luận dữ liệu đúng hay sai.

Đây cũng là cơ sở để mô hình sử dụng CO₂ tích lũy và nhiệt độ trung bình trượt 5 năm, thay vì chỉ liên hệ trực tiếp lượng CO₂ của một năm với nhiệt độ riêng năm đó. Lựa chọn này hỗ trợ mô tả xu hướng, nhưng không biến hồi quy đơn biến thành mô hình giải thích đầy đủ các quá trình khí hậu.

### 4.3.4. Đối chiếu định lượng và giới hạn của tương quan

Tính trên 55 cặp quan sát toàn cầu 1970–2024, hệ số tương quan Pearson giữa **CO₂ hằng năm** và **chênh nhiệt độ hằng năm** xấp xỉ **0,9411**. Đây là phép tính bổ sung cho phần đối chiếu trong báo cáo, không phải chỉ số đang dùng để đánh giá mô hình dự đoán.

Hệ số dương cho thấy hai chuỗi có xu hướng biến động cùng chiều trong toàn giai đoạn. Tuy nhiên, cả hai chuỗi đều thay đổi theo thời gian, nên hệ số tương quan lớn có thể chịu ảnh hưởng đáng kể của xu hướng chung. Không diễn giải kết quả này thành tỷ lệ dự đoán đúng, mức đóng góp nhân quả của CO₂ hoặc khả năng dự đoán từng năm.

Hệ số trên cũng không thay thế R² của mô hình ở Chương 5. Hai phép tính có biến khác nhau: phần đối chiếu dùng CO₂ và nhiệt độ hằng năm; hồi quy dùng CO₂ tích lũy và nhiệt độ trung bình trượt 5 năm, đồng thời đánh giá trên tập kiểm tra riêng.

### 4.3.5. Đối chiếu theo quốc gia

Các bản ghi quốc gia giúp minh họa sự khác nhau giữa tổng CO₂, chỉ tiêu bình quân đầu người và mức thay đổi nhiệt độ tại một quốc gia.

| Quốc gia, năm 2024 | Chênh nhiệt độ quốc gia (°C) | CO₂ (triệu tấn) | CO₂/người (tấn) |
| --- | ---: | ---: | ---: |
| Trung Quốc | +2,277 | 12.289,037 | 8,658 |
| Hoa Kỳ | +1,947 | 4.904,120 | 14,197 |
| Việt Nam | +1,914 | 370,931 | 3,673 |

Trong ba ví dụ này, Trung Quốc có tổng CO₂ cao hơn Hoa Kỳ, nhưng Hoa Kỳ có CO₂/người cao hơn. Vì vậy, thứ hạng quốc gia phụ thuộc đại lượng được dùng để so sánh. Mức chênh nhiệt độ của một quốc gia cũng không được xem là kết quả chỉ do lượng CO₂ mà chính quốc gia đó tạo ra.

Nhiệt độ trong bảng là số liệu FAOSTAT trên đất liền, còn tổng CO₂ và CO₂/người lấy từ OWID/GCP. So sánh các con số cần giữ nguyên định nghĩa nguồn; không kết luận nhiệt độ toàn cầu bằng trung bình ba quốc gia hoặc bằng trung bình tất cả các dòng quốc gia trong bảng ghép.

### 4.3.6. Kết luận phân tích

Dữ liệu 1970–2024 cho thấy CO₂ và nhiệt độ toàn cầu cùng có xu hướng tăng dài hạn, nhưng không biến động đồng nhất trong từng năm. Chênh lệch giữa các nước tiếp tục cho thấy tổng CO₂ và CO₂/người là hai góc nhìn khác nhau. Từ kết quả này, đề tài chuyển sang xây dựng hồi quy tuyến tính nhằm định lượng quan hệ thống kê giữa CO₂ tích lũy và xu hướng nhiệt độ, đồng thời đặt giới hạn rõ ràng cho việc diễn giải các kịch bản tương lai.

## 5.1. Xác định bài toán dự báo (Khang)

### 5.1.1. Câu hỏi nghiên cứu

Bài toán được đặt ra là: **Nếu lượng CO₂ toàn cầu hằng năm thay đổi theo những giả định khác nhau sau năm 2024, chênh lệch nhiệt độ trung bình trượt 5 năm được mô hình ước tính đến năm 2050 sẽ khác nhau như thế nào?**

Đây là bài toán hồi quy vì đầu ra là một đại lượng liên tục, đơn vị °C. Đề tài không phân loại năm thành “nóng” hoặc “lạnh”, cũng không dự đoán một nhãn rủi ro. Do đó, hồi quy tuyến tính được sử dụng thay cho hồi quy Logistic.

### 5.1.2. Đầu vào, đầu ra và phạm vi áp dụng

| Thành phần | Nội dung |
| --- | --- |
| Không gian | Toàn cầu |
| Dữ liệu lịch sử ban đầu | 55 quan sát năm, từ 1970 đến 2024 |
| Biến đầu vào hồi quy | CO₂ tích lũy, chuyển từ triệu tấn sang tỷ tấn |
| Biến mục tiêu | Trung bình trượt 5 năm của chênh nhiệt độ toàn cầu so với 1951–1980 |
| Dữ liệu hợp lệ sau tạo biến | 51 quan sát, từ 1974 đến 2024 |
| Giai đoạn mô phỏng | 2025–2050 |
| Điều khiển kịch bản | Tốc độ thay đổi lượng CO₂ hằng năm |

Lượng CO₂ hằng năm được dùng để xây dựng đường CO₂ tích lũy của tương lai. Nó không phải biến thứ hai được đưa trực tiếp vào hồi quy; mô hình chỉ có một biến giải thích là CO₂ tích lũy.

### 5.1.3. Tiêu chí đánh giá bài toán

Mô hình cần thực hiện đúng thuật toán hồi quy tuyến tính, sử dụng tập kiểm tra nằm sau tập huấn luyện theo thời gian, công bố chỉ số đánh giá và tích hợp kết quả vào dashboard. Các kịch bản cần dùng cùng công thức với phần CSV để kết quả không thay đổi tùy theo nơi xem.

Đối với đồ án này, kết quả được đánh giá bằng R², MAE và RMSE. Độ tin cậy của dự đoán dài hạn không được suy ra chỉ từ một chỉ số khớp trên dữ liệu lịch sử. Phần trình bày cần chỉ rõ nhiệt độ được dự đoán là trung bình trượt 5 năm và các đường tương lai phụ thuộc giả định CO₂.

## 5.2. Lựa chọn biến và xây dựng mô hình hồi quy tuyến tính (Khang)

### 5.2.1. Biến đầu vào

Gọi Cₜ là CO₂ tích lũy toàn cầu tại năm t, theo triệu tấn CO₂ trong nguồn. Biến đầu vào của mô hình là:

```text
xₜ = Cₜ / 1.000
```

xₜ có đơn vị tỷ tấn CO₂, còn gọi là Gt CO₂. Phép chia chỉ chuyển đơn vị, không chuẩn hóa theo trung bình hoặc độ lệch chuẩn. Cụ thể, CO₂ tích lũy năm 2024 trong dữ liệu là **1.849.123,875 triệu tấn**, tương ứng **1.849,123875 tỷ tấn**.

Biến CO₂ tích lũy phản ánh tổng cộng dồn trong chuỗi lịch sử nguồn, khác với lượng CO₂ của riêng năm t. Không tính lại biến này chỉ bằng cách cộng từ năm 1970 vì sẽ làm thay đổi mức nền tích lũy đang được dùng trong phương trình.

### 5.2.2. Biến mục tiêu

Gọi aₜ là chênh nhiệt độ năm t so với thời kỳ cơ sở. Biến mục tiêu được xác định bằng trung bình trượt lùi 5 năm:

```text
yₜ = (aₜ + aₜ₋₁ + aₜ₋₂ + aₜ₋₃ + aₜ₋₄) / 5
```

Giá trị được gắn với năm cuối của cửa sổ. Vì vậy, `y₂₀₂₄` là trung bình của các năm 2020–2024, không phải trung bình 2024–2028 và cũng không phải nhiệt độ riêng năm 2024.

Trong pandas, phép tính tương ứng là `temperature_anomaly.rolling(5).mean()`, không dùng cửa sổ đặt giữa. Bốn năm đầu 1970–1973 không đủ năm trước để tạo cửa sổ trong chuỗi đầu vào nên không được dùng làm quan sát mục tiêu. Từ 55 dòng ban đầu, mô hình còn 51 dòng hợp lệ.

Ví dụ:

```text
y₂₀₂₄ = (1,01 + 0,85 + 0,89 + 1,17 + 1,29) / 5 = 1,042 °C
```

Trung bình trượt làm giảm biến động ngắn hạn, giúp mô hình tập trung vào xu hướng. Đổi lại, các giá trị yₜ liên tiếp dùng chung nhiều năm thành phần, nên các quan sát sau làm trơn không hoàn toàn độc lập với nhau.

### 5.2.3. Phương trình và thuật toán ước lượng

Hồi quy tuyến tính đơn biến được viết dưới dạng:

```text
ŷₜ = β₀ + β₁xₜ
```

Trong đó:

- ŷₜ là chênh nhiệt độ trung bình trượt 5 năm được dự đoán, đơn vị °C.
- β₀ là hệ số chặn, đơn vị °C.
- β₁ là hệ số của CO₂ tích lũy, đơn vị °C/Gt CO₂.
- xₜ là CO₂ tích lũy toàn cầu, đơn vị Gt CO₂.

Chương trình dùng `LinearRegression` của scikit-learn để tìm β₀ và β₁ theo phương pháp bình phương tối thiểu, tức tối thiểu hóa tổng bình phương phần chênh giữa mục tiêu thực tế và dự đoán trên tập huấn luyện:

```text
SSE = Σ (yₜ − β₀ − β₁xₜ)²
```

Mô hình có hệ số chặn và một hệ số góc, không sử dụng điều chuẩn hoặc nhiều tầng xử lý. Việc đổi đơn vị và tạo trung bình trượt được thực hiện trước bước `fit`. [Tài liệu LinearRegression](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LinearRegression.html)

### 5.2.4. Phân biệt mô hình kiểm tra và mô hình tạo kịch bản

Cùng một thuật toán được huấn luyện ở hai thời điểm khác nhau trong chương trình, với hai mục đích riêng:

| Mục đích | Dữ liệu dùng để huấn luyện | Hệ số chặn β₀ | Hệ số β₁ |
| --- | --- | ---: | ---: |
| Dự đoán tập kiểm tra 2015–2024 | 1974–2014 | −0,306927460 | 0,000714380848 |
| Tạo các kịch bản 2025–2050 | 1974–2024 | −0,311193076 | 0,000719406132 |

Phương trình dùng cho các đường kịch bản hiện tại là:

```text
ŷₜ = −0,311193076 + 0,000719406132 × xₜ
```

Các hệ số trong bảng được làm tròn để trình bày; chương trình tính bằng giá trị đầy đủ. Nếu dùng phương trình đã làm tròn để kiểm tra thủ công, có thể xuất hiện sai khác nhỏ ở những chữ số cuối.

Hệ số dương cho thấy trong mẫu lịch sử, CO₂ tích lũy cao hơn đi cùng xu hướng nhiệt độ cao hơn. Không diễn giải β₁ là một hằng số vật lý áp dụng cho mọi thời kỳ hoặc là mức tác động nhân quả đã được tách khỏi mọi yếu tố khác. Hệ số chặn cũng không được hiểu là nhiệt độ thực tế khi toàn bộ lịch sử CO₂ bằng 0, vì đó là phạm vi nằm ngoài dữ liệu huấn luyện.

## 5.3. Chia dữ liệu huấn luyện và kiểm tra (Khang)

### 5.3.1. Chia theo trình tự thời gian

Sau khi tạo biến mục tiêu, dữ liệu 1974–2024 được chia tại mốc 2014:

| Tập dữ liệu | Giai đoạn | Số quan sát | Mục đích |
| --- | --- | ---: | --- |
| Huấn luyện | 1974–2014 | 41 | Ước lượng hệ số hồi quy cho bước đánh giá |
| Kiểm tra | 2015–2024 | 10 | So sánh dự đoán với dữ liệu chưa dùng để fit ở bước đánh giá |
| Huấn luyện lại | 1974–2024 | 51 | Ước lượng phương trình dùng tạo kịch bản sau khi đã đánh giá |

Tập huấn luyện chiếm khoảng 80,39% và tập kiểm tra chiếm khoảng 19,61% số quan sát. Tỷ lệ này là kết quả của việc chọn mốc năm, không phải chia ngẫu nhiên theo tỷ lệ 80/20.

Không trộn ngẫu nhiên các năm giữa hai tập. Cách chia theo thời gian giữ được thứ tự lịch sử: hệ số được ước lượng từ giai đoạn trước và đánh giá ở giai đoạn sau.

### 5.3.2. Trình tự đánh giá và huấn luyện lại

Quá trình trong `mo_hinh_nhiet_do.py` được thực hiện theo thứ tự:

1. Sắp xếp dữ liệu năm và kiểm tra các biến cần thiết không thiếu, không vô cực, không đứt quãng năm.
2. Tính biến nhiệt độ trung bình trượt 5 năm.
3. Huấn luyện trên các năm không lớn hơn 2014.
4. Dự đoán các năm 2015–2024 bằng mô hình vừa huấn luyện.
5. Tính và lưu R², MAE, RMSE của bước kiểm tra.
6. Huấn luyện lại trên toàn bộ 51 quan sát để tạo các kịch bản tương lai.

Mảng dự đoán dùng cho tập kiểm tra được tạo trước bước huấn luyện lại và được lưu riêng. Do đó, chỉ số kiểm tra không được tính bằng mô hình đã nhìn thấy nhiệt độ của tập kiểm tra trong lúc fit.

### 5.3.3. Điều kiện của phép kiểm tra hiện tại

Đầu vào CO₂ tích lũy của 2015–2024 được lấy từ các quan sát đã có trong dữ liệu. Vì vậy, đây là kiểm tra khả năng ước tính nhiệt độ **khi biết CO₂ tích lũy của từng năm**, không phải mô phỏng hoàn chỉnh việc đứng ở cuối 2014 và dự đoán cả CO₂ lẫn nhiệt độ trong mười năm tiếp theo.

Sự khác biệt này quan trọng đối với hồi quy có biến đầu vào chưa biết trong tương lai. Phép kiểm tra dùng giá trị đầu vào đã quan trắc giúp đánh giá quan hệ hồi quy, nhưng không bao gồm sai số khi phải dự đoán chính biến đầu vào đó. [Phân biệt dự báo trước và đánh giá với đầu vào đã biết](https://otexts.com/fpp3/forecasting-regression.html)

Ngoài ra, các cửa sổ trung bình trượt ở hai phía mốc chia có phần năm thành phần trùng nhau. Chẳng hạn, mục tiêu năm 2015 dùng nhiệt độ 2011–2015, trong khi mục tiêu năm 2014 dùng 2010–2014. Đây không phải việc dùng nhiệt độ năm sau để tạo mục tiêu của năm trước, nhưng làm các mục tiêu liên tiếp có liên hệ mạnh; không được xem mười quan sát kiểm tra là mười phép thử độc lập hoàn toàn.

## 5.4. Đánh giá mô hình bằng R² và MAE (Khang)

### 5.4.1. Các chỉ số đánh giá

Với n là số quan sát kiểm tra, yᵢ là mục tiêu thực tế, ŷᵢ là dự đoán và ȳ là trung bình mục tiêu thực tế trong tập kiểm tra:

```text
MAE  = Σ |yᵢ − ŷᵢ| / n
RMSE = √[Σ (yᵢ − ŷᵢ)² / n]
R²   = 1 − Σ (yᵢ − ŷᵢ)² / Σ (yᵢ − ȳ)²
```

MAE thể hiện độ lớn sai số tuyệt đối trung bình, cùng đơn vị °C với biến mục tiêu. RMSE cũng có đơn vị °C nhưng nhạy hơn với các sai số lớn do bình phương sai số trước khi lấy trung bình.

R² so sánh tổng bình phương sai số của mô hình với mức dùng trung bình mục tiêu làm giá trị tham chiếu. Giá trị càng gần 1 thể hiện mức khớp càng cao theo thước đo này; R² có thể âm khi kết quả tệ hơn mức tham chiếu. **R² không phải tỷ lệ số lần dự đoán đúng.** [Định nghĩa R² trong scikit-learn](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.r2_score.html)

### 5.4.2. Kết quả đánh giá chính

| Chỉ số | Giá trị tính được | Giá trị làm tròn để trình bày |
| --- | ---: | ---: |
| R² trên tập huấn luyện | 0,9560768145 | 0,956 |
| R² trên tập kiểm tra | 0,8345060480 | 0,835 |
| MAE trên tập kiểm tra | 0,0306100301 °C | 0,031 °C |
| RMSE trên tập kiểm tra | 0,0357603812 °C | 0,036 °C |
| Sai số tuyệt đối lớn nhất trên tập kiểm tra | 0,0592814778 °C | 0,059 °C |

Các chỉ số cho thấy mô hình bám tương đối sát biến mục tiêu trung bình trượt 5 năm ở giai đoạn kiểm tra 2015–2024. Tuy nhiên, MAE 0,031 °C không có nghĩa mọi năm đều sai không quá 0,031 °C; đây là trung bình của mười sai số tuyệt đối. Tương tự, kết quả không cho biết sai số chắc chắn của năm 2050.

Không trình bày R² = 0,8345 thành “độ chính xác 83,45%” hay “83,45% số năm được dự đoán đúng”. Theo đúng công thức, tổng bình phương sai số của mô hình thấp hơn khoảng 83,45% so với mức tham chiếu là trung bình của tập kiểm tra. Khi báo cáo kết quả, sử dụng trực tiếp **R² = 0,835; MAE = 0,031 °C** là rõ ràng hơn.

### 5.4.3. Đối chiếu từng năm trong tập kiểm tra

| Năm | Mục tiêu thực tế: TB 5 năm (°C) | Dự đoán (°C) | Dự đoán − thực tế (°C) |
| --- | ---: | ---: | ---: |
| 2015 | 0,7180 | 0,7773 | +0,0593 |
| 2016 | 0,7980 | 0,8026 | +0,0046 |
| 2017 | 0,8520 | 0,8283 | −0,0237 |
| 2018 | 0,8860 | 0,8545 | −0,0315 |
| 2019 | 0,9320 | 0,8810 | −0,0510 |
| 2020 | 0,9540 | 0,9061 | −0,0479 |
| 2021 | 0,9220 | 0,9325 | +0,0105 |
| 2022 | 0,9160 | 0,9593 | +0,0433 |
| 2023 | 0,9800 | 0,9865 | +0,0065 |
| 2024 | 1,0420 | 1,0141 | −0,0279 |

Sai số dương là dự đoán cao hơn thực tế, sai số âm là dự đoán thấp hơn thực tế. Mô hình dự đoán thấp trong các năm 2017–2020 rồi cao hơn trong 2021–2023, cho thấy sai số có thể xuất hiện thành nhóm theo thời gian thay vì phân bố hoàn toàn ngẫu nhiên.

Ở năm 2024, dự đoán kiểm tra 1,0141 °C được đối chiếu với trung bình 2020–2024 là 1,0420 °C. Không lấy dự đoán này so trực tiếp với chênh nhiệt độ riêng năm 2024 là 1,29 °C để tính các chỉ số đang công bố, vì đó là hai mục tiêu khác nhau.

### 5.4.4. Kiểm tra bổ sung theo giai đoạn

Một phép chia huấn luyện–kiểm tra chưa đủ để khẳng định chất lượng ổn định ở mọi thời kỳ. Khi lập báo cáo, mô hình được đối chiếu bổ sung bằng cách tăng dần mốc kết thúc huấn luyện và kiểm tra năm năm tiếp theo, vẫn giữ CO₂ quan trắc làm đầu vào:

| Giai đoạn huấn luyện | Giai đoạn kiểm tra bổ sung | MAE (°C) |
| --- | --- | ---: |
| 1974–2004 | 2005–2009 | 0,0261 |
| 1974–2009 | 2010–2014 | 0,0930 |
| 1974–2014 | 2015–2019 | 0,0340 |
| 1974–2019 | 2020–2024 | 0,0284 |

Đây là kết quả đối chiếu bổ sung trên cùng dữ liệu, không phải các chỉ số đang được lưu thay thế trong dashboard. MAE cao hơn ở 2010–2014 cho thấy khả năng dự đoán phụ thuộc giai đoạn. Không chọn riêng khoảng có sai số thấp nhất làm kết quả đại diện cho mọi năm.

Kết quả chính được trình bày trên dashboard vẫn là tập kiểm tra 2015–2024 với mười quan sát. R² huấn luyện cao hơn R² kiểm tra là một điểm cần theo dõi, nhưng chỉ chênh lệch này chưa đủ để kết luận chắc chắn mô hình bị quá khớp; còn cần xét số mẫu, cách chia và cấu trúc chuỗi thời gian.

## 5.5. Xây dựng các kịch bản đến năm 2050 (Khang)

### 5.5.1. Giá trị gốc và cách tính CO₂ tương lai

Năm gốc của kịch bản là 2024, với hai giá trị:

- CO₂ hằng năm E₂₀₂₄ = **38.598,578 triệu tấn/năm**.
- CO₂ tích lũy C₂₀₂₄ = **1.849.123,875 triệu tấn**.

Giả sử g là tốc độ thay đổi CO₂ hằng năm, các năm 2025–2050 được tính như sau:

```text
Eₜ = E₂₀₂₄ × (1 + g)^(t − 2024)
Cₜ = C₂₀₂₄ + Σ Eₖ, với k từ 2025 đến t
xₜ = Cₜ / 1.000
ŷₜ = β₀ + β₁xₜ
```

Tốc độ g được lưu dưới dạng số thập phân, chẳng hạn giảm 5% tương ứng −0,05. Công thức áp dụng lãi kép theo năm, không trừ đi cùng một lượng CO₂ tuyệt đối ở mọi năm. CO₂ năm 2024 đã nằm trong C₂₀₂₄ nên không được cộng lại khi bắt đầu kịch bản.

### 5.5.2. Ba kịch bản mặc định

**Kịch bản tiếp diễn xu hướng.** Tốc độ được tính từ mức CO₂ năm 2005 và 2024 bằng tốc độ tăng trưởng kép bình quân:

```text
g = (E₂₀₂₄ / E₂₀₀₅)^(1 / 19) − 1
  = (38.598,578 / 29.598,951)^(1 / 19) − 1
  ≈ 0,014070519 = 1,407052%/năm
```

Đây là tốc độ suy ra từ hai đầu mốc 2005–2024, không phải trung bình cộng của tất cả tỷ lệ tăng trưởng từng năm. Mô hình giả định tốc độ này tiếp tục không đổi đến 2050.

**Kịch bản giữ mức 2024.** Đặt g = 0, khi đó lượng CO₂ hằng năm giữ bằng 38.598,578 triệu tấn. CO₂ tích lũy vẫn tăng do mỗi năm có thêm một lượng CO₂ dương.

**Kịch bản giảm 5% mỗi năm.** Đặt g = −0,05, khi đó CO₂ năm sau bằng 95% năm trước. Mặc dù lượng hằng năm giảm dần, CO₂ tích lũy vẫn tăng trong toàn giai đoạn mô phỏng vì lượng bổ sung vẫn dương.

Các tên kịch bản mô tả giả định trong đồ án, không đại diện cho một lộ trình chính sách hoặc bộ kịch bản khí hậu chính thức.

### 5.5.3. Kịch bản tùy chỉnh

Dashboard cho phép điều chỉnh g trong khoảng **−10% đến +5%/năm**, bước **0,5 điểm phần trăm**, khi lựa chọn “Tùy chỉnh”. Hàm `tao_kich_ban()` tính lại các năm tương lai bằng cùng bộ hệ số đã huấn luyện trên 1974–2024.

Thao tác thay tốc độ CO₂ không huấn luyện lại mô hình. Nó chỉ thay đường đầu vào tương lai rồi đưa các giá trị đó vào phương trình đã có. Vì vậy, kịch bản tùy chỉnh và các kịch bản xuất sẵn có cùng cách tính, khác nhau ở g.

### 5.5.4. Nhiệt độ dự đoán tại các mốc so sánh

| Kịch bản | Tốc độ CO₂ hằng năm | 2030 (°C) | 2040 (°C) | 2050 (°C) |
| --- | ---: | ---: | ---: | ---: |
| Tiếp diễn xu hướng | +1,407052% | 1,1941 | 1,5204 | 1,8957 |
| Giữ mức 2024 | 0% | 1,1857 | 1,4634 | 1,7410 |
| Giảm 5%/năm | −5% | 1,1588 | 1,3145 | 1,4076 |

Các giá trị trong bảng đều là **chênh nhiệt độ trung bình trượt 5 năm so với 1951–1980**. Mốc 2050 được hiểu là giá trị xu hướng 5 năm gắn với năm 2050 theo định nghĩa mục tiêu, không phải dự đoán riêng nhiệt độ của một ngày hoặc của toàn năm 2050 chưa làm trơn.

Ở năm 2050, kịch bản giữ mức 2024 thấp hơn tiếp diễn khoảng **0,1547 °C**; kịch bản giảm 5%/năm thấp hơn khoảng **0,4881 °C**. Đây là chênh lệch giữa các kết quả của cùng mô hình dưới các giả định khác nhau, không phải mức giảm nhiệt độ đã được quan trắc hoặc được bảo đảm sẽ xảy ra.

### 5.5.5. CO₂ hằng năm và khoảng dự đoán tại 2050

| Kịch bản | CO₂ năm 2050 (tỷ tấn/năm) | Nhiệt độ dự đoán (°C) | Khoảng dự đoán 90% xấp xỉ (°C) |
| --- | ---: | ---: | --- |
| Tiếp diễn xu hướng | 55,5064 | 1,8957 | 1,8061–1,9853 |
| Giữ mức 2024 | 38,5986 | 1,7410 | 1,6545–1,8276 |
| Giảm 5%/năm | 10,1715 | 1,4076 | 1,3267–1,4886 |

CO₂ tích lũy năm 2050 của cả ba kịch bản đều lớn hơn mức cao nhất trong dữ liệu huấn luyện. Các dự đoán ở mốc này vì vậy là ngoại suy ra ngoài miền đầu vào đã quan sát, cần được diễn giải thận trọng hơn kết quả kiểm tra trong lịch sử.

## 5.6. Trực quan hóa và diễn giải kết quả dự báo (Khang)

### 5.6.1. Bố cục trang mô hình

Trang Mô hình dự đoán gồm bộ chọn kịch bản, bộ chọn mốc so sánh, ba thẻ chỉ số, biểu đồ nhiệt độ chính, biểu đồ CO₂ hằng năm và biểu đồ kiểm tra. Phần “Dữ liệu & phương pháp” được thu gọn để giữ giao diện tập trung vào kết quả nhưng vẫn cung cấp thông tin về nguồn, biến và sai số.

Ba thẻ chỉ số thể hiện:

1. Chênh nhiệt độ dự đoán tại mốc đang chọn, kèm hai cận 90%.
2. Mức chênh so với kịch bản tiếp diễn tại cùng năm.
3. Lượng CO₂ hằng năm tại mốc đó, hiển thị bằng tỷ tấn.

Mốc so sánh có ba lựa chọn 2030, 2040 và 2050. Khi đổi mốc, vị trí đánh dấu, giá trị trên thẻ và đường dọc của biểu đồ thay đổi; các đường kịch bản vẫn giữ toàn giai đoạn 2025–2050.

### 5.6.2. Biểu đồ nhiệt độ lịch sử và các đường kịch bản

Đường lịch sử sử dụng trung bình trượt 5 năm của nhiệt độ thực tế, vẽ nét liền màu đậm. Ba kịch bản mặc định dùng nét đứt với màu riêng: cam–đỏ cho tiếp diễn, vàng nâu cho giữ mức 2024 và xanh lá cho giảm 5%/năm. Kịch bản tùy chỉnh dùng màu tím.

Vùng sau năm 2024 được phân biệt bằng nền nhạt và đường phân cách để không trộn quan sát lịch sử với mô phỏng tương lai. Kịch bản đang chọn được vẽ đậm hơn; điểm và nhãn tại mốc so sánh giúp đọc trực tiếp kết quả mà không phải ước lượng bằng mắt trên trục.

Vùng mờ quanh đường đang chọn biểu diễn khoảng dự đoán 90% xấp xỉ của kịch bản đó. Không hiểu vùng mờ là miền bao trùm tất cả kịch bản hoặc toàn bộ sự bất định của khí hậu. Khi chọn kịch bản khác, vùng mờ chuyển theo kịch bản đang xem.

### 5.6.3. Cách tính khoảng dự đoán

Gọi n = 51 là số quan sát dùng để huấn luyện lại; x̄ là trung bình CO₂ tích lũy sau đổi đơn vị; Sxx là tổng bình phương độ lệch của x so với x̄; s là sai số phần dư của mô hình huấn luyện lại. Khoảng dự đoán tại đầu vào x* được tính bằng:

```text
Sxx = Σ (xᵢ − x̄)²
s = √[Σ (yᵢ − ŷᵢ)² / (n − 2)]

Khoảng 90% = ŷ* ± t(0,95; n − 2) × s × √[1 + 1/n + (x* − x̄)²/Sxx]
```

Hai tham số được ước lượng là hệ số chặn và hệ số góc nên bậc tự do là n − 2 = 49. Trong kết quả hiện tại, s xấp xỉ **0,0435055 °C** và phân vị t xấp xỉ **1,6765509**. Số hạng 1 trong căn thức tương ứng với khoảng dự đoán cho một giá trị mục tiêu, khác với khoảng tin cậy chỉ cho giá trị trung bình của đường hồi quy.

Công thức dựa trên các giả định hồi quy, gồm quan hệ tuyến tính, sai số độc lập, phương sai ổn định và giả định phân phối thích hợp để dùng phân vị t. Dữ liệu đã làm trơn có liên hệ giữa các năm, nên khoảng này được ghi rõ là **xấp xỉ**; chưa có cơ sở khẳng định độ phủ thực tế đạt đúng 90%.

Khoảng dự đoán được tính với đường CO₂ của từng kịch bản coi như đã xác định. Nó chưa cộng thêm bất định về chính đường CO₂ tương lai, cấu trúc mô hình hoặc các yếu tố khí hậu bị bỏ qua. [Khoảng dự đoán trong hồi quy theo kịch bản](https://otexts.com/fpp3/forecasting-regression.html)

### 5.6.4. Biểu đồ CO₂ và biểu đồ kiểm tra

Biểu đồ CO₂ hằng năm giúp người xem hiểu nguyên nhân các đường mô phỏng nhiệt độ tách nhau: đầu vào CO₂ tiếp tục tăng, giữ nguyên hoặc giảm theo giả định. Trục tung của biểu đồ này là tỷ tấn CO₂ mỗi năm, không phải CO₂ tích lũy và cũng không phải nồng độ khí quyển.

Biểu đồ kiểm tra thể hiện hai đường trên 2015–2024: trung bình trượt 5 năm thực tế và dự đoán từ mô hình chỉ huấn luyện đến 2014. Nét liền–nét đứt và điểm quan sát hỗ trợ nhận biết năm mô hình dự đoán cao hoặc thấp hơn mục tiêu. Biểu đồ này không thay đổi khi người dùng điều chỉnh kịch bản tương lai, vì phép kiểm tra lịch sử đã được xác định riêng.

### 5.6.5. Diễn giải kết quả trên dashboard

Theo mô hình hiện tại, giảm tốc độ CO₂ giúp nhiệt độ dự đoán ở cùng mốc thấp hơn kịch bản tiếp diễn. Tuy nhiên, đường nhiệt độ của kịch bản giảm 5%/năm vẫn tăng trong giai đoạn mô phỏng. Điều này phù hợp với công thức đang sử dụng: CO₂ hằng năm còn dương, CO₂ tích lũy tiếp tục tăng và hệ số hồi quy β₁ dương.

Do đó, “thấp hơn tiếp diễn” không đồng nghĩa “thấp hơn năm 2024”. Cần phân biệt mức nhiệt độ tại một mốc với chênh lệch giữa hai kịch bản tại cùng mốc. Giao diện thể hiện hai thông tin này bằng hai thẻ riêng để hạn chế nhầm lẫn.

Tất cả nhiệt độ dùng mốc 1951–1980. Không đối chiếu trực tiếp các con số này với ngưỡng được xác định theo một thời kỳ cơ sở khác khi chưa chuyển đổi mốc tham chiếu. Kết quả cũng không phải nhiệt độ tuyệt đối của Trái Đất.

## 5.7. Hạn chế của mô hình (Khang)

### 5.7.1. Số lượng quan sát và cách chia dữ liệu

Sau khi tạo trung bình trượt, dữ liệu chỉ còn 51 quan sát năm. Tập kiểm tra chính có mười quan sát và chỉ đại diện cho giai đoạn 2015–2024. Các phép đối chiếu bổ sung cho thấy sai số thay đổi theo giai đoạn, nên chưa thể khẳng định mô hình có cùng chất lượng ở mọi thời kỳ hoặc mọi độ dài dự báo.

Phiên bản chương trình hiện lưu một phép chia huấn luyện–kiểm tra cố định. Việc mở rộng đánh giá theo nhiều mốc thời gian và so sánh với các mô hình tham chiếu đơn giản là hướng phát triển, không được trình bày như một chức năng đánh giá tự động đã tích hợp đầy đủ trong dashboard.

### 5.7.2. Mục tiêu đã được làm trơn

Mô hình dự đoán trung bình trượt 5 năm nên không mô tả trực tiếp các đợt biến động riêng của một năm. Sai số nhỏ trên chuỗi đã làm trơn không thể được dùng làm bằng chứng rằng nhiệt độ hằng năm cũng có sai số nhỏ tương tự.

Các cửa sổ trượt liên tiếp dùng chung bốn năm thành phần. Điều này làm giảm tính độc lập của quan sát và tạo dấu hiệu liên hệ giữa sai số các năm. Khi xét khoảng dự đoán hoặc độ tin cậy của hệ số, không thể bỏ qua đặc điểm này chỉ vì R² tương đối cao.

### 5.7.3. Mô hình chỉ có một biến giải thích

Quan hệ tuyến tính giữa CO₂ tích lũy và xu hướng nhiệt độ là một cách mô tả thống kê đơn giản. Mô hình không đưa trực tiếp vào các yếu tố như khí nhà kính khác, aerosol, đại dương, núi lửa hoặc dao động khí hậu tự nhiên. CO₂ và nhiệt độ còn cùng có xu hướng theo thời gian; sự phù hợp của đường hồi quy chưa đủ để chứng minh hệ số là tác động nhân quả riêng của CO₂.

Biến CO₂ sử dụng trong dự án không bao gồm toàn bộ mọi nguồn CO₂ hoặc mọi tác nhân gây thay đổi khí hậu. Vì vậy, phương trình không thay thế được mô hình vật lý hoặc các đánh giá khí hậu chuyên ngành.

### 5.7.4. Kiểm tra lịch sử khác với dự đoán thật sự trong tương lai

Ở tập kiểm tra, CO₂ tích lũy của từng năm đã được biết từ nguồn. Trong tương lai, đường CO₂ phải được giả định hoặc dự đoán. Sai số của giả định đầu vào này chưa được thể hiện trong R² = 0,835 hay MAE = 0,031 °C.

Ba tốc độ mặc định cũng không thay đổi theo năm trong cùng kịch bản. Hệ thống chưa mô tả các lộ trình gồm nhiều giai đoạn, các cú sốc kinh tế hay những thay đổi chính sách cụ thể. Tên “tiếp diễn” chỉ chỉ phép kéo dài tốc độ lịch sử đã chọn, không phải khẳng định đây là con đường có xác suất xảy ra cao nhất.

### 5.7.5. Ngoại suy dài hạn và khoảng dự đoán

Các đầu vào đến 2050 nằm ngoài miền CO₂ tích lũy đã dùng để huấn luyện. Việc kéo dài quan hệ tuyến tính thêm nhiều năm giả định rằng quan hệ thống kê lịch sử vẫn tiếp tục phù hợp. Mô hình chưa chứng minh được giả định đó bằng dữ liệu quan trắc tương lai.

Dải 90% trên biểu đồ là kết quả của công thức hồi quy có điều kiện, không phải chứng nhận “mô hình chính xác 90%”. Dải này chưa được hiệu chỉnh để bảo đảm độ phủ trong chuỗi có sai số liên hệ theo thời gian, cũng chưa chứa toàn bộ bất định dữ liệu, giả định CO₂ và cấu trúc mô hình.

### 5.7.6. Giới hạn dữ liệu và phạm vi triển khai

Bộ nguồn có thể được cơ quan cung cấp cập nhật hoặc điều chỉnh lại giá trị lịch sử. Kết quả của báo cáo gắn với bản dữ liệu lưu trong dự án. Khi thay nguồn, cần chạy lại các bước ghép, kiểm tra và huấn luyện thay vì giữ nguyên hệ số cũ rồi ghép với dữ liệu mới.

Mô hình chỉ áp dụng cho chuỗi toàn cầu. Lựa chọn quốc gia trên các trang dữ liệu không biến phương trình này thành mô hình riêng của quốc gia đó. Những quan sát nhiệt độ được nguồn ước tính và các khác biệt định nghĩa giữa NASA, FAOSTAT, OWID và EDGAR cũng cần được giữ trong giới hạn diễn giải chung của đồ án.

### 5.7.7. Kết luận về mô hình

Trong phạm vi đồ án, hồi quy tuyến tính đáp ứng mục tiêu xây dựng một mô hình dễ theo dõi, có kiểm tra theo thời gian và có kết quả tích hợp vào dashboard. Với giai đoạn kiểm tra 2015–2024, mô hình đạt **R² = 0,835**, **MAE = 0,031 °C** và **RMSE = 0,036 °C** khi ước tính nhiệt độ trung bình trượt 5 năm từ CO₂ tích lũy đã biết.

Giá trị sử dụng chính của mô hình là hỗ trợ so sánh kết quả giữa các giả định CO₂ bằng một quy trình thống nhất. Các đường đến 2050 cần được gọi là **kết quả mô phỏng thống kê theo kịch bản**, không phải dự báo khí hậu chính thức hoặc cam kết về nhiệt độ tương lai.

## Phụ lục. Tệp đối chiếu và tài liệu tham khảo

### A. Mã nguồn và dữ liệu đối chiếu trong dự án

Các liên kết dưới đây trỏ đến tệp hiện có trong repository. Số liệu của báo cáo gắn với phiên bản ghi ở đầu tài liệu; việc cập nhật các tệp nguồn sau này có thể làm thay đổi kết quả.

| Nội dung báo cáo | Tệp đối chiếu | Thành phần chính |
| --- | --- | --- |
| Chuẩn hóa nhiệt độ | [Làm sạch dữ liệu của Đức](../../phan_tich_nhiet_do/duc/lam_sach_du_lieu.py) | Đọc NASA, lọc FAOSTAT, chuyển mã, giữ bảng tháng riêng |
| Chuẩn hóa CO₂ và năng lượng | [Làm sạch dữ liệu của Quân](../../phan_tich_co2/quan/lam_sach_du_lieu.py) | Tách chuỗi toàn cầu, bảng quốc gia, ngành và năng lượng |
| Ghép bảng và kiểm tra khóa | [Ghép dữ liệu](../../mo_hinh_du_doan/nguyen_khang/ghep_du_lieu.py) | `build_country_year()`, `build_global_year()`, `_assert_unique()` |
| Khóa chính, khóa ngoại và JOIN | [Tạo cơ sở dữ liệu](../../mo_hinh_du_doan/nguyen_khang/tao_co_so_du_lieu.py), [sơ đồ dữ liệu](../dung_chung/SO_DO_DU_LIEU.md) | Định nghĩa tám bảng, hai view và danh mục dùng chung |
| Bảng quốc gia sau ghép | [CSV quốc gia–năm](../../data/du_lieu_da_xu_ly/nguyen_khang/dashboard_quoc_gia_nam.csv), [báo cáo ghép](../../data/du_lieu_da_xu_ly/nguyen_khang/bao_cao_ghep_du_lieu.json) | Khóa ghép, số dòng, độ phủ và giá trị chỉ tiêu |
| Chuỗi toàn cầu | [CSV khí hậu toàn cầu](../../data/du_lieu_da_xu_ly/nguyen_khang/khi_hau_toan_cau_nam.csv) | Đối chiếu ở mục 4.3 và đầu vào mô hình |
| Cơ sở dữ liệu đối chiếu | [SQLite](../../data/du_lieu_da_xu_ly/nguyen_khang/climate_lab.db) | Kiểm tra tính toàn vẹn, khóa ngoại và kết quả hai view |
| Bộ lọc và tổng hợp | [Dữ liệu dashboard](../../bang_dieu_khien/nguyen_khang/du_lieu.py) | `loc_du_lieu()`, `tong_hop_du_lieu()`, `loc_du_lieu_nganh()`, `loc_du_lieu_thang()` |
| Giao diện, luồng thao tác và CSV | [Ứng dụng dashboard](../../bang_dieu_khien/nguyen_khang/ung_dung.py) | Tạo trang, cập nhật bộ lọc, mở rộng, bảng dữ liệu và xuất tệp |
| Bản đồ và biểu đồ tổng quan, mô hình | [Biểu đồ dashboard](../../bang_dieu_khien/nguyen_khang/bieu_do.py), [tương tác địa cầu](../../bang_dieu_khien/nguyen_khang/tai_nguyen/dia_cau.js) | Phép chiếu, thang màu, chọn quốc gia, đường kịch bản và kiểm tra |
| Biểu đồ phân tích thành viên | [Plotly của Đức](../../phan_tich_nhiet_do/duc/tao_bieu_do_plotly.py), [Plotly của Quân](../../phan_tich_co2/quan/tao_bieu_do_plotly.py) | `build_figures()` dùng chung với dashboard; `main()` xuất HTML |
| Huấn luyện và kịch bản | [Mô hình nhiệt độ](../../mo_hinh_du_doan/nguyen_khang/mo_hinh_nhiet_do.py) | Chia năm, `LinearRegression`, chỉ số đánh giá và `tao_kich_ban()` |
| Kết quả mô hình | [Thông số JSON](../../data/ket_qua_mo_hinh/nguyen_khang/thong_tin_mo_hinh.json), [CSV kiểm tra](../../data/ket_qua_mo_hinh/nguyen_khang/du_doan_kiem_tra.csv), [CSV kịch bản](../../data/ket_qua_mo_hinh/nguyen_khang/kich_ban_2050.csv) | Các bảng số liệu ở mục 5.4–5.6 |
| Kiểm thử tự động | [Kiểm thử pipeline và dashboard](../../bang_dieu_khien/nguyen_khang/kiem_thu/test_pipeline.py) | Dữ liệu, mô hình, các trang, biểu đồ thành viên và tương tác bản đồ |

Hệ số tương quan tại mục 4.3.4 và bảng MAE theo giai đoạn tại mục 5.4.4 được tính bổ sung từ CSV toàn cầu trong quá trình đối chiếu báo cáo. Chúng không thay đổi thông số lưu trong JSON hay kết quả đang hiển thị trên dashboard. Với bảng MAE bổ sung, dữ liệu được sắp xếp theo năm, tính trung bình trượt lùi 5 năm, fit hồi quy trên các năm từ 1974 đến mốc kết thúc huấn luyện và kiểm tra năm năm kế tiếp; biến đầu vào vẫn là CO₂ tích lũy quan trắc chia cho 1.000.

### B. Tài liệu tham khảo

1. NASA Goddard Institute for Space Studies. [GISS Surface Temperature Analysis — GISTEMP v4](https://data.giss.nasa.gov/gistemp/). Nguồn và định nghĩa chuỗi nhiệt độ toàn cầu.
2. Food and Agriculture Organization of the United Nations. [FAOSTAT — Temperature Change on Land](https://www.fao.org/faostat/en/#data/ET). Nguồn nhiệt độ quốc gia theo năm và tháng.
3. Our World in Data. [CO₂ and Greenhouse Gas Emissions Dataset](https://github.com/owid/co2-data). Bộ dữ liệu, từ điển biến và nguồn CO₂, dân số.
4. European Commission, Joint Research Centre. [EDGAR — GHG Emissions of All World Countries, 2026 Report](https://edgar.jrc.ec.europa.eu/report_2026). Nguồn dữ liệu ngành; dự án chỉ chọn các bản ghi CO₂.
5. Our World in Data; nguồn dữ liệu UNSD, IEA và IRENA. [Share of Final Energy Consumption from Renewable Sources](https://ourworldindata.org/grapher/share-of-final-energy-consumption-from-renewable-sources). Định nghĩa tỷ trọng năng lượng tái tạo được sử dụng.
6. pandas Development Team. [pandas.DataFrame.merge](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.merge.html). Cách kết nối DataFrame và ý nghĩa các kiểu ghép.
7. scikit-learn Developers. [LinearRegression](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LinearRegression.html). Thuật toán hồi quy tuyến tính bình phương tối thiểu.
8. scikit-learn Developers. [r2_score](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.r2_score.html). Định nghĩa và giới hạn diễn giải hệ số R².
9. *Forecasting: Principles and Practice*, ấn bản 3. [Forecasting with Regression](https://otexts.com/fpp3/forecasting-regression.html). Biến đầu vào tương lai, dự báo theo kịch bản và giới hạn của khoảng dự đoán có điều kiện.

Các tài liệu bên ngoài được dùng để đối chiếu định nghĩa và phương pháp. Số lượng bản ghi, giá trị quan sát, chỉ số kiểm tra và các kết quả kịch bản trong báo cáo được tính từ bản dữ liệu của đồ án, không lấy từ số liệu cập nhật trực tiếp trên các trang tham khảo.
