"""Lam sach du lieu phan Quan: CO2 (OWID), phat thai theo nganh (EDGAR), nang luong tai tao (UN/OWID).

Doc: data/data/README.md  (muc "Quan - CO2, nganh phat thai va nang luong tai tao")
Quy tac bat buoc tuan thu:
  - Khoa ghep cuoi: iso_alpha + year
  - Missing giu null, khong fill 0
  - Tach vung tong hop khoi quoc gia (khong cong trung)
  - EDGAR: loc Substance = CO2, loai GLOBAL TOTAL / EU27 / International Aviation-Shipping
  - Khong xoa "outlier" la quoc gia phat thai cao
Chay:  python3 scripts/clean_quan.py
"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "data"
OUT = ROOT / "processed"
EDA = ROOT / "eda" / "quan"

OWID = RAW / "02_quan_phat_thai_co2" / "owid_phat_thai_co2_1750_2024.csv"
EDGAR = RAW / "02_quan_phat_thai_co2" / "edgar_phat_thai_theo_nganh_1970_2025.xlsx"
RENEW = RAW / "03_quan_nang_luong_tai_tao" / "un_ty_trong_nang_luong_tai_tao_1990_2024.csv"
CONTINENT = RAW / "04_dung_chung_danh_muc_quoc_gia" / "owid_quoc_gia_chau_luc.csv"

# Cac entity tong hop trong OWID (khong co iso_code) + World; giu rieng de tranh cong trung
OWID_AGGREGATES_KEEP = {"World"}  # chuoi toan cau dung truc tiep dong World (theo README muc 7)

EDGAR_EXCLUDE_COUNTRIES = {
    "GLOBAL TOTAL", "EU27", "International Aviation", "International Shipping",
}
EDGAR_EXCLUDE_CODES = {"AIR", "SEA"}  # ma EDGAR rieng cho hang khong / van tai bien quoc te

# Tu dien du lieu cho 3 bang dau ra (README: moi bang can co data dictionary)
DATA_DICTIONARY = {
    "quan_co2_quoc_gia.csv": {
        "country": "Ten quoc gia/lanh tho (OWID)",
        "iso_alpha": "Ma ISO3, khoa ghep cung year",
        "continent": "Chau luc theo OWID (null neu khong ghep duoc: ATA)",
        "year": "Nam (1750-2024; phan tich chinh 1970-2024)",
        "decade": "Thap ky = floor(year/10)*10 (2020-2024 la giai doan chua du 10 nam)",
        "co2": "Phat thai CO2 Mt/nam, khong gom thay doi su dung dat (GCP via OWID); null=thieu",
        "co2_per_capita": "tan CO2/nguoi (khong LUC); null=thieu",
        "population": "Dan so (nguoi); null=thieu",
    },
    "quan_co2_theo_nganh.csv": {
        "country": "Ten quoc gia (EDGAR)",
        "iso_alpha": "Ma quoc gia EDGAR (tuong duong ISO3), khoa ghep cung year",
        "year": "Nam (1970-2025, dang long)",
        "sector": "Nganh EDGAR: Power Industry, Industrial Combustion, Transport, "
                  "Buildings, Fuel Production, Agriculture, Processes, Waste",
        "co2": "Phat thai CO2 Mt/nam cua nganh (Substance=CO2 da loc)",
        "sector_share_percent": "Ty trong nganh trong tong CO2 quoc gia-nam (%)",
    },
    "quan_nang_luong_tai_tao.csv": {
        "country": "Ten quoc gia",
        "iso_alpha": "Ma ISO3, khoa ghep cung year",
        "year": "Nam (1990-2024; phan tich chinh 1990-2023 vi 2024 chi 84 nuoc)",
        "renewable_percent": "% nang luong tai tao trong tong tieu thu nang luong "
                             "cuoi cung (khong phai % dien tai tao)",
    },
}


def load_continent():
    c = pd.read_csv(CONTINENT)
    cmap = dict(zip(c["Code"], c["World region according to OWID"]))
    return cmap


def clean_owid(cmap):
    df = pd.read_csv(OWID, low_memory=False)
    n_raw = len(df)
    # Bao cao truoc loc
    agg_rows = df[df["iso_code"].isna()]
    agg_names = sorted(agg_rows["country"].unique().tolist())
    world = df[df["country"] == "World"].copy()

    keep = df[df["iso_code"].notna()].copy()
    keep = keep.rename(columns={"iso_code": "iso_alpha"})
    keep["continent"] = keep["iso_alpha"].map(cmap)
    keep["decade"] = (keep["year"] // 10 * 10).astype(int)
    out = keep[[
        "country", "iso_alpha", "continent", "year", "decade",
        "co2", "co2_per_capita", "population",
    ]].sort_values(["iso_alpha", "year"]).reset_index(drop=True)

    unmatched = sorted(out[out["continent"].isna()]["iso_alpha"].unique().tolist())
    # Muc tang CO2 theo nam (YoY %) chi dung cho EDA, khong dua vao CSV de giu schema
    g = out.sort_values(["iso_alpha", "year"])
    yoy = g.groupby("iso_alpha")["co2"].pct_change(fill_method=None) * 100

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
    }
    return out, report


def clean_edgar(cmap):
    df = pd.read_excel(EDGAR, sheet_name="GHG_by_sector_and_country")
    n_raw = len(df)
    co2 = df[df["Substance"] == "CO2"].copy()
    # Loai dong tong hop / quoc te ca theo ten va ma
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
    # Tong CO2 quoc gia-nam de tinh ty trong nganh
    total = long.groupby(["iso_alpha", "year"])["co2"].transform("sum")
    long["sector_share_percent"] = long["co2"] / total * 100
    long["continent"] = long["iso_alpha"].map(cmap)  # phu tro, khong xuat
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
    # Vung tong hop: Code null (LDCs/SIDS/...) hoac ma vung UN/SDG/OWID_WRL (chua '_')
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
        "entities_without_code_separated": no_code,  # vd Kosovo: quoc gia that nhung khong co ma ISO
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

    co2_nat, r1 = clean_owid(cmap)
    co2_sec, r2 = clean_edgar(cmap)
    renew, r3 = clean_renewable(cmap)

    co2_nat.to_csv(OUT / "quan_co2_quoc_gia.csv", index=False)
    co2_sec.to_csv(OUT / "quan_co2_theo_nganh.csv", index=False)
    renew.to_csv(OUT / "quan_nang_luong_tai_tao.csv", index=False)

    quality = {
        "data_dictionary": DATA_DICTIONARY,
        "quan_co2_quoc_gia": r1,
        "quan_co2_theo_nganh": r2,
        "quan_nang_luong_tai_tao": r3,
        "notes": [
            "co2 OWID don vi Mt/nam (khong gom thay doi su dung dat); "
            "co2_per_capita tan/nguoi; EDGAR Substance=CO2 don vi Mt CO2.",
            "renewable_percent la ty le nang luong tai tao trong tong tieu thu "
            "nang luong cuoi cung (%), khong phai ty le dien tai tao.",
            "Giai doan phan tich chinh 1970-2024; co nang luong tai tao thi 1990-2023 "
            "(2024 chi 84 quoc gia).",
            "Quoc gia phat thai cao KHONG bi xoa; SCG (Serbia and Montenegro) giu "
            "continent=null va bao cao unmatched de Khang quyet dinh khi join.",
        ],
    }
    (OUT / "quan_data_quality.json").write_text(
        json.dumps(quality, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"OK: co2_quoc_gia {co2_nat.shape} | theo_nganh {co2_sec.shape} | "
          f"tai_tao {renew.shape}")
    print("Unmatched:", r1["continent_unmatched_iso"], r2["continent_unmatched_iso"],
          r3["continent_unmatched_iso"])


if __name__ == "__main__":
    main()
