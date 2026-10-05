from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "bieu_do/tinh"
PROC = ROOT / "du_lieu_sach"

sns.set_theme(style="whitegrid")
plt.rcParams.update({
    "figure.dpi": 150,
    "font.family": "DejaVu Sans",
    "font.size": 10,
})
OUT.mkdir(parents=True, exist_ok=True)

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

    fig, ax = plt.subplots(figsize=(8, 4.2))
    w = world[(world["year"] >= 1970) & (world["year"] <= 2024)]
    ax.plot(w["year"], w["co2"], lw=2)
    ax.set_title("CO₂ toàn cầu tăng ~2,6 lần 1970-2024, chưa đảo chiều (dòng World, OWID/GCP)")
    ax.set_xlabel("Năm"); ax.set_ylabel("Triệu tấn CO₂ / năm")
    last = w.iloc[-1]
    ax.text(0.03, 0.92, f"{int(last['year'])}: {last['co2']:,.0f} Mt",
            transform=ax.transAxes, fontsize=9, va="top", ha="left",
            bbox=dict(facecolor="white", alpha=0.8, edgecolor="none"))
    fig.tight_layout(); fig.savefig(OUT / "01_line_co2_toan_cau.png"); plt.close(fig)

    top = nat[nat["year"] == 2023].nlargest(15, "co2").sort_values("co2")
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(top["country"], top["co2"])
    ax.set_title("Top 15 năm 2023: Trung Quốc gấp ~2,5 lần Mỹ (triệu tấn)")
    ax.set_xlabel("Triệu tấn CO₂")
    fig.tight_layout(); fig.savefig(OUT / "02_bar_top15_quoc_gia.png"); plt.close(fig)

    sec_main = sec[(sec["year"] >= 1970) & (sec["year"] <= 2024)]
    piv = sec_main.groupby(["year", "sector"])["co2"].sum().unstack(fill_value=0).sort_index()
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.stackplot(piv.index, *[piv[c] for c in piv.columns], labels=piv.columns, alpha=0.85)
    ax.legend(ncol=2, fontsize=8, loc="upper left")
    ax.set_title("Điện ~40,8% CO₂ năm 2024 - đầu mối giảm phát thải (EDGAR, triệu tấn)")
    ax.set_xlabel("Năm"); ax.set_ylabel("Triệu tấn CO₂")
    fig.tight_layout(); fig.savefig(OUT / "03_area_co_cau_nganh.png"); plt.close(fig)

    j = nat[nat["year"] == 2023][["iso_alpha", "country", "continent",
                                  "co2_per_capita"]].merge(
        ren[ren["year"] == 2023][["iso_alpha", "renewable_percent"]],
        on="iso_alpha", how="inner").dropna()
    fig, ax = plt.subplots(figsize=(8, 4.8))
    corr = j["co2_per_capita"].corr(j["renewable_percent"])
    sns.scatterplot(data=j, x="renewable_percent", y="co2_per_capita",
                    hue="continent", hue_order=sorted(CONTINENT_COLORS),
                    palette=CONTINENT_COLORS, alpha=0.7, ax=ax)
    ax.set_title(f"Tái tạo cao đi cùng CO₂/người thấp hơn, nhưng phân tán rộng (2023, n={len(j)}, r≈{corr:.2f})")
    ax.set_xlabel("Năng lượng tái tạo (% tiêu thụ cuối cùng)")
    ax.set_ylabel("Tấn CO₂ / người")
    fig.text(0.5, 0.01, "Mối liên hệ mô tả, không phải nhân-quả.", ha="center", fontsize=8)
    ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(OUT / "04_scatter_co2pc_renewable.png"); plt.close(fig)

    cov = pd.DataFrame({
        "CO₂ (quốc gia có số liệu)": nat.groupby("year")["co2"].apply(lambda s: s.notna().sum()),
        "Tái tạo (quốc gia có số liệu)": ren.groupby("year")["renewable_percent"].apply(lambda s: s.notna().sum()),
    })
    cov = cov.loc[1970:2024]
    fig, ax = plt.subplots(figsize=(8, 4.2))
    cov.plot(ax=ax, marker="o", ms=3)
    ax.set_title("Độ phủ: CO₂ đủ từ 1970, tái tạo từ 1990 - 2024 còn sơ bộ (84 nước)")
    ax.set_xlabel("Năm"); ax.set_ylabel("Số quốc gia")
    ax.annotate("2024 sơ bộ: 84 nước",
                xy=(2024, cov.loc[2024, "Tái tạo (quốc gia có số liệu)"]),
                xytext=(-110, 60), textcoords="offset points", fontsize=9,
                arrowprops=dict(arrowstyle="->", lw=1))
    fig.tight_layout(); fig.savefig(OUT / "05_line_do_phu_du_lieu.png"); plt.close(fig)

    print("EDA OK:", sorted(p.name for p in OUT.glob("*.png")))
    print(f"scatter-2023 n={len(j)}, corr={j['co2_per_capita'].corr(j['renewable_percent']):.3f}")

if __name__ == "__main__":
    main()
