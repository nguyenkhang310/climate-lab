from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

ROOT = Path(__file__).resolve().parent
PROC = ROOT.parents[1] / "data/du_lieu_da_xu_ly/duc"
OUT = ROOT / "bieu_do/tuong_tac"
CHARTS = [
    ("01_xu_huong_nhiet_do_toan_cau", "Xu hướng nhiệt độ toàn cầu"),
    ("02_nhiet_do_theo_thap_ky", "Nhiệt độ trung bình theo thập kỷ"),
    ("03_ban_do_nhiet_do", "Bản đồ nhiệt độ theo quốc gia"),
    ("04_heatmap_chau_luc_thap_ky", "Nhiệt độ theo châu lục và thập kỷ"),
    ("05_phan_bo_nhiet_do_quoc_gia", "Phân bố nhiệt độ theo thập kỷ"),
    ("06_nhiet_do_theo_thang", "Chênh nhiệt độ theo tháng"),
]


def build_figures(series, countries, monthly, map_countries=None):
    series = series.sort_values("year")
    countries = countries.dropna(subset=["temperature_anomaly"]).copy()
    countries["decade"] = (countries.year // 10 * 10).astype(str)
    labels = {"year": "Năm", "temperature_anomaly": "Chênh nhiệt độ (°C)",
              "decade": "Thập kỷ", "country": "Quốc gia"}
    trend = go.Figure([
        go.Scatter(x=series.year, y=series.temperature_anomaly, name="Hằng năm",
                   mode="lines+markers" if len(series) == 1 else "lines", line=dict(color="#EF6B54", width=1.5)),
        go.Scatter(x=series.year, y=series.temperature_anomaly.rolling(5).mean(),
                   name="Trung bình 5 năm", mode="lines", line=dict(color="#B42335", width=2.5)),
    ])
    trend.update_layout(xaxis_title="Năm", yaxis_title=labels["temperature_anomaly"], hovermode="x unified")
    trend.add_hline(y=0, line_dash="dot", line_color="#96A7BA")
    trend.update_traces(hovertemplate="%{x}: %{y:+.2f} °C<extra>%{fullData.name}</extra>")
    decades = series.assign(decade=(series.year // 10 * 10).astype(str)).groupby("decade").agg(
        temperature_anomaly=("temperature_anomaly", "mean"), years=("temperature_anomaly", "count"))
    bars = go.Figure(go.Bar(
        x=decades.index, y=decades.temperature_anomaly,
        marker_color=["#3478B8" if v < 0 else "#D94835" for v in decades.temperature_anomaly],
        customdata=decades.years, text=decades.temperature_anomaly.map("{:+.2f}".format),
        textposition="outside", cliponaxis=False,
        hovertemplate="%{x} · %{customdata} năm có số liệu<br>%{y:+.2f} °C<extra></extra>"))
    bars.update_layout(xaxis_title="Thập kỷ", yaxis_title=labels["temperature_anomaly"])
    map_data = countries if map_countries is None else map_countries
    map_data = map_data.dropna(subset=["temperature_anomaly"]).sort_values("year")
    map_data = map_data[(map_data.year % 10 == 0) | map_data.year.isin([map_data.year.min(), map_data.year.max()])]
    world_map = px.choropleth(map_data,
                             locations="iso_alpha", color="temperature_anomaly",
                             animation_frame="year", animation_group="iso_alpha",
                             hover_name="country", range_color=[-6, 6],
                             color_continuous_scale="RdBu_r", labels=labels)
    if world_map.frames:
        world_map.update_layout(meta=dict(autoplay=True))
        world_map.layout.updatemenus[0].buttons = [
            dict(label="■ Dừng", method="relayout", args=[{"meta.autoplay": False}])]
    pivot = countries.pivot_table(index="continent", columns="decade", values="temperature_anomaly")
    heatmap = (px.imshow(pivot, text_auto=".2f", aspect="auto", range_color=[-2.5, 2.5],
                        color_continuous_scale="RdBu_r",
                        labels=dict(x="Thập kỷ", y="Châu lục", color="Chênh nhiệt độ (°C)"))
               if not pivot.empty else go.Figure())
    box = px.box(countries, x="decade", y="temperature_anomaly", color="decade",
                 points="outliers", hover_data=["country", "year"], labels=labels)
    by_month = monthly.groupby(["year", "month"]).temperature_anomaly.mean().groupby("month")
    months = by_month.agg(["mean", "count"]).reindex(range(1, 13))
    profile = go.Figure(go.Scatter(
        x=months.index, y=months["mean"], customdata=months["count"], mode="lines+markers",
        line=dict(color="#D94835", width=2.5), marker_size=7, connectgaps=False,
        hovertemplate="Tháng %{x}<br>Chênh nhiệt độ: %{y:+.2f} °C<br>%{customdata} năm có số liệu<extra></extra>"))
    profile.update_layout(xaxis=dict(title="Tháng", tickmode="array", tickvals=list(range(1, 13))),
                          yaxis_title=labels["temperature_anomaly"])
    profile.add_hline(y=0, line_dash="dot", line_color="#96A7BA")
    return dict(zip([name for name, _ in CHARTS], [trend, bars, world_map, heatmap, box, profile]))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    figures = build_figures(pd.read_csv(PROC / "nhiet_do_toan_cau.csv"),
                            pd.read_csv(PROC / "nhiet_do_quoc_gia.csv"),
                            pd.read_csv(PROC / "nhiet_do_theo_thang.csv").query("iso_alpha == 'WLD'"))
    for name, title in CHARTS:
        figure = figures[name]
        figure.update_layout(template="plotly_white", title=title)
        animation = (ROOT.parents[1] / "bang_dieu_khien/nguyen_khang/tai_nguyen/eda.js").read_text() if figure.frames else None
        figure.write_html(OUT / f"{name}.html", include_plotlyjs="cdn", config={"scrollZoom": False},
                          auto_play=False, post_script=animation)
    print("Plotly OK:", list(figures))


if __name__ == "__main__":
    main()
