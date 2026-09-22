from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DUC = ROOT / "processed" / "duc"
QUAN = ROOT / "processed" / "quan"
OUT = ROOT / "processed" / "nguyen_khang"

START_YEAR = 1970
END_YEAR = 2024

def _assert_unique(frame: pd.DataFrame, keys: list[str], name: str) -> None:
    duplicates = int(frame.duplicated(keys).sum())
    if duplicates:
        raise ValueError(f"{name} có {duplicates} khóa trùng trên {keys}")

def build_country_year() -> tuple[pd.DataFrame, dict]:
    temperature = pd.read_csv(DUC / "nhiet_do_quoc_gia.csv")
    co2 = pd.read_csv(QUAN / "co2_quoc_gia.csv")
    renewable = pd.read_csv(QUAN / "nang_luong_tai_tao.csv")

    _assert_unique(temperature, ["iso_alpha", "year"], "Nhiệt độ quốc gia")
    _assert_unique(co2, ["iso_alpha", "year"], "CO₂ quốc gia")
    _assert_unique(renewable, ["iso_alpha", "year"], "Năng lượng tái tạo")

    temperature = temperature.rename(columns={
        "country": "country_temperature",
        "continent": "continent_temperature",
    })[[
        "iso_alpha", "year", "country_temperature", "continent_temperature",
        "temperature_anomaly", "source_flag",
    ]]
    co2 = co2.rename(columns={
        "country": "country_co2",
        "continent": "continent_co2",
    })[[
        "iso_alpha", "year", "country_co2", "continent_co2",
        "co2", "co2_per_capita", "population",
    ]]
    renewable = renewable.rename(columns={"country": "country_renewable"})

    merged = temperature.merge(co2, on=["iso_alpha", "year"], how="outer")
    merged = merged.merge(renewable, on=["iso_alpha", "year"], how="outer")
    merged["country"] = (
        merged["country_temperature"]
        .combine_first(merged["country_co2"])
        .combine_first(merged["country_renewable"])
    )
    merged["continent"] = merged["continent_temperature"].combine_first(
        merged["continent_co2"]
    )
    merged.loc[merged["iso_alpha"] == "ATA", "continent"] = "Antarctica"
    merged["decade"] = (merged["year"] // 10 * 10).astype(int)

    columns = [
        "country", "iso_alpha", "continent", "year", "decade",
        "temperature_anomaly", "co2", "co2_per_capita", "population",
        "renewable_percent", "source_flag",
    ]
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
            for column in [
                "temperature_anomaly", "co2", "co2_per_capita",
                "population", "renewable_percent",
            ]
        },
        "countries_with_data": {
            column: int(result.loc[result[column].notna(), "iso_alpha"].nunique())
            for column in [
                "temperature_anomaly", "co2", "co2_per_capita",
                "population", "renewable_percent",
            ]
        },
        "join_strategy": (
            "Full outer join theo iso_alpha + year; giữ null, không nội suy và "
            "không thay giá trị thiếu bằng 0."
        ),
    }
    return result, report

def build_global_year() -> pd.DataFrame:
    temperature = pd.read_csv(DUC / "nhiet_do_toan_cau.csv")
    co2 = pd.read_csv(QUAN / "co2_toan_cau.csv")
    result = temperature.merge(co2, on=["year", "decade"], how="inner")
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
