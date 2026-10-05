from pathlib import Path

import pandas as pd
import plotly.express as px

ROOT = Path(__file__).resolve().parent
PROC = ROOT / "du_lieu_sach"
OUT = ROOT / "bieu_do/tuong_tac"
OUT.mkdir(parents=True, exist_ok=True)


PLOTLY_CONFIG = {"scrollZoom": False}

CONTINENT_COLORS = {
    "Africa": "#00CC96",
    "Asia": "#EF553B",
    "Europe": "#AB63FA",
    "North America": "#636EFA",
    "Oceania": "#19D3F3",
    "South America": "#FFA15A",
}

def main():
    nat = pd.read_csv(PROC / "co2_quoc_gia.csv")
    sec = pd.read_csv(PROC / "co2_theo_nganh.csv")
    ren = pd.read_csv(PROC / "nang_luong_tai_tao.csv")
    world = pd.read_csv(PROC / "co2_toan_cau.csv")
    world = world[(world["year"] >= 1970) & (world["year"] <= 2024)]

    figs = {}
    figs["01_line_co2_toan_cau"] = px.area(
        world, x="year", y="co2",
        title="CO₂ toàn cầu tăng ~2,6 lần 1970-2024, chưa đảo chiều (triệu tấn/năm, OWID/GCP - dòng World)",
        labels={"year": "Năm", "co2": "Triệu tấn CO₂"})
    top = nat[nat["year"] == 2023].nlargest(15, "co2").sort_values("co2")
    figs["02_bar_top15"] = px.bar(
        top, x="co2", y="country", orientation="h", color="continent",
        color_discrete_map=CONTINENT_COLORS,
        title="Top 15 năm 2023: Trung Quốc gấp ~2,5 lần Mỹ (triệu tấn)",
        labels={"co2": "Triệu tấn CO₂", "country": "", "continent": "Châu lục"}
        )
    figs["02_bar_top15"].update_yaxes(categoryorder='total ascending')
    anim = nat[(nat["year"] >= 1970) & (nat["year"] <= 2024)]
    figs["03_choropleth_co2pc"] = px.choropleth(
        anim, locations="iso_alpha", color="co2_per_capita", hover_name="country",
        animation_frame="year", range_color=[0, 40],
        title="CO₂/người theo năm: xếp hạng đảo lộn so với tổng thải (tấn/người, kéo thanh năm để xem)",
        labels={"co2_per_capita": "tấn/người", "year": "Năm"},
        color_continuous_scale="YlOrRd")
    sec_main = sec[(sec["year"] >= 1970) & (sec["year"] <= 2024)]
    piv = sec_main.groupby(["year", "sector"])["co2"].sum().reset_index()
    figs["04_stacked_area_nganh"] = px.area(
        piv, x="year", y="co2", color="sector",
        title="Điện là đầu mối CO₂ theo ngành 1970-2024 (EDGAR, triệu tấn)",
        labels={"year": "Năm", "co2": "Triệu tấn CO₂", "sector": "Ngành"})
    tree = sec_main[sec_main["year"] == 2024].groupby("sector")["co2"].sum().reset_index()
    tree["share"] = tree["co2"] / tree["co2"].sum() * 100
    figs["05_treemap_nganh"] = px.treemap(
        tree, path=["sector"], values="co2", custom_data=["share"],
        title="Điện ~40,8% CO₂ năm 2024; nông nghiệp thấp vì EDGAR chỉ tính CO₂")
    figs["05_treemap_nganh"].update_traces(
        texttemplate="%{label}<br>%{customdata[0]:.1f}%",
        hovertemplate="%{label}<br>%{value:,.1f} triệu tấn (%{customdata[0]:.1f}%)<extra></extra>")
    j = nat[nat["year"] == 2023][["iso_alpha", "country", "continent",
                                  "co2_per_capita"]].merge(
        ren[ren["year"] == 2023][["iso_alpha", "renewable_percent"]],
        on="iso_alpha", how="inner").dropna()
    figs["06_scatter_co2pc_renewable"] = px.scatter(
        j, x="renewable_percent", y="co2_per_capita", color="continent",
        color_discrete_map=CONTINENT_COLORS,
        hover_name="country", size_max=10,
        title="Tái tạo cao đi cùng CO₂/người thấp hơn, phân tán rộng - mô tả, không nhân-quả (2023)",
        labels={"renewable_percent": "% tái tạo (tiêu thụ cuối cùng)",
                "co2_per_capita": "tấn CO₂/người", "continent": "Châu lục"})

    for name, fig in figs.items():
        fig.write_html(OUT / f"{name}.html", include_plotlyjs="cdn", config=PLOTLY_CONFIG)
    print("Plotly OK:", sorted(p.name for p in OUT.glob("*.html")))

if __name__ == "__main__":
    main()
