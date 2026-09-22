import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "processed" / "quan"
EDA = ROOT / "eda" / "quan"

OWID = RAW / "02_quan_phat_thai_co2" / "owid_phat_thai_co2_1750_2024.csv"
EDGAR = RAW / "02_quan_phat_thai_co2" / "edgar_phat_thai_theo_nganh_1970_2025.xlsx"
RENEW = RAW / "03_quan_nang_luong_tai_tao" / "un_ty_trong_nang_luong_tai_tao_1990_2024.csv"
CONTINENT = RAW / "04_dung_chung_danh_muc_quoc_gia" / "owid_quoc_gia_chau_luc.csv"

OWID_AGGREGATES_KEEP = {"World"}

EDGAR_EXCLUDE_COUNTRIES = {
    "GLOBAL TOTAL", "EU27", "International Aviation", "International Shipping",
}
EDGAR_EXCLUDE_CODES = {"AIR", "SEA"}

DATA_DICTIONARY = {
    "co2_quoc_gia.csv": {
        "country": "Tên quốc gia/lãnh thổ (OWID)",
        "iso_alpha": "Mã ISO3, khóa ghép cùng year",
        "continent": "Châu lục theo OWID (null nếu không ghép được: ATA)",
        "year": "Năm (1750–2024; phân tích chính 1970–2024)",
        "decade": "Thập kỷ = floor(year/10)*10 (2020–2024 là giai đoạn chưa đủ 10 năm)",
        "co2": "Phát thải CO₂ Mt/năm, không gồm thay đổi sử dụng đất (GCP qua OWID); null là thiếu",
        "co2_per_capita": "Tấn CO₂/người (không gồm LUC); null là thiếu",
        "co2_growth_pct": "Tăng trưởng CO₂ so với năm trước của cùng quốc gia (%/năm); "
                          "năm đầu tiên của mỗi chuỗi là null",
        "population": "Dân số (người); null là thiếu",
    },
    "co2_toan_cau.csv": {
        "year": "Năm (dòng World của OWID, 1750–2024)",
        "decade": "Thập kỷ = floor(year/10)*10",
        "co2": "Phát thải CO₂ toàn cầu Mt/năm (dòng World trực tiếp, không tự cộng)",
        "co2_per_capita": "Tấn CO₂/người toàn cầu",
        "population": "Dân số toàn cầu (người)",
        "cumulative_co2": "CO₂ tích lũy từ 1750 (Mt)",
    },
    "co2_theo_nganh.csv": {
        "country": "Tên quốc gia (EDGAR)",
        "iso_alpha": "Mã quốc gia EDGAR (tương đương ISO3), khóa ghép cùng year",
        "year": "Năm (1970–2025 dạng long; phân tích chính 1970–2024, 2025 là số sơ bộ)",
        "sector": "Ngành EDGAR: Power Industry, Industrial Combustion, Transport, "
                  "Buildings, Fuel Production, Agriculture, Processes, Waste",
        "co2": "Phát thải CO₂ Mt/năm của ngành (đã lọc Substance = CO2)",
        "sector_share_percent": "Tỷ trọng ngành trong tổng CO₂ quốc gia–năm (%)",
    },
    "nang_luong_tai_tao.csv": {
        "country": "Tên quốc gia",
        "iso_alpha": "Mã ISO3, khóa ghép cùng year",
        "year": "Năm (1990–2024; phân tích chính 1990–2023 vì 2024 chỉ có 84 nước)",
        "renewable_percent": "% năng lượng tái tạo trong tổng tiêu thụ năng lượng "
                             "cuối cùng (không phải % điện tái tạo)",
    },
}

def load_continent():
    c = pd.read_csv(CONTINENT)
    cmap = dict(zip(c["Code"], c["World region according to OWID"]))
    return cmap

def clean_owid(cmap):
    df = pd.read_csv(OWID, low_memory=False)
    n_raw = len(df)
    agg_rows = df[df["iso_code"].isna()]
    agg_names = sorted(agg_rows["country"].unique().tolist())
    world = df[df["country"] == "World"].copy()
    world["decade"] = (world["year"] // 10 * 10).astype(int)
    world_out = world[[
        "year", "decade", "co2", "co2_per_capita", "population",
        "cumulative_co2",
    ]].sort_values("year").reset_index(drop=True)

    keep = df[df["iso_code"].notna()].copy()
    keep = keep.rename(columns={"iso_code": "iso_alpha"})
    keep["continent"] = keep["iso_alpha"].map(cmap)
    keep["decade"] = (keep["year"] // 10 * 10).astype(int)
    keep = keep.sort_values(["iso_alpha", "year"])
    keep["co2_growth_pct"] = keep.groupby("iso_alpha")["co2"].pct_change(fill_method=None) * 100
    out = keep[[
        "country", "iso_alpha", "continent", "year", "decade",
        "co2", "co2_per_capita", "co2_growth_pct", "population",
    ]].reset_index(drop=True)

    unmatched = sorted(out[out["continent"].isna()]["iso_alpha"].unique().tolist())
    yoy = keep["co2_growth_pct"]

    flagged = keep[(keep["year"] >= 1970) & (keep["year"] <= 2024)].copy()
    flagged["delta_mt"] = flagged.groupby("iso_alpha")["co2"].diff()
    flagged = flagged[
        (flagged["co2_growth_pct"].abs() > 50)
        & (flagged["delta_mt"].abs() > 1)
        & flagged["co2"].notna()
    ].sort_values("delta_mt", key=abs, ascending=False)
    outlier_list = [
        {
            "country": r.country, "iso_alpha": r.iso_alpha, "year": int(r.year),
            "co2_mt": round(float(r.co2), 3),
            "tang_truong_pct": round(float(r.co2_growth_pct), 1),
            "chenh_lech_mt": round(float(r.delta_mt), 1),
        }
        for r in flagged.itertuples()
    ]
    zeros = sorted(out[(out["year"] >= 1970) & (out["co2"] == 0)]["country"].unique().tolist())

    report = {
        "rows_raw": int(n_raw),
        "rows_output": int(len(out)),
        "aggregates_separated": agg_names,
        "world_rows": int(len(world)),
        "countries": int(out["iso_alpha"].nunique()),
        "year_min": int(out["year"].min()), "year_max": int(out["year"].max()),
        "missing_rate": {k: round(float(v), 4) for k, v in out.isna().mean().to_dict().items()},
        "continent_unmatched_iso": unmatched,
        "co2_yoy_median_pct": round(float(yoy.median()), 3),
        "co2_yoy_p99_pct": round(float(yoy.quantile(0.99)), 3),
        "top_co2_2023": out[out["year"] == 2023].nlargest(5, "co2")[
            ["country", "iso_alpha", "co2"]].to_dict("records"),
        "outlier": {
            "quy_tac": [
                "O1. co2 < 0 là lỗi dữ liệu, loại khỏi phân tích.",
                "O2. Quốc gia phát thải lớn không phải outlier, giữ nguyên.",
                "O3. Biến động mạnh (|tăng trưởng| > 50% và |chênh lệch| > 1 Mt, "
                "giai đoạn 1970–2024) thì gắn cờ kiểm tra thủ công; giữ lại vì "
                "đều gắn với sự kiện lịch sử có thật.",
                "O4. co2 == 0 là giá trị gốc trong nguồn, giữ nguyên và phân "
                "biệt với thiếu dữ liệu (null).",
            ],
            "co2_am": {"so_dong": int((out["co2"] < 0).sum()), "quyet_dinh": "giữ"},
            "nuoc_phat_thai_lon": {
                "quyet_dinh": "giữ toàn bộ, không coi là outlier",
                "ghi_chu": "xem top_co2_2023",
            },
            "bien_dong_manh": {
                "tieu_chi": "|tăng trưởng| > 50% và |chênh lệch| > 1 Mt (1970–2024)",
                "so_dong": int(len(outlier_list)),
                "quyet_dinh": "giữ toàn bộ",
                "vi_du_dien_hinh": "Kuwait 1991 (+1202%, chiến tranh vùng Vịnh và "
                                   "cháy giếng dầu) rồi rơi về 1992; Libya 2020–2021 "
                                   "(nội chiến, phong tỏa dầu mỏ rồi phục hồi)",
                "danh_sach": outlier_list,
            },
            "co2_bang_0": {
                "quoc_gia_giai_doan_1970_2024": zeros,
                "quyet_dinh": "giữ nguyên giá trị gốc, không thay bằng null",
            },
        },
    }
    return out, world_out, report

def clean_edgar(cmap):
    df = pd.read_excel(EDGAR, sheet_name="GHG_by_sector_and_country")
    n_raw = len(df)
    co2 = df[df["Substance"] == "CO2"].copy()
    mask_ex = co2["Country"].isin(EDGAR_EXCLUDE_COUNTRIES) | \
        co2["EDGAR Country Code"].isin(EDGAR_EXCLUDE_CODES)
    excluded = sorted(co2[mask_ex]["Country"].unique().tolist())
    co2 = co2[~mask_ex].copy()
    year_cols = [c for c in co2.columns if str(c).isdigit()]
    id_vars = ["Country", "EDGAR Country Code", "Sector"]
    long = co2[id_vars + year_cols].melt(
        id_vars=id_vars, value_vars=year_cols,
        var_name="year", value_name="co2",
    )
    long["year"] = long["year"].astype(int)
    long = long.rename(columns={
        "Country": "country", "EDGAR Country Code": "iso_alpha",
        "Sector": "sector",
    })
    total = long.groupby(["iso_alpha", "year"])["co2"].transform("sum")
    long["sector_share_percent"] = long["co2"] / total * 100
    long["continent"] = long["iso_alpha"].map(cmap)
    unmatched = sorted(long[long["continent"].isna()]["iso_alpha"].unique().tolist())
    out = long[["country", "iso_alpha", "year", "sector", "co2",
                "sector_share_percent"]].sort_values(
        ["iso_alpha", "year", "sector"]).reset_index(drop=True)

    report = {
        "rows_raw_wide": int(n_raw),
        "rows_co2_wide": int((df["Substance"] == "CO2").sum()),
        "excluded_entities": excluded,
        "rows_output_long": int(len(out)),
        "countries": int(out["iso_alpha"].nunique()),
        "sectors": sorted(out["sector"].unique().tolist()),
        "year_min": int(out["year"].min()), "year_max": int(out["year"].max()),
        "missing_rate": {k: round(float(v), 4) for k, v in out.isna().mean().to_dict().items()},
        "continent_unmatched_iso": unmatched,
        "sector_share_check_max": round(float(out["sector_share_percent"].max()), 2),
    }
    return out, report

def clean_renewable(cmap):
    df = pd.read_csv(RENEW)
    n_raw = len(df)
    is_agg = df["Code"].isna() | df["Code"].str.contains("_", na=False)
    agg = sorted(df[is_agg & df["Code"].notna()]["Entity"].unique().tolist())
    no_code = sorted(df[df["Code"].isna()]["Entity"].unique().tolist())
    keep = df[~is_agg].copy()
    keep.columns = ["country", "iso_alpha", "year", "renewable_percent"]
    keep["continent"] = keep["iso_alpha"].map(cmap)
    out = keep[["country", "iso_alpha", "year", "renewable_percent"]].sort_values(
        ["iso_alpha", "year"]).reset_index(drop=True)
    unmatched = sorted(out["iso_alpha"][out["iso_alpha"].map(cmap).isna()].unique().tolist())
    cov = out.groupby("year")["iso_alpha"].nunique()
    report = {
        "rows_raw": int(n_raw),
        "rows_output": int(len(out)),
        "aggregates_separated": agg,
        "entities_without_code_separated": no_code,
        "year_min": int(out["year"].min()), "year_max": int(out["year"].max()),
        "coverage_by_year": {int(k): int(v) for k, v in cov.to_dict().items()},
        "coverage_2023": int(cov.get(2023, 0)), "coverage_2024": int(cov.get(2024, 0)),
        "missing_rate": {k: round(float(v), 4) for k, v in out.isna().mean().to_dict().items()},
        "continent_unmatched_iso": unmatched,
    }
    return out, report

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    EDA.mkdir(parents=True, exist_ok=True)
    cmap = load_continent()

    co2_nat, co2_world, r1 = clean_owid(cmap)
    co2_sec, r2 = clean_edgar(cmap)
    renew, r3 = clean_renewable(cmap)

    co2_nat.to_csv(OUT / "co2_quoc_gia.csv", index=False)
    co2_world.to_csv(OUT / "co2_toan_cau.csv", index=False)
    co2_sec.to_csv(OUT / "co2_theo_nganh.csv", index=False)
    renew.to_csv(OUT / "nang_luong_tai_tao.csv", index=False)

    quality = {
        "data_dictionary": DATA_DICTIONARY,
        "quan_co2_quoc_gia": r1,
        "quan_co2_theo_nganh": r2,
        "quan_nang_luong_tai_tao": r3,
        "notes": [
            "co2 OWID đơn vị Mt/năm (không gồm thay đổi sử dụng đất); "
            "co2_per_capita tính bằng tấn/người; EDGAR Substance = CO2 đơn vị Mt CO₂.",
            "renewable_percent là tỷ lệ năng lượng tái tạo trong tổng tiêu thụ "
            "năng lượng cuối cùng (%), không phải tỷ lệ điện tái tạo.",
            "Giai đoạn phân tích chính 1970–2024; có năng lượng tái tạo thì 1990–2023 "
            "(năm 2024 chỉ có 84 quốc gia). Năm 2025 của EDGAR là số sơ bộ, "
            "biểu đồ chốt ở 2024.",
            "Quốc gia phát thải cao không bị xóa; SCG (Serbia and Montenegro) giữ "
            "continent = null và báo unmatched để quyết định khi ghép bảng.",
        ],
    }
    (OUT / "bao_cao_chat_luong.json").write_text(
        json.dumps(quality, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"OK: co2_quoc_gia {co2_nat.shape} | theo_nganh {co2_sec.shape} | "
          f"tai_tao {renew.shape}")
    print("Unmatched:", r1["continent_unmatched_iso"], r2["continent_unmatched_iso"],
          r3["continent_unmatched_iso"])

if __name__ == "__main__":
    main()
