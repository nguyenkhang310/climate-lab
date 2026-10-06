from pathlib import Path
import sqlite3

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data/du_lieu_da_xu_ly"
DB = DATA / "nguyen_khang/climate_lab.db"
DUC = DATA / "duc"
QUAN = DATA / "quan"

FILES = {
    "nhiet_do_quoc_gia": DUC / "nhiet_do_quoc_gia.csv",
    "nhiet_do_toan_cau": DUC / "nhiet_do_toan_cau.csv",
    "co2_quoc_gia": QUAN / "co2_quoc_gia.csv",
    "co2_toan_cau": QUAN / "co2_toan_cau.csv",
    "nang_luong_tai_tao": QUAN / "nang_luong_tai_tao.csv",
    "co2_theo_nganh": QUAN / "co2_theo_nganh.csv",
}

COLUMNS = {
    "nhiet_do_quoc_gia": ["iso_alpha", "year", "temperature_anomaly", "source_flag"],
    "nhiet_do_toan_cau": ["year", "temperature_anomaly"],
    "co2_quoc_gia": [
        "iso_alpha", "year", "co2", "co2_per_capita", "co2_growth_pct", "population"
    ],
    "co2_toan_cau": [
        "year", "co2", "co2_per_capita", "population", "cumulative_co2"
    ],
    "nang_luong_tai_tao": ["iso_alpha", "year", "renewable_percent"],
    "co2_theo_nganh": ["iso_alpha", "year", "sector", "co2", "sector_share_percent"],
}

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE quoc_gia (
    iso_alpha TEXT PRIMARY KEY, country TEXT NOT NULL, continent TEXT
);
CREATE TABLE nam (
    year INTEGER PRIMARY KEY, decade INTEGER NOT NULL
);
CREATE TABLE nhiet_do_quoc_gia (
    iso_alpha TEXT NOT NULL, year INTEGER NOT NULL,
    temperature_anomaly REAL, source_flag TEXT,
    PRIMARY KEY (iso_alpha, year),
    FOREIGN KEY (iso_alpha) REFERENCES quoc_gia (iso_alpha),
    FOREIGN KEY (year) REFERENCES nam (year)
);
CREATE TABLE co2_quoc_gia (
    iso_alpha TEXT NOT NULL, year INTEGER NOT NULL,
    co2 REAL, co2_per_capita REAL, co2_growth_pct REAL, population REAL,
    PRIMARY KEY (iso_alpha, year),
    FOREIGN KEY (iso_alpha) REFERENCES quoc_gia (iso_alpha),
    FOREIGN KEY (year) REFERENCES nam (year)
);
CREATE TABLE nang_luong_tai_tao (
    iso_alpha TEXT NOT NULL, year INTEGER NOT NULL, renewable_percent REAL,
    PRIMARY KEY (iso_alpha, year),
    FOREIGN KEY (iso_alpha) REFERENCES quoc_gia (iso_alpha),
    FOREIGN KEY (year) REFERENCES nam (year)
);
CREATE TABLE co2_theo_nganh (
    iso_alpha TEXT NOT NULL, year INTEGER NOT NULL, sector TEXT NOT NULL,
    co2 REAL, sector_share_percent REAL,
    PRIMARY KEY (iso_alpha, year, sector),
    FOREIGN KEY (iso_alpha) REFERENCES quoc_gia (iso_alpha),
    FOREIGN KEY (year) REFERENCES nam (year)
);
CREATE TABLE nhiet_do_toan_cau (
    year INTEGER PRIMARY KEY, temperature_anomaly REAL,
    FOREIGN KEY (year) REFERENCES nam (year)
);
CREATE TABLE co2_toan_cau (
    year INTEGER PRIMARY KEY, co2 REAL, co2_per_capita REAL,
    population REAL, cumulative_co2 REAL,
    FOREIGN KEY (year) REFERENCES nam (year)
);
CREATE VIEW dashboard_quoc_gia_nam AS
WITH khoa AS (
    SELECT iso_alpha, year FROM nhiet_do_quoc_gia
    UNION SELECT iso_alpha, year FROM co2_quoc_gia
    UNION SELECT iso_alpha, year FROM nang_luong_tai_tao
)
SELECT q.country, k.iso_alpha, q.continent, k.year, n.decade,
       t.temperature_anomaly, c.co2, c.co2_per_capita, c.population,
       r.renewable_percent, t.source_flag
FROM khoa k
JOIN quoc_gia q USING (iso_alpha)
JOIN nam n USING (year)
LEFT JOIN nhiet_do_quoc_gia t USING (iso_alpha, year)
LEFT JOIN co2_quoc_gia c USING (iso_alpha, year)
LEFT JOIN nang_luong_tai_tao r USING (iso_alpha, year)
WHERE k.year BETWEEN 1970 AND 2024;
CREATE VIEW khi_hau_toan_cau_nam AS
SELECT t.year, n.decade, t.temperature_anomaly, c.co2,
       c.co2_per_capita, c.population, c.cumulative_co2
FROM nhiet_do_toan_cau t
JOIN co2_toan_cau c USING (year)
JOIN nam n USING (year)
WHERE t.year BETWEEN 1970 AND 2024;
"""


def dimensions(frames: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame]:
    countries = [frame.reindex(columns=["iso_alpha", "country", "continent"])
                 for frame in frames.values() if "iso_alpha" in frame]
    country = pd.concat(countries).groupby("iso_alpha", as_index=False).first()
    country.loc[country["iso_alpha"] == "ATA", "continent"] = "Antarctica"
    year = pd.concat([frame[["year"]] for frame in frames.values()]).drop_duplicates().sort_values("year")
    year["decade"] = year["year"] // 10 * 10
    return country, year


def main() -> None:
    DB.parent.mkdir(parents=True, exist_ok=True)
    temporary = DB.with_suffix(".tmp.db")
    temporary.unlink(missing_ok=True)
    frames = {name: pd.read_csv(path) for name, path in FILES.items()}
    country, year = dimensions(frames)

    with sqlite3.connect(temporary) as connection:
        connection.executescript(SCHEMA)
        country.to_sql("quoc_gia", connection, if_exists="append", index=False)
        year.to_sql("nam", connection, if_exists="append", index=False)
        for name, frame in frames.items():
            frame[COLUMNS[name]].to_sql(name, connection, if_exists="append", index=False)
        if connection.execute("PRAGMA foreign_key_check").fetchall():
            raise ValueError("Dữ liệu vi phạm khóa ngoại")

    temporary.replace(DB)
    with sqlite3.connect(DB) as connection:
        rows = connection.execute("SELECT COUNT(*) FROM dashboard_quoc_gia_nam").fetchone()[0]
    print(f"OK: {DB.name}, {len(FILES) + 2} bảng, {rows:,} dòng dashboard")


if __name__ == "__main__":
    main()
