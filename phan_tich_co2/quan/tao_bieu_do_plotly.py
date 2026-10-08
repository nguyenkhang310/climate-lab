from pathlib import Path
import sys

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from bang_dieu_khien.nguyen_khang.thap_ky import country_decade_means  # noqa: E402

ROOT = Path(__file__).resolve().parent
PROC = ROOT.parents[1] / "data/du_lieu_da_xu_ly/quan"
OUT = ROOT / "bieu_do/tuong_tac"
CHARTS = [
    ("01_line_co2_toan_cau", "Lượng CO₂ toàn cầu"),
    ("02_bar_top15", "Quốc gia có CO₂ trung bình năm cao nhất"),
    ("03_choropleth_co2pc", "CO₂/người trung bình theo thập kỷ"),
    ("04_stacked_area_chau_luc", "Lượng CO₂ theo châu lục"),
    ("05_treemap_nganh", "Tỷ trọng CO₂ theo ngành"),
    ("06_scatter_co2pc_renewable", "CO₂/người và năng lượng tái tạo"),
]
CONTINENT_COLORS = {"Africa": "#00A881", "Asia": "#E9604D", "Europe": "#9563CC",
                    "North America": "#5575CE", "Oceania": "#19A5B8", "South America": "#E89741",
                    "Antarctica": "#96A7BA"}
SECTOR_NAMES = {"Power Industry": "Điện năng", "Transport": "Giao thông",
                "Industrial Combustion": "Đốt công nghiệp", "Buildings": "Tòa nhà",
                "Processes": "Quá trình công nghiệp", "Fuel Production": "Sản xuất nhiên liệu",
                "Agriculture": "Nông nghiệp", "Waste": "Chất thải"}
SECTOR_COLORS = dict(zip(sorted(SECTOR_NAMES),
                         ["#709CBA", "#D37C65", "#69A58D", "#A082B2", "#DEA45F", "#4BA5AC", "#5576A7", "#8DAB69"]))
SECTOR_COLORS.update({name: SECTOR_COLORS[key] for key, name in SECTOR_NAMES.items()})


def sector_coverage_note(sectors):
    if sectors.empty:
        return "Chưa có dữ liệu ngành cho phạm vi này"
    coverage = sectors.groupby(["iso_alpha", "year"]).co2.agg(["count", "size"])
    missing = int(coverage["count"].lt(coverage["size"]).sum())
    note = "Tỷ trọng trong các ngành có số liệu"
    if missing:
        note += f" · {missing}/{len(coverage)} nhóm quốc gia–năm thiếu giá trị ngành"
    if sectors.iso_alpha.eq("SCG").any():
        note += " · Serbia và Montenegro dùng chuỗi gộp chung"
    return note


def renewable_coverage_note(countries):
    counts = countries.groupby("year").renewable_percent.count()
    counts = counts[counts.gt(0)]
    if counts.empty:
        return "Chưa có dữ liệu tái tạo trong kỳ"
    note = f"Tái tạo: {counts.index.min()}–{counts.index.max()} · {counts.index.max()}: {counts.iloc[-1]} quốc gia có số liệu"
    if counts.nunique() > 1:
        note += f" · Độ phủ thay đổi ({counts.min()}–{counts.max()} quốc gia/năm)"
    return note


def build_figures(series, countries, sectors):
    keys = ["iso_alpha", "country", "continent"]
    averages = countries.groupby(keys, as_index=False, dropna=False).agg(
        co2=("co2", "mean"), years=("co2", "count"))
    map_data = country_decade_means(countries, "co2_per_capita")
    labels = {"year": "Năm", "co2": "CO₂ (triệu tấn)", "country": "Quốc gia",
              "continent": "Châu lục", "sector": "Ngành", "co2_per_capita": "CO₂/người (tấn)",
              "renewable_percent": "Năng lượng tái tạo (%)", "period": "Thập kỷ",
              "years": "Số năm có dữ liệu"}
    top = averages.dropna(subset=["co2"]).nlargest(15, "co2").sort_values("co2")
    continents = (
        countries.groupby(["year", "continent"], as_index=False, observed=True)
        .co2.sum(min_count=1)
        .dropna(subset=["co2"])
    )
    areas = sectors.groupby(["year", "sector"], as_index=False).co2.sum(min_count=1)
    tree = areas.groupby("sector", as_index=False).co2.mean().dropna(subset=["co2"])
    tree = tree[tree.co2 > 0].assign(share=lambda data: data.co2 / data.co2.sum() * 100)
    paired = countries.dropna(subset=["co2_per_capita", "renewable_percent"])
    paired = paired.groupby(keys, as_index=False, dropna=False).agg(
        co2_per_capita=("co2_per_capita", "mean"), renewable_percent=("renewable_percent", "mean"),
        years=("year", "nunique"))
    figures = {
        "01_line_co2_toan_cau": px.area(series.sort_values("year"), x="year", y="co2", labels=labels,
                                       color_discrete_sequence=["#1689E8"]),
        "02_bar_top15": px.bar(top, x="co2", y="country", orientation="h", color="continent",
                               color_discrete_map=CONTINENT_COLORS, labels=labels, hover_data=["years"]),
        "03_choropleth_co2pc": px.choropleth(
            map_data,
            locations="iso_alpha", color="co2_per_capita", animation_frame="period", animation_group="iso_alpha",
            hover_name="country", hover_data=["period", "years"], range_color=[0, 40], color_continuous_scale="YlOrRd", labels=labels),
        "04_stacked_area_chau_luc": px.area(
            continents, x="year", y="co2", color="continent", labels=labels,
            color_discrete_map=CONTINENT_COLORS),
        "05_treemap_nganh": go.Figure(go.Treemap(
            labels=tree.sector, parents=[""] * len(tree), values=tree.co2,
            customdata=tree[["share"]], marker_colors=tree.sector.map(SECTOR_COLORS))),
        "06_scatter_co2pc_renewable": px.scatter(
            paired, x="renewable_percent", y="co2_per_capita", color="continent",
            hover_name="country", hover_data=["years"], color_discrete_map=CONTINENT_COLORS, labels=labels),
    }
    if len(series) == 1:
        figures["01_line_co2_toan_cau"].update_traces(mode="lines+markers")
    figures["02_bar_top15"].update_yaxes(categoryorder="total ascending", title=None, tickmode="linear", dtick=1)
    figures["03_choropleth_co2pc"].update_coloraxes(
        colorbar=dict(tickvals=[0, 10, 20, 30, 40], ticktext=["0", "10", "20", "30", "≥40"]))
    world_map = figures["03_choropleth_co2pc"]
    if world_map.frames:
        for button, label in zip(world_map.layout.updatemenus[0].buttons, ("▶ Phát", "■ Dừng")):
            button.update(label=label, execute=False)
        world_map.layout.sliders[0].update(x=.05, len=1)
    treemap = figures["05_treemap_nganh"]
    treemap.update_traces(
        texttemplate="%{label}<br>%{customdata[0]:.1f}%",
        hovertemplate="%{label}<br>TB %{value:,.1f} triệu tấn/năm · %{customdata[0]:.1f}%<extra></extra>")
    figures["02_bar_top15"].update_xaxes(title="CO₂ trung bình năm (triệu tấn/năm)")
    figures["06_scatter_co2pc_renewable"].update_xaxes(title="Năng lượng tái tạo trung bình (%)")
    figures["06_scatter_co2pc_renewable"].update_yaxes(title="CO₂/người trung bình (tấn/người/năm)")
    figures["06_scatter_co2pc_renewable"].update_traces(marker_size=8)
    figures["05_treemap_nganh"].update_layout(meta={"coverage_note": sector_coverage_note(sectors)})
    figures["06_scatter_co2pc_renewable"].update_layout(meta={"coverage_note": renewable_coverage_note(countries)})
    return figures


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    countries = pd.read_csv(PROC / "co2_quoc_gia.csv").merge(
        pd.read_csv(PROC / "nang_luong_tai_tao.csv")[["iso_alpha", "year", "renewable_percent"]],
        on=["iso_alpha", "year"], how="left", validate="one_to_one")
    countries = countries[countries.year.between(1850, 2024)]
    series = pd.read_csv(PROC / "co2_toan_cau.csv").query("1850 <= year <= 2024")
    sectors = pd.read_csv(PROC / "co2_theo_nganh.csv").query("1970 <= year <= 2024")
    figures = build_figures(series, countries, sectors)
    for name, title in CHARTS:
        figure = figures[name]
        note = (figure.layout.meta or {}).get("coverage_note", "")
        figure.update_layout(template="plotly_white", title=f"{title}<br><sup>{note}</sup>" if note else title)
        controls = (ROOT.parents[1] / "bang_dieu_khien/nguyen_khang/tai_nguyen/eda.js").read_text(encoding="utf-8") if figure.frames else None
        figure.write_html(OUT / f"{name}.html", include_plotlyjs="cdn", config={"scrollZoom": False},
                          auto_play=False, post_script=controls)
    print("Plotly OK")


if __name__ == "__main__":
    main()
