from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

ROOT = Path(__file__).resolve().parent
PROC = ROOT.parents[1] / "data/du_lieu_da_xu_ly/quan"
OUT = ROOT / "bieu_do/tuong_tac"
CHARTS = [
    ("01_line_co2_toan_cau", "Lượng CO₂ toàn cầu"),
    ("02_bar_top15", "Quốc gia có lượng CO₂ cao nhất"),
    ("03_choropleth_co2pc", "CO₂ bình quân đầu người"),
    ("04_stacked_area_nganh", "Lượng CO₂ theo ngành"),
    ("05_treemap_nganh", "Tỷ trọng CO₂ theo ngành"),
    ("06_scatter_co2pc_renewable", "CO₂/người và năng lượng tái tạo"),
]
CONTINENT_COLORS = {"Africa": "#00A881", "Asia": "#E9604D", "Europe": "#9563CC",
                    "North America": "#5575CE", "Oceania": "#19A5B8", "South America": "#E89741"}
SECTOR_NAMES = {"Power Industry": "Điện năng", "Transport": "Giao thông",
                "Industrial Combustion": "Đốt công nghiệp", "Buildings": "Tòa nhà",
                "Processes": "Quá trình công nghiệp", "Fuel Production": "Sản xuất nhiên liệu",
                "Agriculture": "Nông nghiệp", "Waste": "Chất thải"}
SECTOR_COLORS = dict(zip(sorted(SECTOR_NAMES),
                         ["#709CBA", "#D37C65", "#69A58D", "#A082B2", "#DEA45F", "#4BA5AC", "#5576A7", "#8DAB69"]))
SECTOR_COLORS.update({name: SECTOR_COLORS[key] for key, name in SECTOR_NAMES.items()})


def build_figures(series, countries, sectors, map_countries=None):
    latest = countries[countries.year == series.year.max()]
    map_data = countries if map_countries is None else map_countries
    map_data = map_data.dropna(subset=["co2_per_capita"]).sort_values("year")
    map_data = map_data[(map_data.year % 10 == 0) | map_data.year.isin([map_data.year.min(), map_data.year.max()])]
    labels = {"year": "Năm", "co2": "CO₂ (triệu tấn)", "country": "Quốc gia",
              "continent": "Châu lục", "sector": "Ngành", "co2_per_capita": "CO₂/người (tấn)",
              "renewable_percent": "Năng lượng tái tạo (%)"}
    top = latest.dropna(subset=["co2"]).nlargest(15, "co2").sort_values("co2")
    areas = sectors.groupby(["year", "sector"], as_index=False).co2.sum(min_count=1)
    tree = areas[areas.year == series.year.max()].dropna(subset=["co2"])
    tree = tree[tree.co2 > 0].assign(share=lambda data: data.co2 / data.co2.sum() * 100)
    paired = latest.dropna(subset=["co2_per_capita", "renewable_percent"])
    figures = {
        "01_line_co2_toan_cau": px.area(series.sort_values("year"), x="year", y="co2", labels=labels,
                                       color_discrete_sequence=["#1689E8"]),
        "02_bar_top15": px.bar(top, x="co2", y="country", orientation="h", color="continent",
                               color_discrete_map=CONTINENT_COLORS, labels=labels),
        "03_choropleth_co2pc": px.choropleth(
            map_data,
            locations="iso_alpha", color="co2_per_capita", animation_frame="year", animation_group="iso_alpha",
            hover_name="country", range_color=[0, 40], color_continuous_scale="YlOrRd", labels=labels),
        "04_stacked_area_nganh": px.area(areas, x="year", y="co2", color="sector", labels=labels,
                                         color_discrete_map=SECTOR_COLORS),
        "05_treemap_nganh": go.Figure(go.Treemap(
            labels=tree.sector, parents=[""] * len(tree), values=tree.co2,
            customdata=tree[["share"]], marker_colors=tree.sector.map(SECTOR_COLORS))),
        "06_scatter_co2pc_renewable": px.scatter(
            paired, x="renewable_percent", y="co2_per_capita", color="continent",
            hover_name="country", color_discrete_map=CONTINENT_COLORS, labels=labels),
    }
    if len(series) == 1:
        figures["01_line_co2_toan_cau"].update_traces(mode="lines+markers")
    figures["02_bar_top15"].update_yaxes(categoryorder="total ascending", title=None, tickmode="linear", dtick=1)
    figures["03_choropleth_co2pc"].update_coloraxes(
        colorbar=dict(tickvals=[0, 10, 20, 30, 40], ticktext=["0", "10", "20", "30", "≥40"]))
    world_map = figures["03_choropleth_co2pc"]
    if world_map.frames:
        world_map.update_layout(meta=dict(autoplay=True))
        world_map.layout.updatemenus[0].buttons = [
            dict(label="■ Dừng", method="relayout", args=[{"meta.autoplay": False}])]
    treemap = figures["05_treemap_nganh"]
    treemap.update_traces(
        texttemplate="%{label}<br>%{customdata[0]:.1f}%",
        hovertemplate="%{label}<br>%{value:,.1f} triệu tấn · %{customdata[0]:.1f}%<extra></extra>")
    figures["06_scatter_co2pc_renewable"].update_traces(marker_size=8)
    return figures


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    countries = pd.read_csv(PROC / "co2_quoc_gia.csv").merge(
        pd.read_csv(PROC / "nang_luong_tai_tao.csv")[["iso_alpha", "year", "renewable_percent"]],
        on=["iso_alpha", "year"], how="left", validate="one_to_one")
    countries = countries[countries.year.between(1970, 2024)]
    series = pd.read_csv(PROC / "co2_toan_cau.csv").query("1970 <= year <= 2024")
    sectors = pd.read_csv(PROC / "co2_theo_nganh.csv").query("1970 <= year <= 2024")
    figures = build_figures(series, countries, sectors)
    for name, title in CHARTS:
        figure = figures[name]
        figure.update_layout(template="plotly_white", title=title)
        animation = (ROOT.parents[1] / "bang_dieu_khien/nguyen_khang/tai_nguyen/eda.js").read_text() if figure.frames else None
        figure.write_html(OUT / f"{name}.html", include_plotlyjs="cdn", config={"scrollZoom": False},
                          auto_play=False, post_script=animation)
    print("Plotly OK")


if __name__ == "__main__":
    main()
