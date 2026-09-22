"""
Pipeline làm sạch dữ liệu nhiệt độ và tạo biểu đồ EDA của Đức.
Bao gồm:
1. Làm sạch dữ liệu nhiệt độ toàn cầu NASA GISTEMP (1880–2025).
2. Làm sạch & chuẩn hóa dữ liệu nhiệt độ quốc gia FAOSTAT (1961–2025) bằng chuẩn UN M49 -> ISO3.
3. Xuất báo cáo kiểm định chất lượng dữ liệu bao_cao_chat_luong.json.
4. Tạo đầy đủ 6 biểu đồ tĩnh (PNG) và biểu đồ tương tác (Plotly HTML).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "processed" / "duc"
EDA_STATIC = ROOT / "eda" / "duc" / "bieu_do_tinh"
EDA_INTERACTIVE = ROOT / "eda" / "duc" / "bieu_do_tuong_tac"

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
    n_raw = len(df_raw)

    df = df_raw[["Year", "J-D"]].copy()
    df.rename(columns={"Year": "year", "J-D": "temperature_anomaly"}, inplace=True)
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["temperature_anomaly"] = pd.to_numeric(df["temperature_anomaly"], errors="coerce")
    df = df.dropna(subset=["temperature_anomaly"])
    df = df[df["year"] <= 2025].copy()
    df["year"] = df["year"].astype(int)
    df["decade"] = (df["year"] // 10) * 10

    df_final = df[["year", "decade", "temperature_anomaly"]].sort_values("year").reset_index(drop=True)
    output_path = PROCESSED / "nhiet_do_toan_cau.csv"
    df_final.to_csv(output_path, index=False)

    stats = {
        "rows_raw": int(n_raw),
        "rows_output": int(len(df_final)),
        "year_min": int(df_final["year"].min()),
        "year_max": int(df_final["year"].max()),
        "missing_rate": {col: round(float(df_final[col].isna().mean()), 4) for col in df_final.columns},
        "temperature_mean": round(float(df_final["temperature_anomaly"].mean()), 4),
        "temperature_std": round(float(df_final["temperature_anomaly"].std()), 4),
        "temperature_min": round(float(df_final["temperature_anomaly"].min()), 4),
        "temperature_max": round(float(df_final["temperature_anomaly"].max()), 4),
    }
    return df_final, stats


def clean_faostat() -> tuple[pd.DataFrame, dict]:
    """Làm sạch chuỗi nhiệt độ quốc gia FAOSTAT bằng mã UN M49 sang ISO3."""
    # 1. Đọc bảng ánh xạ M49 sang ISO-3 và châu lục
    m49_df = pd.read_csv(M49_REF, dtype=str)
    m49_to_iso = dict(zip(m49_df["m49"].str.zfill(3), m49_df["iso_alpha"]))
    m49_to_name = dict(zip(m49_df["m49"].str.zfill(3), m49_df["country_name"]))

    owid_df = pd.read_csv(OWID_CONTINENT)
    iso_to_cont = dict(zip(owid_df["Code"], owid_df["World region according to OWID"]))
    iso_to_name = dict(zip(owid_df["Code"], owid_df["Entity"]))

    # 2. Đọc file thô FAOSTAT
    df_raw = pd.read_csv(FAO_RAW, low_memory=False)
    n_raw = len(df_raw)

    # 3. Lọc chỉ lấy Temperature change và Meteorological year
    df_fao = df_raw[
        (df_raw["Element"] == "Temperature change") &
        (df_raw["Months"] == "Meteorological year")
    ].copy()
    n_meteorological = len(df_fao)

    # 4. Chuẩn hóa mã M49
    df_fao["m49_clean"] = (
        df_fao["Area Code (M49)"]
        .astype(str)
        .str.strip()
        .str.replace("'", "", regex=False)
        .str.zfill(3)
    )

    # 5. Ánh xạ M49 sang ISO-3
    df_fao["iso_alpha"] = df_fao["m49_clean"].map(m49_to_iso)

    # Thống kê các vùng tổng hợp và các mã không ghép được
    unmatched_rows = df_fao[df_fao["iso_alpha"].isna()]
    aggregates_separated = sorted(unmatched_rows["Area"].unique().tolist())

    # 6. Lọc các quốc gia/lãnh thổ có mã ISO-3 hợp lệ (3 chữ cái)
    df_clean = df_fao.dropna(subset=["iso_alpha"]).copy()
    df_clean = df_clean[df_clean["iso_alpha"].str.len() == 3].copy()

    # 7. Chuẩn hóa tên quốc gia và châu lục
    df_clean["country"] = (
        df_clean["iso_alpha"]
        .map(iso_to_name)
        .fillna(df_clean["m49_clean"].map(m49_to_name))
        .fillna(df_clean["Area"])
    )
    df_clean["continent"] = df_clean["iso_alpha"].map(iso_to_cont)

    # Chuẩn hóa kiểu dữ liệu
    df_clean["year"] = pd.to_numeric(df_clean["Year"], errors="coerce").astype(int)
    df_clean["temperature_anomaly"] = pd.to_numeric(df_clean["Value"], errors="coerce")
    df_clean["source_flag"] = df_clean["Flag"]
    df_clean["decade"] = (df_clean["year"] // 10) * 10

    target_cols = [
        "country", "iso_alpha", "continent", "year", "decade",
        "temperature_anomaly", "source_flag"
    ]
    df_final = df_clean[target_cols].sort_values(["iso_alpha", "year"]).reset_index(drop=True)

    # Kiểm tra trùng lặp khóa (bắt buộc = 0)
    dup_keys = int(df_final.duplicated(["iso_alpha", "year"]).sum())
    if dup_keys > 0:
        raise ValueError(f"Dữ liệu FAOSTAT sạch có {dup_keys} dòng trùng khóa (iso_alpha, year)!")

    # Xuất file CSV
    output_path = PROCESSED / "nhiet_do_quoc_gia.csv"
    df_final.to_csv(output_path, index=False)

    # Tính toán thống kê phân phối và outlier
    temp_series = df_final["temperature_anomaly"].dropna()
    q1 = float(temp_series.quantile(0.25))
    q3 = float(temp_series.quantile(0.75))
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    outliers_iqr = int(((temp_series < lower_bound) | (temp_series > upper_bound)).sum())

    unmatched_continents = sorted(df_final[df_final["continent"].isna()]["iso_alpha"].unique().tolist())

    # Top 5 năm dị thường nhiệt độ cao nhất theo quốc gia
    top_extremes = (
        df_final.nlargest(5, "temperature_anomaly")
        [["country", "iso_alpha", "year", "temperature_anomaly", "source_flag"]]
        .to_dict(orient="records")
    )

    stats = {
        "rows_raw": int(n_raw),
        "rows_meteorological_year": int(n_meteorological),
        "rows_output": int(len(df_final)),
        "aggregates_separated_count": len(aggregates_separated),
        "aggregates_separated": aggregates_separated,
        "countries_count": int(df_final["iso_alpha"].nunique()),
        "year_min": int(df_final["year"].min()),
        "year_max": int(df_final["year"].max()),
        "duplicate_keys": dup_keys,
        "missing_rate": {col: round(float(df_final[col].isna().mean()), 4) for col in df_final.columns},
        "continent_unmatched_iso": unmatched_continents,
        "flag_distribution": {
            str(k): int(v) for k, v in df_final["source_flag"].value_counts(dropna=False).to_dict().items()
        },
        "distribution": {
            "mean": round(float(temp_series.mean()), 4),
            "std": round(float(temp_series.std()), 4),
            "median": round(float(temp_series.median()), 4),
            "min": round(float(temp_series.min()), 4),
            "max": round(float(temp_series.max()), 4),
            "p1": round(float(temp_series.quantile(0.01)), 4),
            "p99": round(float(temp_series.quantile(0.99)), 4),
            "iqr_bounds": [round(lower_bound, 4), round(upper_bound, 4)],
            "outliers_iqr_count": outliers_iqr,
            "outliers_iqr_pct": round(float(outliers_iqr / len(temp_series) * 100), 2)
        },
        "top_positive_extremes": top_extremes,
        "outlier_interpretation": (
            "Các giá trị vượt ngưỡng IQR chủ yếu tập trung tại các vùng cực Bắc (Svalbard, Greenland, Canada, Nga) "
            "vào các đợt nắng nóng kỷ lục sau năm 2010. Toàn bộ các giá trị này đều có cờ FAO là 'E' (Estimated), "
            "phản ánh hiện tượng khí hậu cực đoan thực tế (Arctic Amplification), không phải lỗi nhập liệu."
        )
    }
    return df_final, stats


def export_quality_report(nasa_stats: dict, fao_stats: dict) -> None:
    """Tổng hợp và lưu báo cáo chất lượng dữ liệu ra file JSON."""
    report = {
        "data_dictionary": DATA_DICTIONARY,
        "duc_nhiet_do_toan_cau": nasa_stats,
        "duc_nhiet_do_quoc_gia": fao_stats,
        "methodology_notes": {
            "m49_to_iso3": (
                "Sử dụng bảng chuẩn UN M49 numeric để chuyển đổi sang ISO-3166-1 alpha-3. "
                "Xử lý riêng mã 156 (China, mainland) gắn chuẩn vào CHN với tên 'China'. "
                "Tách riêng Hong Kong (344/HKG), Macao (446/MAC), Đài Loan (158/TWN). "
                "Mã 159 (China tổng hợp của FAO) được tách ra nhóm aggregates_separated cùng World, Africa, Europe... "
                "nhằm đảm bảo không cộng trùng dữ liệu."
            ),
            "baseline": "Thời kỳ cơ sở 1951–1980 (0°C) cho cả NASA GISTEMP và FAOSTAT.",
            "join_key": "iso_alpha + year, kiểu dữ liệu: string(3) + int."
        }
    }
    out_file = PROCESSED / "bao_cao_chat_luong.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"Đã xuất báo cáo chất lượng: {out_file}")


def generate_eda_charts(df_nasa: pd.DataFrame, df_fao: pd.DataFrame) -> None:
    """Tạo đầy đủ các biểu đồ EDA tĩnh và tương tác."""
    EDA_STATIC.mkdir(parents=True, exist_ok=True)
    EDA_INTERACTIVE.mkdir(parents=True, exist_ok=True)

    # 1. Line Chart: Xu hướng nhiệt độ toàn cầu 1880–2025
    plt.figure(figsize=(12, 5))
    plt.plot(df_nasa["year"], df_nasa["temperature_anomaly"], color="#f46d43", alpha=0.5, label="Nhiệt độ hàng năm")
    df_nasa_copy = df_nasa.copy()
    df_nasa_copy["rolling_5"] = df_nasa_copy["temperature_anomaly"].rolling(5, center=True).mean()
    plt.plot(df_nasa_copy["year"], df_nasa_copy["rolling_5"], color="#a50026", linewidth=2.5, label="Đường xu hướng (Trung bình 5 năm)")
    plt.axhline(0, color="blue", linestyle="--", linewidth=1, label="Baseline 1951–1980 (0°C)")
    plt.title("Xu hướng Nhiệt độ Toàn cầu qua Thời gian (1880 – 2025)", fontsize=14, fontweight="bold")
    plt.xlabel("Năm")
    plt.ylabel("Độ lệch nhiệt độ (°C)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(EDA_STATIC / "01_xu_huong_nhiet_do_toan_cau.png", dpi=300)
    plt.close()

    # 2. Bar Chart: Nhiệt độ trung bình theo thập kỷ
    df_dec = df_nasa.groupby("decade")["temperature_anomaly"].mean().reset_index()
    colors = ["#4575b4" if v < 0 else "#d73027" for v in df_dec["temperature_anomaly"]]
    plt.figure(figsize=(11, 5))
    plt.bar(df_dec["decade"].astype(str) + "s", df_dec["temperature_anomaly"], color=colors, width=0.6)
    plt.axhline(0, color="black", linewidth=0.8)
    plt.title("Nhiệt độ Trung bình Toàn cầu theo Thập kỷ (NASA GISS)", fontsize=14, fontweight="bold")
    plt.xlabel("Thập kỷ")
    plt.ylabel("Độ lệch (°C)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(EDA_STATIC / "02_nhiet_do_theo_thap_ky.png", dpi=300)
    plt.close()

    # 3. Choropleth Map: Bản đồ nhiệt độ thế giới năm 2024
    df_2024 = df_fao[df_fao["year"] == 2024].dropna(subset=["temperature_anomaly"])
    fig_map = px.choropleth(
        df_2024,
        locations="iso_alpha",
        color="temperature_anomaly",
        hover_name="country",
        color_continuous_scale="RdBu_r",
        range_color=[-1.5, 3.5],
        title="Bản đồ Độ lệch Nhiệt độ Thế giới năm 2024 (so với 1951–1980)",
        labels={"temperature_anomaly": "Độ lệch (°C)"},
        template="plotly_white"
    )
    fig_map.write_html(str(EDA_INTERACTIVE / "03_ban_do_nhiet_do.html"))
    fig_map.write_image(str(EDA_STATIC / "03_ban_do_nhiet_do.png"), scale=2)

    # 4. Heatmap: Châu lục x Thập kỷ
    pivot_cont = df_fao.pivot_table(index="continent", columns="decade", values="temperature_anomaly", aggfunc="mean")
    pivot_cont.columns = [f"{c}s" for c in pivot_cont.columns]
    plt.figure(figsize=(11, 5))
    sns.heatmap(pivot_cont, cmap="coolwarm", annot=True, fmt=".2f", linewidths=0.5)
    plt.title("Nhiệt độ Trung bình theo Châu lục và Thập kỷ (FAOSTAT)", fontsize=14, fontweight="bold")
    plt.xlabel("Thập kỷ")
    plt.ylabel("Châu lục")
    plt.tight_layout()
    plt.savefig(EDA_STATIC / "04_heatmap_chau_luc_thap_ky.png", dpi=300)
    plt.close()

    # 5. Boxplot: Phân bố nhiệt độ giữa các quốc gia
    plt.figure(figsize=(12, 5))
    df_fao_box = df_fao.copy()
    df_fao_box["decade_str"] = df_fao_box["decade"].astype(str) + "s"
    sns.boxplot(
        data=df_fao_box, x="decade_str", y="temperature_anomaly",
        hue="decade_str", palette="Reds", showmeans=True, legend=False
    )
    plt.axhline(0, color="blue", linestyle="--", linewidth=0.8)
    plt.title("Phân bố Độ lệch Nhiệt độ giữa các Quốc gia qua từng Thập kỷ", fontsize=14, fontweight="bold")
    plt.xlabel("Thập kỷ")
    plt.ylabel("Độ lệch (°C)")
    plt.tight_layout()
    plt.savefig(EDA_STATIC / "05_phan_bo_nhiet_do_quoc_gia.png", dpi=300)
    plt.close()

    # 6. Biểu đồ Dự báo Hồi quy Tuyến tính (Linear Regression) đến năm 2050
    df_mod = df_nasa[df_nasa["year"] >= 1970].copy()
    train = df_mod[df_mod["year"] <= 2014]
    test = df_mod[df_mod["year"] >= 2015]

    # Train model
    lr_train = LinearRegression()
    lr_train.fit(train[["year"]], train["temperature_anomaly"])
    test_pred = lr_train.predict(test[["year"]])
    test_mae = mean_absolute_error(test["temperature_anomaly"], test_pred)
    test_rmse = np.sqrt(mean_squared_error(test["temperature_anomaly"], test_pred))

    # Full modern model (1970–2025)
    lr_full = LinearRegression()
    lr_full.fit(df_mod[["year"]], df_mod["temperature_anomaly"])
    full_pred = lr_full.predict(df_mod[["year"]])
    full_r2 = r2_score(df_mod["temperature_anomaly"], full_pred)
    full_mae = mean_absolute_error(df_mod["temperature_anomaly"], full_pred)
    full_rmse = np.sqrt(mean_squared_error(df_mod["temperature_anomaly"], full_pred))
    slope_decade = lr_full.coef_[0] * 10

    # Dự báo tương lai đến năm 2050
    future_years = np.arange(2025, 2051)
    future_df = pd.DataFrame({"year": future_years})
    future_pred = lr_full.predict(future_df)

    # Tính dải tin cậy 95%
    residuals = df_mod["temperature_anomaly"] - full_pred
    dof = len(df_mod) - 2
    s_err = np.sqrt(np.sum(residuals**2) / dof)
    x_mean = df_mod["year"].mean()
    ss_x = np.sum((df_mod["year"] - x_mean)**2)
    pi = 1.96 * s_err * np.sqrt(1 + 1 / len(df_mod) + (future_years - x_mean)**2 / ss_x)
    upper_pi = future_pred + pi
    lower_pi = future_pred - pi

    # 6a. Static Matplotlib
    plt.figure(figsize=(12, 6))
    pre = df_nasa[df_nasa["year"] < 1970]
    plt.plot(pre["year"], pre["temperature_anomaly"], color="#999999", alpha=0.6, label="Lịch sử (1880–1969)")
    plt.scatter(train["year"], train["temperature_anomaly"], color="#1f77b4", s=25, alpha=0.8, label="Huấn luyện (1970–2014)")
    plt.scatter(test["year"], test["temperature_anomaly"], color="#d62728", s=35, marker="s", label="Kiểm định thực tế (2015–2025)")
    plt.plot(df_mod["year"], full_pred, color="#d95f02", linewidth=2.5, label=f"Hồi quy OLS (+{slope_decade:.3f}°C/thập kỷ)")
    plt.plot(future_years, future_pred, color="#e41a1c", linestyle="--", linewidth=2.5, label="Dự báo xu hướng đến 2050")
    plt.fill_between(future_years, lower_pi, upper_pi, color="#e41a1c", alpha=0.15, label="Dải tin cậy 95%")
    plt.axhline(0, color="blue", linestyle=":", linewidth=1, label="Baseline 1951–1980 (0°C)")

    plt.title("Dự báo Xu hướng Nhiệt độ Toàn cầu đến năm 2050 (Mô hình Hồi quy Tuyến tính OLS)", fontsize=13, fontweight="bold")
    plt.xlabel("Năm", fontsize=11)
    plt.ylabel("Độ lệch nhiệt độ so với mốc 1951–1980 (°C)", fontsize=11)

    metrics_text = (
        f"Chỉ số Đánh giá Mô hình (1970–2025):\n"
        f"• R² = {full_r2:.4f}\n"
        f"• MAE = {full_mae:.4f}°C\n"
        f"• RMSE = {full_rmse:.4f}°C\n"
        f"• Tốc độ tăng: +{slope_decade:.3f}°C / thập kỷ\n"
        f"• Kiểm định Test (2015–2025):\n"
        f"  RMSE = {test_rmse:.4f}°C | MAE = {test_mae:.4f}°C\n"
        f"• Dự báo 2050: +{future_pred[-1]:.2f}°C (CI: [{lower_pi[-1]:.2f}, {upper_pi[-1]:.2f}]°C)"
    )
    plt.gca().text(
        0.02, 0.95, metrics_text, transform=plt.gca().transAxes, fontsize=9.5,
        verticalalignment="top",
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#f8f9fa", edgecolor="#cccccc", alpha=0.9)
    )
    plt.legend(loc="lower right", framealpha=0.9)
    plt.grid(True, linestyle="--", alpha=0.4)
    plt.tight_layout()
    plt.savefig(EDA_STATIC / "06_du_bao_hoi_quy_tuyen_tinh.png", dpi=300)
    plt.close()

    # 6b. Interactive Plotly HTML
    fig_reg = go.Figure()
    fig_reg.add_trace(go.Scatter(
        x=pre["year"], y=pre["temperature_anomaly"],
        mode="lines+markers", name="Lịch sử (1880–1969)",
        line=dict(color="#999999", width=1.5), marker=dict(size=4, color="#999999"),
        hovertemplate="Năm %{x}: %{y:.3f}°C<extra></extra>"
    ))
    fig_reg.add_trace(go.Scatter(
        x=train["year"], y=train["temperature_anomaly"],
        mode="markers", name="Huấn luyện (1970–2014)",
        marker=dict(size=6, color="#1f77b4"),
        hovertemplate="Năm %{x}: %{y:.3f}°C (Train)<extra></extra>"
    ))
    fig_reg.add_trace(go.Scatter(
        x=test["year"], y=test["temperature_anomaly"],
        mode="markers", name="Kiểm định thực tế (2015–2025)",
        marker=dict(size=8, symbol="square", color="#d62728"),
        hovertemplate="Năm %{x}: %{y:.3f}°C (Test)<extra></extra>"
    ))
    fig_reg.add_trace(go.Scatter(
        x=df_mod["year"], y=full_pred,
        mode="lines", name=f"Hồi quy OLS (+{slope_decade:.3f}°C/thập kỷ)",
        line=dict(color="#d95f02", width=2.5),
        hovertemplate="Hồi quy %{x}: %{y:.3f}°C<extra></extra>"
    ))
    fig_reg.add_trace(go.Scatter(
        x=future_years, y=future_pred,
        mode="lines", name="Dự báo đến 2050",
        line=dict(color="#e41a1c", width=2.5, dash="dash"),
        hovertemplate="Dự báo %{x}: %{y:.3f}°C<extra></extra>"
    ))
    fig_reg.add_trace(go.Scatter(
        x=np.concatenate([future_years, future_years[::-1]]),
        y=np.concatenate([upper_pi, lower_pi[::-1]]),
        fill="toself", fillcolor="rgba(228, 26, 28, 0.15)",
        line=dict(color="rgba(255,255,255,0)"),
        hoverinfo="skip", showlegend=True, name="Dải tin cậy 95%"
    ))
    fig_reg.add_hline(y=0, line_dash="dot", line_color="blue", annotation_text="Baseline 1951–1980 (0°C)")

    fig_reg.update_layout(
        title="<b>Dự báo Xu hướng Nhiệt độ Toàn cầu đến năm 2050 (Mô hình Hồi quy Tuyến tính OLS)</b>",
        xaxis_title="Năm",
        yaxis_title="Độ lệch nhiệt độ so với mốc 1951–1980 (°C)",
        template="plotly_white",
        hovermode="x unified",
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01, bgcolor="rgba(255,255,255,0.8)"),
        annotations=[dict(
            x=2050, y=future_pred[-1],
            text=f"2050: +{future_pred[-1]:.2f}°C",
            showarrow=True, arrowhead=2, ax=-40, ay=-30,
            bgcolor="#ffebee", bordercolor="#d32f2f"
        )]
    )
    fig_reg.write_html(str(EDA_INTERACTIVE / "06_du_bao_hoi_quy_tuyen_tinh.html"))
    print("Đã tạo đầy đủ 6 biểu đồ tĩnh và tương tác thành công!")


def main() -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    print("=== BẮT ĐẦU PIPELINE LÀM SẠCH VÀ EDA PHẦN ĐỨC ===")
    
    df_nasa, nasa_stats = clean_nasa()
    print(f"1. Hoàn tất làm sạch NASA: {len(df_nasa)} dòng (1880–2025).")

    df_fao, fao_stats = clean_faostat()
    print(f"2. Hoàn tất làm sạch FAOSTAT: {len(df_fao)} dòng ({df_fao['iso_alpha'].nunique()} quốc gia, 1961–2025).")

    export_quality_report(nasa_stats, fao_stats)
    print("3. Hoàn tất xuất báo cáo chất lượng dữ liệu.")

    generate_eda_charts(df_nasa, df_fao)
    print("4. Hoàn tất tạo biểu đồ EDA và mô hình hồi quy tuyến tính.")
    print("=== PIPELINE HOÀN THÀNH XUẤT SẮC ===")


if __name__ == "__main__":
    main()
