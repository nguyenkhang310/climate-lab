import json
from pathlib import Path

import pandas as pd

from phan_tich_co2.quan.tao_bieu_do_plotly import SECTOR_NAMES

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data/du_lieu_da_xu_ly"
OUTPUTS = ROOT / "data/ket_qua_mo_hinh/nguyen_khang"
DATA = pd.read_csv(PROCESSED / "nguyen_khang/dashboard_quoc_gia_nam.csv")
GLOBAL_DATA = pd.read_csv(PROCESSED / "nguyen_khang/khi_hau_toan_cau_nam.csv")
SECTOR_DATA = pd.read_csv(PROCESSED / "quan/co2_theo_nganh.csv")
MONTHLY_DATA = pd.read_csv(PROCESSED / "duc/nhiet_do_theo_thang.csv")
SCENARIO_DATA = pd.read_csv(OUTPUTS / "kich_ban_2050.csv")
BACKTEST_DATA = pd.read_csv(OUTPUTS / "du_doan_kiem_tra.csv")
MODEL_INFO = json.loads((OUTPUTS / "thong_tin_mo_hinh.json").read_text(encoding="utf-8"))

DATA["year"] = DATA["year"].astype(int)
SECTOR_DATA["year"] = SECTOR_DATA["year"].astype(int)

CONTINENTS = sorted(DATA["continent"].dropna().unique().tolist())
CONTINENT_NAMES = {"Africa": "Châu Phi", "Asia": "Châu Á", "Europe": "Châu Âu",
                   "North America": "Bắc Mỹ", "South America": "Nam Mỹ",
                   "Oceania": "Châu Đại Dương", "Antarctica": "Nam Cực"}
COUNTRY_NAMES = (
    DATA[["iso_alpha", "country"]]
    .dropna()
    .drop_duplicates("iso_alpha")
    .sort_values("country")
    .set_index("iso_alpha")["country"]
    .to_dict()
)

COORDINATES = {
    "VNM": (108, 16), "CHN": (104, 35), "USA": (-100, 38),
    "IND": (79, 22), "JPN": (138, 37), "DEU": (10, 51),
    "FRA": (2, 47), "BRA": (-52, -12), "CAN": (-106, 57),
    "AUS": (134, -25), "ZAF": (25, -29), "THA": (101, 15),
    "RUS": (95, 60), "IDN": (118, -3), "EGY": (30, 27),
}

def filter_data(year_range=None, continent="all", country="all") -> pd.DataFrame:
    if isinstance(year_range, str):
        years = [int(value) for value in year_range.split("-")]
    elif year_range:
        years = [int(year_range[0]), int(year_range[-1])]
    else:
        years = [int(DATA.year.min()), int(DATA.year.max())]
    frame = DATA[DATA.year.between(*years)]
    if continent != "all":
        frame = frame[frame.continent == continent]
    if country != "all":
        frame = frame[frame.iso_alpha == country]
    return frame.copy()

def aggregate(frame: pd.DataFrame, use_global: bool = False) -> pd.DataFrame:
    columns = ["year", "temperature_anomaly", "co2", "population", "co2_per_capita"]
    if frame.empty:
        return pd.DataFrame(columns=columns)
    if use_global:
        start, end = int(frame.year.min()), int(frame.year.max())
        return GLOBAL_DATA[GLOBAL_DATA.year.between(start, end)].copy()
    if frame.iso_alpha.nunique() == 1:
        return frame[columns].sort_values("year").copy()

    grouped = frame.groupby("year", as_index=False)
    result = grouped.agg(
        temperature_anomaly=("temperature_anomaly", "mean"),
        co2=("co2", lambda values: values.sum(min_count=1)),
        population=("population", lambda values: values.sum(min_count=1)),
    )
    paired = frame.dropna(subset=["co2", "population"])
    totals = paired[paired.population > 0].groupby("year")[["co2", "population"]].sum()
    result["co2_per_capita"] = result.year.map(totals.co2 * 1_000_000 / totals.population)
    return result

def filtered_sectors(frame, use_global=False):
    data = SECTOR_DATA[SECTOR_DATA.year.between(frame.year.min(), frame.year.max())]
    if not use_global:
        data = data[data.iso_alpha.isin(frame.iso_alpha)]
    return data.assign(sector=data.sector.replace(SECTOR_NAMES))


def filtered_months(frame, use_global=False):
    codes = ["WLD"] if use_global else frame.iso_alpha.unique()
    return MONTHLY_DATA[MONTHLY_DATA.year.between(frame.year.min(), frame.year.max()) & MONTHLY_DATA.iso_alpha.isin(codes)]


def sector_totals(frame: pd.DataFrame, use_global=False) -> pd.Series:
    data = filtered_sectors(frame, use_global)
    return data[data.year.eq(frame.year.max())].groupby("sector").co2.sum(min_count=1).dropna().sort_values(ascending=False)
