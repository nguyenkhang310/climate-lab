from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
PROCESSED = ROOT / "processed"
OUTPUTS = ROOT / "outputs" / "nguyen_khang"

DATA = pd.read_csv(PROCESSED / "nguyen_khang" / "dashboard_quoc_gia_nam.csv")
GLOBAL_DATA = pd.read_csv(PROCESSED / "nguyen_khang" / "khi_hau_toan_cau_nam.csv")
SECTOR_DATA = pd.read_csv(PROCESSED / "quan" / "co2_theo_nganh.csv")
FORECAST_DATA = pd.read_csv(OUTPUTS / "kich_ban_nhiet_do_2050.csv")
HISTORICAL_PREDICTIONS = pd.read_csv(OUTPUTS / "du_doan_tap_kiem_tra.csv")
MODEL_METRICS = json.loads((OUTPUTS / "so_sanh_mo_hinh.json").read_text(encoding="utf-8"))

DATA["year"] = DATA["year"].astype(int)
SECTOR_DATA["year"] = SECTOR_DATA["year"].astype(int)

CONTINENTS = sorted(DATA["continent"].dropna().unique().tolist())
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
    if frame.empty:
        return pd.DataFrame(columns=[
            "year", "temperature_anomaly", "co2", "population",
            "co2_per_capita", "renewable_percent",
        ])

    if use_global:
        start, end = int(frame.year.min()), int(frame.year.max())
        result = GLOBAL_DATA[GLOBAL_DATA.year.between(start, end)].copy()
        result["renewable_percent"] = np.nan
        return result

    grouped = frame.groupby("year", as_index=False)
    result = grouped.agg(
        temperature_anomaly=("temperature_anomaly", "mean"),
        co2=("co2", lambda values: values.sum(min_count=1)),
        population=("population", lambda values: values.sum(min_count=1)),
    )
    result["co2_per_capita"] = result["co2"] * 1_000_000 / result["population"]

    yearly_renewable = {}
    renewable = frame.dropna(subset=["renewable_percent"])
    for year, group in renewable.groupby("year"):
        weights = group["population"].fillna(group["population"].median()).fillna(1)
        yearly_renewable[year] = float(
            (group["renewable_percent"] * weights).sum() / weights.sum()
        )
    result["renewable_percent"] = result["year"].map(yearly_renewable)
    return result

def filter_sector_data(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return SECTOR_DATA.iloc[0:0].copy()
    countries = set(frame.iso_alpha.dropna())
    return SECTOR_DATA[
        SECTOR_DATA.iso_alpha.isin(countries)
        & SECTOR_DATA.year.between(int(frame.year.min()), int(frame.year.max()))
    ].copy()
