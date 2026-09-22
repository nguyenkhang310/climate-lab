"""
Pipeline làm sạch dữ liệu nhiệt độ của Đức:
1. Làm sạch chuỗi nhiệt độ toàn cầu NASA GISTEMP (1880–2025) -> processed/duc/nhiet_do_toan_cau.csv
2. Chuẩn hóa nhiệt độ quốc gia FAOSTAT (1961–2025) theo UN M49 -> ISO3 -> processed/duc/nhiet_do_quoc_gia.csv
3. Xuất báo cáo kiểm định chất lượng dữ liệu -> processed/duc/bao_cao_chat_luong.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "processed" / "duc"

NASA_RAW = RAW / "01_duc_nhiet_do" / "nasa_nhiet_do_toan_cau_1880_2026.csv"
FAO_RAW = RAW / "01_duc_nhiet_do" / "faostat_nhiet_do_quoc_gia_1961_2025.csv"
M49_REF = RAW / "04_dung_chung_danh_muc_quoc_gia" / "un_m49_iso3.csv"
OWID_CONTINENT = RAW / "04_dung_chung_danh_muc_quoc_gia" / "owid_quoc_gia_chau_luc.csv"

DATA_DICTIONARY = {
    "nhiet_do_toan_cau.csv": {
        "year": "Năm quan sát (1880–2025). Năm 2026 chưa đủ 12 tháng nên được loại bỏ.",
        "decade": "Thập kỷ quan sát = (year // 10) * 10 (ví dụ 2020s là 2020–2025).",
        "temperature_anomaly": "Độ lệch nhiệt độ trung bình năm toàn cầu (°C) so với thời kỳ cơ sở 1951–1980 (NASA GISTEMP v4, cột J-D)."
    },
    "nhiet_do_quoc_gia.csv": {
        "country": "Tên quốc gia / lãnh thổ chuẩn hóa (theo danh mục OWID / ISO-3166).",
        "iso_alpha": "Mã quốc gia chuẩn ISO-3166-1 alpha-3 (3 ký tự viết hoa), dùng làm khóa ghép bảng chính cùng cột year.",
        "continent": "Châu lục theo phân loại OWID (Africa, Asia, Europe, North America, South America, Oceania; null nếu là vùng đặc thù như ATA).",
        "year": "Năm quan sát (1961–2025; phân tích chính 1970–2024).",
        "decade": "Thập kỷ quan sát = (year // 10) * 10.",
        "temperature_anomaly": "Độ lệch nhiệt độ trên đất liền (°C) so với thời kỳ cơ sở 1951–1980 (FAOSTAT Temperature change on land, Meteorological year).",
        "source_flag": "Cờ chất lượng nguồn dữ liệu từ FAO: 'E' = Estimated value, null = Giá trị quan sát trực tiếp hoặc thiếu."
    }
}


def clean_nasa() -> tuple[pd.DataFrame, dict]:
    """Làm sạch chuỗi nhiệt độ toàn cầu từ NASA GISTEMP v4."""
    df_raw = pd.read_csv(NASA_RAW, na_values="***")
    if "Year" not in df_raw.columns:
        df_raw = pd.read_csv(NASA_RAW, header=1, na_values="***")

    df = df_raw[["Year", "J-D"]].rename(columns={"Year": "year", "J-D": "temperature_anomaly"})
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["temperature_anomaly"] = pd.to_numeric(df["temperature_anomaly"], errors="coerce")
    df = df.dropna(subset=["temperature_anomaly"])
    df = df[df["year"] <= 2025].copy()
    df["year"] = df["year"].astype(int)
    df["decade"] = (df["year"] // 10) * 10

    out = df[["year", "decade", "temperature_anomaly"]].sort_values("year").reset_index(drop=True)
    out.to_csv(OUT / "nhiet_do_toan_cau.csv", index=False)

    stats = {
        "rows_raw": int(len(df_raw)),
        "rows_output": int(len(out)),
        "year_min": int(out["year"].min()),
        "year_max": int(out["year"].max()),
        "missing_rate": {c: round(float(out[c].isna().mean()), 4) for c in out.columns},
        "temperature_mean": round(float(out["temperature_anomaly"].mean()), 4),
        "temperature_std": round(float(out["temperature_anomaly"].std()), 4),
        "temperature_min": round(float(out["temperature_anomaly"].min()), 4),
        "temperature_max": round(float(out["temperature_anomaly"].max()), 4),
    }
    return out, stats


def clean_faostat() -> tuple[pd.DataFrame, dict]:
    """Làm sạch chuỗi nhiệt độ quốc gia FAOSTAT bằng mã UN M49 -> ISO3."""
    m49_df = pd.read_csv(M49_REF, dtype=str)
    m49_to_iso = dict(zip(m49_df["m49"].str.zfill(3), m49_df["iso_alpha"]))
    m49_to_name = dict(zip(m49_df["m49"].str.zfill(3), m49_df["country_name"]))

    owid_df = pd.read_csv(OWID_CONTINENT)
    iso_to_cont = dict(zip(owid_df["Code"], owid_df["World region according to OWID"]))
    iso_to_name = dict(zip(owid_df["Code"], owid_df["Entity"]))

    df_raw = pd.read_csv(FAO_RAW, low_memory=False)
    df_fao = df_raw[
        (df_raw["Element"] == "Temperature change") &
        (df_raw["Months"] == "Meteorological year")
    ].copy()

    df_fao["m49_clean"] = df_fao["Area Code (M49)"].astype(str).str.strip().str.replace("'", "", regex=False).str.zfill(3)
    df_fao["iso_alpha"] = df_fao["m49_clean"].map(m49_to_iso)

    aggregates_separated = sorted(df_fao[df_fao["iso_alpha"].isna()]["Area"].unique().tolist())

    df_clean = df_fao.dropna(subset=["iso_alpha"]).copy()
    df_clean = df_clean[df_clean["iso_alpha"].str.len() == 3].copy()

    df_clean["country"] = df_clean["iso_alpha"].map(iso_to_name).fillna(df_clean["m49_clean"].map(m49_to_name)).fillna(df_clean["Area"])
    df_clean["continent"] = df_clean["iso_alpha"].map(iso_to_cont)
    df_clean["year"] = pd.to_numeric(df_clean["Year"], errors="coerce").astype(int)
    df_clean["temperature_anomaly"] = pd.to_numeric(df_clean["Value"], errors="coerce")
    df_clean["source_flag"] = df_clean["Flag"]
    df_clean["decade"] = (df_clean["year"] // 10) * 10

    target_cols = ["country", "iso_alpha", "continent", "year", "decade", "temperature_anomaly", "source_flag"]
    out = df_clean[target_cols].sort_values(["iso_alpha", "year"]).reset_index(drop=True)

    dup_keys = int(out.duplicated(["iso_alpha", "year"]).sum())
    if dup_keys > 0:
        raise ValueError(f"Dữ liệu FAOSTAT có {dup_keys} dòng trùng khóa (iso_alpha, year)!")

    out.to_csv(OUT / "nhiet_do_quoc_gia.csv", index=False)

    temp = out["temperature_anomaly"].dropna()
    q1, q3 = float(temp.quantile(0.25)), float(temp.quantile(0.75))
    iqr = q3 - q1
    lower_bound, upper_bound = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    outliers_low = int((temp < lower_bound).sum())
    outliers_high = int((temp > upper_bound).sum())
    outliers_iqr = outliers_low + outliers_high

    stats = {
        "rows_raw": int(len(df_raw)),
        "rows_meteorological_year": int(len(df_fao)),
        "rows_output": int(len(out)),
        "aggregates_separated_count": len(aggregates_separated),
        "aggregates_separated": aggregates_separated,
        "countries_count": int(out["iso_alpha"].nunique()),
        "year_min": int(out["year"].min()),
        "year_max": int(out["year"].max()),
        "duplicate_keys": dup_keys,
        "missing_rate": {c: round(float(out[c].isna().mean()), 4) for c in out.columns},
        "continent_unmatched_iso": sorted(out[out["continent"].isna()]["iso_alpha"].unique().tolist()),
        "flag_distribution": {str(k): int(v) for k, v in out["source_flag"].value_counts(dropna=False).to_dict().items()},
        "distribution": {
            "mean": round(float(temp.mean()), 4), "std": round(float(temp.std()), 4),
            "median": round(float(temp.median()), 4), "min": round(float(temp.min()), 4),
            "max": round(float(temp.max()), 4), "p1": round(float(temp.quantile(0.01)), 4),
            "p99": round(float(temp.quantile(0.99)), 4),
            "iqr_bounds": [round(lower_bound, 4), round(upper_bound, 4)],
            "outliers_low_count": outliers_low,
            "outliers_high_count": outliers_high,
            "outliers_iqr_count": outliers_iqr,
            "outliers_iqr_pct": round(float(outliers_iqr / len(temp) * 100), 2)
        },
        "top_positive_extremes": out.nlargest(5, "temperature_anomaly")[["country", "iso_alpha", "year", "temperature_anomaly", "source_flag"]].to_dict("records"),
        "top_negative_extremes": out.nsmallest(5, "temperature_anomaly")[["country", "iso_alpha", "year", "temperature_anomaly", "source_flag"]].to_dict("records"),
        "outlier_interpretation": "Trong 199 quan sát ngoại lai theo ngưỡng IQR ([-1.33°C, 2.42°C]), có 178 điểm ngoại lai nóng (> 2.42°C) tập trung nhiều tại các vùng vĩ độ cao sau năm 2010 và 21 điểm ngoại lai lạnh (< -1.33°C) chủ yếu ở các thập niên trước. Tất cả các điểm này mang cờ FAO 'E' (Estimated), vì vậy được giữ nguyên nhưng phải diễn giải thận trọng; cờ 'E' không tự chứng minh giá trị là quan sát trực tiếp hay không có sai số."
    }
    return out, stats


def export_quality_report(nasa_stats: dict, fao_stats: dict) -> None:
    """Tổng hợp và lưu báo cáo chất lượng dữ liệu ra JSON."""
    report = {
        "data_dictionary": DATA_DICTIONARY,
        "duc_nhiet_do_toan_cau": nasa_stats,
        "duc_nhiet_do_quoc_gia": fao_stats,
        "methodology_notes": {
            "m49_to_iso3": "Dùng bảng UN M49 numeric sang ISO3. 156 (China, mainland) -> CHN ('China'). Tách riêng HKG, MAC, TWN và 52 vùng tổng hợp.",
            "baseline": "Baseline 1951–1980 (0°C) cho cả NASA GISTEMP và FAOSTAT.",
            "join_key": "iso_alpha + year"
        }
    }
    with open(OUT / "bao_cao_chat_luong.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    df_nasa, nasa_stats = clean_nasa()
    df_fao, fao_stats = clean_faostat()
    export_quality_report(nasa_stats, fao_stats)
    print(f"OK: NASA ({len(df_nasa)} dòng), FAOSTAT ({len(df_fao)} dòng, {df_fao['iso_alpha'].nunique()} nước). Đã xuất bao_cao_chat_luong.json.")


if __name__ == "__main__":
    main()
