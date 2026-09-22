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
        title="Phat thai CO2 toan cau 1970-2024 (Mt/nam, OWID/GCP - dong World)",
        labels={"year": "Nam", "co2": "Mt CO2"})
    top = nat[nat["year"] == 2023].nlargest(15, "co2").sort_values("co2")
    figs["02_bar_top15"] = px.bar(
        top, x="co2", y="country", orientation="h", color="continent",
        title="Top 15 quoc gia phat thai CO2 nam 2023 (Mt)",
        labels={"co2": "Mt CO2", "country": "", "continent": "Chau luc"})
    snap = nat[nat["year"] == 2023]
    figs["03_choropleth_co2pc"] = px.choropleth(
        snap, locations="iso_alpha", color="co2_per_capita", hover_name="country",
        title="CO2 binh quan dau nguoi nam 2023 (tan/nguoi)",
        labels={"co2_per_capita": "tan/nguoi"},
        color_continuous_scale="YlOrRd")
    piv = sec.groupby(["year", "sector"])["co2"].sum().reset_index()
    figs["04_stacked_area_nganh"] = px.area(
        piv, x="year", y="co2", color="sector",
        title="Co cau phat thai CO2 theo nganh 1970-2025 (EDGAR, Mt)",
        labels={"year": "Nam", "co2": "Mt CO2", "sector": "Nganh"})
    y_last = int(sec["year"].max())
    tree = sec[sec["year"] == y_last].groupby("sector")["co2"].sum().reset_index()
    figs["05_treemap_nganh"] = px.treemap(
        tree, path=["sector"], values="co2",
        title=f"Ty trong phat thai CO2 theo nganh nam {y_last} (EDGAR)")
    j = nat[nat["year"] == 2023][["iso_alpha", "country", "continent",
                                  "co2_per_capita"]].merge(
        ren[ren["year"] == 2023][["iso_alpha", "renewable_percent"]],
        on="iso_alpha", how="inner").dropna()
    figs["06_scatter_co2pc_renewable"] = px.scatter(
        j, x="renewable_percent", y="co2_per_capita", color="continent",
        hover_name="country", size_max=10,
        title="CO2/nguoi vs ty trong nang luong tai tao 2023",
        labels={"renewable_percent": "% tai tao (tieu thu cuoi cung)",
                "co2_per_capita": "tan CO2/nguoi", "continent": "Chau luc"})

    for name, fig in figs.items():
        fig.write_html(OUT / f"{name}.html", include_plotlyjs="cdn")
    print("Plotly OK:", sorted(p.name for p in OUT.glob("*.html")))

if __name__ == "__main__":
    main()
