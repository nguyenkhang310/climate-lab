# Insight phan Quan — CO2, nganh phat thai, nang luong tai tao

Nguon: 3 CSV trong `processed/` + bieu do mau `eda/quan/plotly/*.html` + EDA tinh `eda/quan/*.png`.
Don vi: OWID `co2` = Mt/nam (khong gom LUC), `co2_per_capita` = tan/nguoi;
EDGAR `Substance=CO2` = Mt CO2; `renewable_percent` = % tai tao trong **tong tieu thu
nang luong cuoi cung** (khong phai % dien tai tao).

## 1. Xu huong toan cau (1970-2024, dong World truc tiep)
- CO2 toan cau tang tu ~14.899 Mt (1970) len ~38.599 Mt (2024), gap **~2,6 lan**.
- Duong tang lien tuc, khong co diem dao chieu ben vung trong giai doan nay.

## 2. Tap trung phat thai (2023)
- Top 5: Trung Quoc (~12.172 Mt) > My (~4.918) > An Do (~3.063) > Nga (~1.733) > Nhat (~987).
- Trung Quoc mot minh ~ gap 2,5 lan My; tong top 5 chiem hon 60% toan cau.
- Xep hang theo tong CO2 va theo CO2/nguoi cho thu tu khac nhau -> dashboard can ca hai che do (da co trong bieu do mau 02/03).

## 3. Co cau nganh (EDGAR 2024, toan cau)
- Dien nang (Power Industry) **~40,8%** — dau moi giam phat thai.
- Giao thong ~18,7% + Dot cong nghiep ~16,0% = ~35% tiep theo.
- Nong nghiep (0,4%) + Chat thai (0,1%) trong EDGAR chi tinh CO2 (khong gom CH4/N2O)
  nen ty trong thap — **khong doc la "nong nghiep khong dang ke"** khi noi ve KNK tong.
- Khong dung sheet `GHG_totals_by_country` duoi nhan CO2 (do la CO2-tuong-duong).

## 4. CO2/nguoi vs nang luong tai tao (2023, n=212, r ≈ -0,49)
- Tuong quan am vua: quoc gia co ty trong tai tao cao thuong co CO2/nguoi thap hon,
  nhung phan tan rong -> tai tao chi la mot manh ghep (cau truc kinh te, khi hau, muc
  song deu anh huong). Trung binh tai tao 2023 ~27,3%, trung vi ~18,3% (lech phai:
  nhieu nuoc nho dung sinh khoi truyen thong o muc rat cao).
- Day la moi lien he mo ta, khong phai nhan-qua.

## 5. Luu y chat luong cho Khang khi ghep dashboard
- Ghep bang `iso_alpha + year`; 2024 thieu nang luong tai tao (84/225 nuoc) -> bo loc
  mac dinh co tai tao nen dung **1990-2023**.
- `ATA` (OWID) va `SCG` (EDGAR, Serbia and Montenegro lich su) co `continent=null`;
  giu lai, Khang left-join tu danh muc quoc gia va quyet dinh hien thi.
- Kosovo khong co ma ISO o ca OWID va renewable -> tach rieng, khong co trong 3 CSV.
- Chi tiet day du: `processed/quan_data_quality.json`.
