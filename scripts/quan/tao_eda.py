from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "eda" / "quan" / "bieu_do_tinh"
PROC = ROOT / "processed" / "quan"

sns.set_theme(style="whitegrid")
plt.rcParams.update({
    "figure.dpi": 150,
    "font.family": "DejaVu Sans",
    "font.size": 10,
})
OUT.mkdir(parents=True, exist_ok=True)

def main():
    nat = pd.read_csv(PROC / "co2_quoc_gia.csv")
    sec = pd.read_csv(PROC / "co2_theo_nganh.csv")
    ren = pd.read_csv(PROC / "nang_luong_tai_tao.csv")
    world = pd.read_csv(PROC / "co2_toan_cau.csv")

    fig, ax = plt.subplots(figsize=(8, 4.2))
    w = world[(world["year"] >= 1970) & (world["year"] <= 2024)]
    ax.plot(w["year"], w["co2"], lw=2)
    ax.set_title("Phát thải CO₂ toàn cầu 1970–2024 (dòng World, OWID/GCP)")
    ax.set_xlabel("Năm"); ax.set_ylabel("Mt CO₂ / năm")
    fig.tight_layout(); fig.savefig(OUT / "01_line_co2_toan_cau.png"); plt.close(fig)

    top = nat[nat["year"] == 2023].nlargest(15, "co2").sort_values("co2")
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(top["country"], top["co2"])
    ax.set_title("Top 15 quốc gia phát thải CO₂ năm 2023 (Mt)")
    ax.set_xlabel("Mt CO₂")
    fig.tight_layout(); fig.savefig(OUT / "02_bar_top15_quoc_gia.png"); plt.close(fig)

    sec_main = sec[(sec["year"] >= 1970) & (sec["year"] <= 2024)]
    piv = sec_main.groupby(["year", "sector"])["co2"].sum().unstack(fill_value=0).sort_index()
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.stackplot(piv.index, *[piv[c] for c in piv.columns], labels=piv.columns, alpha=0.85)
    ax.legend(ncol=2, fontsize=8, loc="upper left")
    ax.set_title("Cơ cấu phát thải CO₂ theo ngành 1970–2024 (EDGAR, Mt)")
    ax.set_xlabel("Năm"); ax.set_ylabel("Mt CO₂")
    fig.tight_layout(); fig.savefig(OUT / "03_area_co_cau_nganh.png"); plt.close(fig)

    j = nat[nat["year"] == 2023][["iso_alpha", "country", "continent",
                                  "co2_per_capita"]].merge(
        ren[ren["year"] == 2023][["iso_alpha", "renewable_percent"]],
        on="iso_alpha", how="inner").dropna()
    fig, ax = plt.subplots(figsize=(8, 4.8))
    sns.scatterplot(data=j, x="renewable_percent", y="co2_per_capita",
                    hue="continent", alpha=0.7, ax=ax)
    ax.set_title(f"CO₂/người và tỷ trọng năng lượng tái tạo 2023 (n={len(j)})")
    ax.set_xlabel("Năng lượng tái tạo (% tiêu thụ cuối cùng)")
    ax.set_ylabel("Tấn CO₂ / người")
    ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(OUT / "04_scatter_co2pc_renewable.png"); plt.close(fig)

    cov = pd.DataFrame({
        "CO₂ (quốc gia có số liệu)": nat.groupby("year")["co2"].apply(lambda s: s.notna().sum()),
        "Tái tạo (quốc gia có số liệu)": ren.groupby("year").size(),
    })
    cov = cov.loc[1970:2024]
    fig, ax = plt.subplots(figsize=(8, 4.2))
    cov.plot(ax=ax, marker="o", ms=3)
    ax.set_title("Độ phủ quốc gia theo năm: CO₂ và năng lượng tái tạo")
    ax.set_xlabel("Năm"); ax.set_ylabel("Số quốc gia")
    fig.tight_layout(); fig.savefig(OUT / "05_line_do_phu_du_lieu.png"); plt.close(fig)

    print("EDA OK:", sorted(p.name for p in OUT.glob("*.png")))
    print(f"scatter-2023 n={len(j)}, corr={j['co2_per_capita'].corr(j['renewable_percent']):.3f}")

if __name__ == "__main__":
    main()
