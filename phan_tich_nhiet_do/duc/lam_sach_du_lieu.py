import json
import sys
from calendar import month_abbr, month_name
from pathlib import Path

import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data/du_lieu_goc/duc"
OUT = ROOT / "data/du_lieu_da_xu_ly/duc"
REFERENCE = ROOT / "data/du_lieu_goc/dung_chung"

NASA_RAW = RAW / "nasa_nhiet_do_toan_cau_1880_2026.csv"
FAO_RAW = RAW / "faostat_nhiet_do_quoc_gia_1961_2025.csv"
M49_REF = REFERENCE / "un_m49_iso3.csv"
OWID_CONTINENT = REFERENCE / "owid_quoc_gia_chau_luc.csv"

DATA_DICTIONARY = {
    "nhiet_do_toan_cau.csv": {
        "year": "Năm quan sát (1880–2025). Năm 2026 chưa đủ 12 tháng nên được loại bỏ.",
        "decade": "Thập kỷ quan sát = (year // 10) * 10 (ví dụ 2020s là 2020–2025).",
        "temperature_anomaly": "Độ lệch nhiệt độ trung bình năm toàn cầu (°C) so với thời kỳ cơ sở 1951–1980 (NASA GISTEMP v4, cột J-D)."
    },
    "nhiet_do_theo_thang.csv": {
        "iso_alpha": "Mã ISO3 của quốc gia (FAOSTAT); WLD là chuỗi toàn cầu NASA GISTEMP.",
        "year": "Năm quan sát, không dùng năm 2026 chưa hoàn chỉnh.",
        "month": "Tháng 1–12; khóa bảng: iso_alpha + year + month.",
        "temperature_anomaly": "Chênh nhiệt độ tháng (°C) so với cùng tháng giai đoạn 1951–1980; giữ nguyên giá trị thiếu.",
        "source_flag": "Cờ nguồn FAOSTAT; để trống với NASA."
    },
    "nhiet_do_quoc_gia.csv": {
        "country": "Tên quốc gia / lãnh thổ chuẩn hóa (theo danh mục OWID / ISO-3166).",
        "iso_alpha": "Mã quốc gia chuẩn ISO-3166-1 alpha-3 (3 ký tự viết hoa), dùng làm khóa ghép bảng chính cùng cột year.",
        "continent": "Châu lục theo OWID và UN M49; ATA được gán Antarctica.",
        "year": "Năm khí tượng (tháng 12 năm trước đến tháng 11 năm đang xét), 1961–2025.",
        "decade": "Thập kỷ quan sát = (year // 10) * 10.",
        "temperature_anomaly": "Độ lệch nhiệt độ trên đất liền (°C) so với thời kỳ cơ sở 1951–1980 (FAOSTAT Temperature change on land, Meteorological year).",
        "source_flag": "Cờ FAOSTAT giữ nguyên: E = Estimated value. Cờ trống không chứng minh quan sát trực tiếp."
    },
    "nhiet_do_quoc_gia_nam_lich.csv": {
        "year": "Năm lịch tháng 1–12, dùng khi ghép với CO₂ và năng lượng tái tạo.",
        "temperature_anomaly": "Trung bình chênh nhiệt độ 12 tháng FAOSTAT so với 1951–1980; null nếu thiếu bất kỳ tháng nào.",
        "months_available": "Số tháng có giá trị, từ 0 đến 12; chỉ tính nhiệt độ năm khi đủ 12 tháng.",
        "source_flag": "Các cờ FAOSTAT của 12 tháng dùng để tính năm; trống nếu không đủ 12 tháng.",
        "country": "Tên quốc gia giống bảng năm khí tượng.",
        "iso_alpha": "ISO3, khóa ghép cùng year.",
        "continent": "Châu lục giống bảng năm khí tượng.",
        "decade": "Thập kỷ = (year // 10) * 10."
    }
}


def clean_nasa() -> tuple[pd.DataFrame, dict]:
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
    df_clean["continent"] = df_clean["iso_alpha"].map(iso_to_cont).fillna(
        df_clean["iso_alpha"].map(m49_df.set_index("iso_alpha")["continent"]))
    df_clean.loc[df_clean.iso_alpha.eq("ATA"), "continent"] = "Antarctica"
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


def clean_monthly() -> pd.DataFrame:
    nasa = pd.read_csv(NASA_RAW, header=1, na_values="***")
    nasa = nasa[nasa.Year <= 2025].melt(id_vars="Year", value_vars=list(month_abbr)[1:],
                                      var_name="month", value_name="temperature_anomaly")
    nasa = nasa.rename(columns={"Year": "year"}).assign(iso_alpha="WLD")
    nasa["month"] = nasa.month.map({name: i for i, name in enumerate(month_abbr)})
    fao = pd.read_csv(FAO_RAW, usecols=["Area Code (M49)", "Year", "Months", "Element", "Value", "Flag"])
    fao = fao[fao.Element.eq("Temperature change") & fao.Months.isin(list(month_name)[1:])].copy()
    codes = pd.read_csv(M49_REF, dtype=str).set_index("m49").iso_alpha
    fao["iso_alpha"] = fao["Area Code (M49)"].str.replace("'", "", regex=False).str.zfill(3).map(codes)
    fao["month"] = fao.Months.map({name: i for i, name in enumerate(month_name)})
    fao = fao.rename(columns={"Year": "year", "Value": "temperature_anomaly", "Flag": "source_flag"})
    keys = ["iso_alpha", "year", "month"]
    out = pd.concat([nasa, fao.dropna(subset=["iso_alpha"])])[keys + ["temperature_anomaly", "source_flag"]]
    out["temperature_anomaly"] = pd.to_numeric(out.temperature_anomaly, errors="coerce")
    out = out[out.year <= 2025].sort_values(keys).reset_index(drop=True)
    if out.duplicated(keys).any():
        raise ValueError("Dữ liệu nhiệt độ tháng trùng khóa quốc gia, năm, tháng.")
    out.to_csv(OUT / "nhiet_do_theo_thang.csv", index=False)
    return out


def clean_calendar_year(countries: pd.DataFrame, monthly: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    national = monthly[monthly.iso_alpha.ne("WLD")]
    if national.duplicated(["iso_alpha", "year", "month"]).any():
        raise ValueError("Không thể tính năm lịch từ các tháng trùng khóa.")
    if not national.month.between(1, 12).all():
        raise ValueError("Tháng phải nằm trong khoảng 1–12.")
    annual = national.groupby(["iso_alpha", "year"], as_index=False).agg(
        temperature_anomaly=("temperature_anomaly", "mean"),
        months_available=("temperature_anomaly", "count"),
        source_flag=("source_flag", lambda flags: ",".join(sorted(flags.dropna().unique()))),
    )
    complete = annual.months_available.eq(12)
    annual["temperature_anomaly"] = annual.temperature_anomaly.where(complete)
    annual["source_flag"] = annual.source_flag.where(complete)
    out = countries[["country", "iso_alpha", "continent", "year", "decade"]].merge(
        annual, on=["iso_alpha", "year"], how="left", validate="one_to_one",
    ).sort_values(["iso_alpha", "year"]).reset_index(drop=True)
    out["months_available"] = out.months_available.fillna(0).astype(int)
    out.to_csv(OUT / "nhiet_do_quoc_gia_nam_lich.csv", index=False)
    stats = {
        "rows_output": len(out), "year_min": int(out.year.min()), "year_max": int(out.year.max()),
        "complete_years": int(out.temperature_anomaly.notna().sum()),
        "incomplete_years": int(out.temperature_anomaly.isna().sum()),
        "year_basis": "January–December; required 12 valid monthly values; no imputation",
    }
    return out, stats


def export_quality_report(nasa_stats: dict, fao_stats: dict, calendar_stats: dict | None = None) -> None:
    report = {
        "data_dictionary": DATA_DICTIONARY,
        "duc_nhiet_do_toan_cau": nasa_stats,
        "duc_nhiet_do_quoc_gia": fao_stats,
        "duc_nhiet_do_quoc_gia_nam_lich": calendar_stats,
        "methodology_notes": {
            "m49_to_iso3": "Dùng bảng UN M49 numeric sang ISO3. 156 (China, mainland) -> CHN ('China'). Tách riêng HKG, MAC, TWN và 52 vùng tổng hợp.",
            "baseline": "Baseline 1951–1980 (0°C) cho cả NASA GISTEMP và FAOSTAT.",
            "join_key": "iso_alpha + year",
            "year_basis": "NASA J-D và bảng năm lịch: tháng 1–12. FAOSTAT Meteorological year: tháng 12 năm trước đến tháng 11. Bảng ghép dùng nhiet_do_quoc_gia_nam_lich.csv."
        }
    }
    with open(OUT / "bao_cao_chat_luong.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    df_nasa, nasa_stats = clean_nasa()
    df_fao, fao_stats = clean_faostat()
    monthly = clean_monthly()
    _, calendar_stats = clean_calendar_year(df_fao, monthly)
    export_quality_report(nasa_stats, fao_stats, calendar_stats)
    print(f"OK: NASA ({len(df_nasa)} dòng), FAOSTAT ({len(df_fao)} dòng, {df_fao['iso_alpha'].nunique()} nước). Đã xuất bao_cao_chat_luong.json.")


if __name__ == "__main__":
    main()
