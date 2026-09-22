from pathlib import Path

import pandas as pd
import plotly.express as px

ROOT = Path(__file__).resolve().parents[2]
PROC = ROOT / "processed" / "quan"
OUT = ROOT / "eda" / "quan" / "bieu_do_tuong_tac"
OUT.mkdir(parents=True, exist_ok=True)

def main():
    nat = pd.read_csv(PROC / "co2_quoc_gia.csv")
    sec = pd.read_csv(PROC / "co2_theo_nganh.csv")
    ren = pd.read_csv(PROC / "nang_luong_tai_tao.csv")
    world = pd.read_csv(PROC / "co2_toan_cau.csv")
    world = world[(world["year"] >= 1970) & (world["year"] <= 2024)]

    figs = {}
    figs["01_line_co2_toan_cau"] = px.area(
        world, x="year", y="co2",
        title="Phát thải CO₂ toàn cầu 1970–2024 (Mt/năm, OWID/GCP – dòng World)",
        labels={"year": "Năm", "co2": "Mt CO₂"})
    top = nat[nat["year"] == 2023].nlargest(15, "co2").sort_values("co2")
    figs["02_bar_top15"] = px.bar(
        top, x="co2", y="country", orientation="h", color="continent",
        title="Top 15 quốc gia phát thải CO₂ năm 2023 (Mt)",
        labels={"co2": "Mt CO₂", "country": "", "continent": "Châu lục"})
    snap = nat[nat["year"] == 2023]
    figs["03_choropleth_co2pc"] = px.choropleth(
        snap, locations="iso_alpha", color="co2_per_capita", hover_name="country",
        title="CO₂ bình quân đầu người năm 2023 (tấn/người)",
        labels={"co2_per_capita": "tấn/người"},
        color_continuous_scale="YlOrRd")
    sec_main = sec[(sec["year"] >= 1970) & (sec["year"] <= 2024)]
    piv = sec_main.groupby(["year", "sector"])["co2"].sum().reset_index()
    figs["04_stacked_area_nganh"] = px.area(
        piv, x="year", y="co2", color="sector",
        title="Cơ cấu phát thải CO₂ theo ngành 1970–2024 (EDGAR, Mt)",
        labels={"year": "Năm", "co2": "Mt CO₂", "sector": "Ngành"})
    tree = sec_main[sec_main["year"] == 2024].groupby("sector")["co2"].sum().reset_index()
    figs["05_treemap_nganh"] = px.treemap(
        tree, path=["sector"], values="co2",
        title="Tỷ trọng phát thải CO₂ theo ngành năm 2024 (EDGAR)")
    j = nat[nat["year"] == 2023][["iso_alpha", "country", "continent",
                                  "co2_per_capita"]].merge(
        ren[ren["year"] == 2023][["iso_alpha", "renewable_percent"]],
        on="iso_alpha", how="inner").dropna()
    figs["06_scatter_co2pc_renewable"] = px.scatter(
        j, x="renewable_percent", y="co2_per_capita", color="continent",
        hover_name="country", size_max=10,
        title="CO₂/người và tỷ trọng năng lượng tái tạo 2023",
        labels={"renewable_percent": "% tái tạo (tiêu thụ cuối cùng)",
                "co2_per_capita": "tấn CO₂/người", "continent": "Châu lục"})

    for name, fig in figs.items():
        fig.write_html(OUT / f"{name}.html", include_plotlyjs="cdn")
    print("Plotly OK:", sorted(p.name for p in OUT.glob("*.html")))

if __name__ == "__main__":
    main()
