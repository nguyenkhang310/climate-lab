"""Tạo dữ liệu mẫu để chạy dashboard."""
import pandas as pd

YEARS = list(range(1960, 2021, 10))
# country, iso_alpha, continent, anomaly 2020, CO₂ Mt, population triệu, renewable %
COUNTRIES = [
    ("Việt Nam", "VNM", "Châu Á", .82, 356.6, 97.3, 14.6),
    ("Trung Quốc", "CHN", "Châu Á", 1.12, 10668, 1402, 15.9),
    ("Hoa Kỳ", "USA", "Bắc Mỹ", 1.28, 5416, 331, 12.6),
    ("Ấn Độ", "IND", "Châu Á", .76, 2654, 1380, 22.1),
    ("Nhật Bản", "JPN", "Châu Á", 1.06, 1162, 125.8, 18.4),
    ("Đức", "DEU", "Châu Âu", 1.53, 728, 83.2, 38.0),
    ("Pháp", "FRA", "Châu Âu", 1.42, 306, 67.4, 24.0),
    ("Brazil", "BRA", "Nam Mỹ", .94, 467, 212.6, 45.3),
    ("Canada", "CAN", "Bắc Mỹ", 1.76, 583, 38, 28.1),
    ("Australia", "AUS", "Châu Đại Dương", 1.35, 414, 25.7, 17.2),
    ("Nam Phi", "ZAF", "Châu Phi", 1.18, 452, 59.3, 9.5),
    ("Thái Lan", "THA", "Châu Á", .88, 258, 69.8, 13.7),
    ("Nga", "RUS", "Châu Âu", 1.68, 1711, 144.1, 8.2),
    ("Indonesia", "IDN", "Châu Á", .79, 619, 273.5, 19.2),
    ("Ai Cập", "EGY", "Châu Phi", 1.02, 234, 102.3, 7.6),
]
COUNTRY_NAMES = {row[1]: row[0] for row in COUNTRIES}
CONTINENTS = list(dict.fromkeys(row[2] for row in COUNTRIES))
COORDINATES = dict(zip(COUNTRY_NAMES, [
    (108, 16), (104, 35), (-100, 38), (79, 22), (138, 37), (10, 51), (2, 47),
    (-52, -12), (-106, 57), (134, -25), (25, -29), (101, 15), (95, 60), (118, -3), (30, 27),
]))


def load_data():
    """Tạo 105 dòng dữ liệu cố định cho 15 quốc gia và 7 mốc năm."""
    rows = []
    warming = [-.26, -.18, .02, .25, .44, .78, 1]
    developing_emissions = [.11, .18, .28, .45, .65, .96, 1]
    population_growth = [.42, .52, .63, .72, .81, .99, 1]
    renewable_growth = [.45, .54, .63, .72, .80, .877, 1]
    developed = {"USA", "JPN", "DEU", "FRA", "CAN", "AUS", "RUS"}
    for name, iso, continent, anomaly, co2, population, renewable in COUNTRIES:
        for index, year in enumerate(YEARS):
            progress = index / 6
            if iso in developed:
                emissions = co2 * (.42 + .58 * progress ** 1.65)
            else:
                emissions = co2 * developing_emissions[index]
            people = population * 1_000_000 * population_growth[index]
            rows.append({
                "country": name,
                "iso_alpha": iso,
                "continent": continent,
                "year": year,
                "temperature_anomaly": round(anomaly * warming[index], 3),
                "co2": round(emissions, 2),
                "co2_per_capita": round(emissions * 1e6 / people, 3),
                "population": round(people),
                "renewable_percent": round(renewable * renewable_growth[index], 1),
            })
    return pd.DataFrame(rows)


DATA = load_data()


def filter_data(year_range=None, continent="all", country="all"):
    if isinstance(year_range, str):
        years = [int(value) for value in year_range.split("-")]
    else:
        years = year_range or [1960, 2020]
    frame = DATA[DATA.year.between(*years)]
    if continent != "all":
        frame = frame[frame.continent == continent]
    if country != "all":
        frame = frame[frame.iso_alpha == country]
    return frame.copy()


def aggregate(frame):
    """Gộp dữ liệu theo năm sau khi người dùng lọc."""
    if frame.empty:
        columns = [
            "year",
            "temperature_anomaly",
            "co2",
            "population",
            "co2_per_capita",
            "renewable_percent",
        ]
        return pd.DataFrame(columns=columns)
    weighted = frame.assign(
        temperature_weight=frame.temperature_anomaly * frame.population,
        renewable_weight=frame.renewable_percent * frame.population,
    )
    result = weighted.groupby("year", as_index=False).agg(
        co2=("co2", "sum"),
        population=("population", "sum"),
        temperature_weight=("temperature_weight", "sum"),
        renewable_weight=("renewable_weight", "sum"),
    )
    return result.assign(
        temperature_anomaly=result.temperature_weight / result.population,
        co2_per_capita=result.co2 * 1e6 / result.population,
        renewable_percent=result.renewable_weight / result.population,
    )
