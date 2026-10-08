import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data/du_lieu_da_xu_ly"
DUC = DATA / "duc"
QUAN = DATA / "quan"
OUT = DATA / "nguyen_khang"

# Bảng chung giữ CO₂ từ 1850; từng trang tự chọn giai đoạn phù hợp.
# Phép ghép toàn cầu chỉ giữ những năm có cả NASA và CO₂ (từ 1880).
START_YEAR = 1850
END_YEAR = 2024

def _assert_unique(frame: pd.DataFrame, keys: list[str], name: str) -> None:
    duplicates = int(frame.duplicated(keys).sum())
    if duplicates:
        raise ValueError(f"{name} có {duplicates} khóa trùng trên {keys}")

def build_country_year() -> tuple[pd.DataFrame, dict]:
    temperature = pd.read_csv(DUC / "nhiet_do_quoc_gia_nam_lich.csv")
    co2 = pd.read_csv(QUAN / "co2_quoc_gia.csv")
    renewable = pd.read_csv(QUAN / "nang_luong_tai_tao.csv")

    _assert_unique(temperature, ["iso_alpha", "year"], "Nhiệt độ quốc gia")
    _assert_unique(co2, ["iso_alpha", "year"], "CO₂ quốc gia")
    _assert_unique(renewable, ["iso_alpha", "year"], "Năng lượng tái tạo")

    co2 = co2[["iso_alpha", "year", "country", "continent", "co2", "co2_per_capita", "population"]]
    renewable = renewable.rename(columns={"country": "country_renewable"})

    merged = temperature.merge(co2, on=["iso_alpha", "year"], how="outer",
                               suffixes=("_temperature", "_co2"))
    merged = merged.merge(renewable, on=["iso_alpha", "year"], how="outer")
    merged["country"] = (
        merged.country_temperature.fillna(merged.country_co2).fillna(merged.country_renewable)
    )
    merged["continent"] = merged.continent_temperature.fillna(merged.continent_co2)
    reference = ROOT / "data/du_lieu_goc/dung_chung/un_m49_iso3.csv"
    regions = pd.read_csv(reference).set_index("iso_alpha").continent
    merged["continent"] = merged.continent.fillna(merged.iso_alpha.map(regions))
    merged.loc[merged["iso_alpha"] == "ATA", "continent"] = "Antarctica"
    merged["decade"] = (merged["year"] // 10 * 10).astype(int)

    indicators = ["temperature_anomaly", "co2", "co2_per_capita", "population", "renewable_percent"]
    columns = ["country", "iso_alpha", "continent", "year", "decade"] + indicators + ["source_flag"]
    result = (
        merged.loc[merged["year"].between(START_YEAR, END_YEAR), columns]
        .sort_values(["iso_alpha", "year"])
        .reset_index(drop=True)
    )
    _assert_unique(result, ["iso_alpha", "year"], "Bảng dashboard")

    report = {
        "period": [START_YEAR, END_YEAR],
        "rows": int(len(result)),
        "countries_or_territories": int(result["iso_alpha"].nunique()),
        "continents": sorted(result["continent"].dropna().unique().tolist()),
        "duplicate_keys": int(result.duplicated(["iso_alpha", "year"]).sum()),
        "coverage_non_null": {
            column: round(float(result[column].notna().mean()), 4)
            for column in indicators
        },
        "countries_with_data": {
            column: int(result.loc[result[column].notna(), "iso_alpha"].nunique())
            for column in indicators
        },
        "join_strategy": (
            "Full outer join theo iso_alpha + year; giữ null, không nội suy và "
            "không thay giá trị thiếu bằng 0."
        ),
        "temperature_year_basis": (
            "January–December; đủ 12 tháng FAOSTAT; cùng năm lịch với CO2 và tái tạo."
        ),
    }
    return result, report

def build_global_year() -> pd.DataFrame:
    temperature = pd.read_csv(DUC / "nhiet_do_toan_cau.csv")
    co2 = pd.read_csv(QUAN / "co2_toan_cau.csv")
    _assert_unique(temperature, ["year"], "Nhiệt độ toàn cầu")
    _assert_unique(co2, ["year"], "CO₂ toàn cầu")
    result = temperature.merge(co2, on=["year", "decade"], how="inner", validate="one_to_one")
    result = result[result["year"].between(START_YEAR, END_YEAR)].copy()
    _assert_unique(result, ["year"], "Chuỗi toàn cầu")
    return result.sort_values("year").reset_index(drop=True)

def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    country_year, report = build_country_year()
    global_year = build_global_year()

    country_year.to_csv(OUT / "dashboard_quoc_gia_nam.csv", index=False)
    global_year.to_csv(OUT / "khi_hau_toan_cau_nam.csv", index=False)
    (OUT / "bao_cao_ghep_du_lieu.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        f"OK: dashboard={country_year.shape}, global={global_year.shape}, "
        f"countries={country_year['iso_alpha'].nunique()}"
    )

if __name__ == "__main__":
    main()
