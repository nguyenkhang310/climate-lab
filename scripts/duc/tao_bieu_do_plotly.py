"""
Tạo toàn bộ 6 biểu đồ tương tác Plotly (HTML) cho phần Nhiệt độ Toàn cầu & Quốc gia (Đức).
Đồng bộ hóa các biểu đồ với các chuẩn:
- include_plotlyjs='cdn' để tối ưu dung lượng và loại bỏ mã thư viện nhúng.
- Tâm thang màu cố định tại 0°C đối với Heatmap và Bản đồ.
- Bản đồ thế giới hỗ trợ thanh trượt chọn năm (1961–2025).
- Tích hợp mô hình dự báo hồi quy tuyến tính OLS đến năm 2050 kèm dải tin cậy 95%.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression

ROOT = Path(__file__).resolve().parents[2]
PROC = ROOT / "processed" / "duc"
OUT = ROOT / "eda" / "duc" / "bieu_do_tuong_tac"
OUT.mkdir(parents=True, exist_ok=True)


def main() -> None:
    df_nasa = pd.read_csv(PROC / "nhiet_do_toan_cau.csv")
    df_fao = pd.read_csv(PROC / "nhiet_do_quoc_gia.csv")

    # 1. Line chart: Xu hướng nhiệt độ toàn cầu qua thời gian (1880–2025)
    rolling_5 = df_nasa["temperature_anomaly"].rolling(5, center=True).mean()
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(
        x=df_nasa["year"], y=df_nasa["temperature_anomaly"],
        mode="lines+markers", name="Nhiệt độ hàng năm",
        line=dict(color="#f46d43", width=1.5), marker=dict(size=4, color="#f46d43"),
        hovertemplate="Năm %{x}: <b>%{y:.2f}°C</b><extra></extra>"
    ))
    fig1.add_trace(go.Scatter(
        x=df_nasa["year"], y=rolling_5,
        mode="lines", name="Trung bình 5 năm (Xu hướng)",
        line=dict(color="#a50026", width=3),
        hovertemplate="Xu hướng 5 năm (%{x}): <b>%{y:.2f}°C</b><extra></extra>"
    ))
    fig1.add_hline(y=0, line_dash="dash", line_color="blue", annotation_text="Baseline 1951–1980 (0°C)")
    fig1.add_annotation(
        x=2024, y=1.29, text="Kỷ lục 2024 (+1.29°C)",
        showarrow=True, arrowhead=2, ax=-50, ay=-35,
        bgcolor="#ffebee", bordercolor="#d32f2f"
    )
    fig1.update_layout(
        title="<b>Xu hướng Độ lệch Nhiệt độ Toàn cầu qua Thời gian (1880–2025)</b>",
        xaxis_title="Năm", yaxis_title="Độ lệch nhiệt độ so với mốc 1951–1980 (°C)",
        template="plotly_white", hovermode="x unified",
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01, bgcolor="rgba(255,255,255,0.8)")
    )
    fig1.write_html(OUT / "01_xu_huong_nhiet_do_toan_cau.html", include_plotlyjs="cdn")

    # 2. Bar chart: Nhiệt độ trung bình theo thập kỷ (1880s–2020s)
    df_dec = df_nasa.groupby("decade")["temperature_anomaly"].mean().reset_index()
    bar_colors = ["#4575b4" if v < 0 else "#d73027" for v in df_dec["temperature_anomaly"]]
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        x=[f"{d}s" for d in df_dec["decade"]],
        y=df_dec["temperature_anomaly"],
        marker_color=bar_colors,
        text=[f"{v:+.2f}°C" for v in df_dec["temperature_anomaly"]],
        textposition="outside",
        hoverinfo="text",
        hovertext=[f"Thập kỷ: <b>{r.decade}s</b><br>Độ lệch trung bình: <b>{r.temperature_anomaly:+.3f}°C</b>" for r in df_dec.itertuples()],
        name="Nhiệt độ thập kỷ"
    ))
    fig2.add_hline(y=0, line_color="black", line_width=1)
    fig2.update_layout(
        title="<b>Độ lệch Nhiệt độ Trung bình Toàn cầu theo Thập kỷ (1880s–2020s) [NASA GISS]</b>",
        xaxis_title="Thập kỷ", yaxis_title="Độ lệch nhiệt độ trung bình (°C)",
        template="plotly_white"
    )
    fig2.write_html(OUT / "02_nhiet_do_theo_thap_ky.html", include_plotlyjs="cdn")

    # 3. Choropleth Map: Bản đồ nhiệt độ thế giới kèm thanh trượt chọn năm (1961–2025)
    df_map_all = df_fao.dropna(subset=["temperature_anomaly"]).sort_values("year").copy()
    fig3 = px.choropleth(
        df_map_all,
        locations="iso_alpha",
        color="temperature_anomaly",
        hover_name="country",
        animation_frame="year",
        color_continuous_scale="RdBu_r",
        color_continuous_midpoint=0,
        range_color=[-3.0, 3.0],
        title="<b>Bản đồ Độ lệch Nhiệt độ Thế giới theo Năm (1961–2025) [Tâm 0°C]</b>",
        labels={"temperature_anomaly": "Độ lệch (°C)"},
        template="plotly_white"
    )
    fig3.update_layout(
        coloraxis_colorbar=dict(title="Độ lệch (°C)"),
        margin=dict(l=0, r=0, t=50, b=0)
    )
    fig3.write_html(OUT / "03_ban_do_nhiet_do.html", include_plotlyjs="cdn")

    # 4. Heatmap: Nhiệt độ theo Châu lục x Thập kỷ (Đặt tâm tại 0°C)
    piv = df_fao.pivot_table(index="continent", columns="decade", values="temperature_anomaly", aggfunc="mean")
    piv.columns = [f"{c}s" for c in piv.columns]
    fig4 = px.imshow(
        piv,
        labels=dict(x="Thập kỷ", y="Châu lục", color="Độ lệch (°C)"),
        x=piv.columns.tolist(), y=piv.index.tolist(),
        color_continuous_scale="RdBu_r", color_continuous_midpoint=0,
        range_color=[-2.5, 2.5], text_auto=".2f",
        title="<b>Biểu đồ Nhiệt theo Châu lục và Thập kỷ (1960s–2020s) [Tâm 0°C]</b>",
        template="plotly_white"
    )
    fig4.update_layout(xaxis_title="Thập kỷ", yaxis_title="Châu lục", coloraxis_colorbar=dict(title="Độ lệch (°C)"))
    fig4.write_html(OUT / "04_heatmap_chau_luc_thap_ky.html", include_plotlyjs="cdn")

    # 5. Boxplot: Phân bố nhiệt độ giữa các quốc gia qua từng thập kỷ
    df_box = df_fao.copy()
    df_box["decade_str"] = df_box["decade"].astype(str) + "s"
    fig5 = px.box(
        df_box, x="decade_str", y="temperature_anomaly", color="decade_str",
        points="outliers", hover_data=["country", "year"],
        labels={"decade_str": "Thập kỷ", "temperature_anomaly": "Độ lệch nhiệt độ (°C)", "country": "Quốc gia", "year": "Năm"},
        title="<b>Phân bố Độ lệch Nhiệt độ giữa các Quốc gia qua từng Thập kỷ (Boxplot Tương tác)</b>",
        template="plotly_white"
    )
    fig5.add_hline(y=0, line_dash="dash", line_color="blue", annotation_text="Baseline 1951–1980 (0°C)")
    fig5.update_layout(xaxis_title="Thập kỷ", yaxis_title="Độ lệch nhiệt độ (°C)", showlegend=False)
    fig5.write_html(OUT / "05_phan_bo_nhiet_do_quoc_gia.html", include_plotlyjs="cdn")

    # 6. Biểu đồ Dự báo Hồi quy Tuyến tính (Linear Regression) đến năm 2050
    df_mod = df_nasa[df_nasa["year"] >= 1970].copy()
    train = df_mod[df_mod["year"] <= 2014]
    test = df_mod[df_mod["year"] >= 2015]

    lr_full = LinearRegression()
    lr_full.fit(df_mod[["year"]], df_mod["temperature_anomaly"])
    full_pred = lr_full.predict(df_mod[["year"]])
    slope_decade = lr_full.coef_[0] * 10

    future_years = np.arange(2025, 2051)
    future_df = pd.DataFrame({"year": future_years})
    future_pred = lr_full.predict(future_df)

    residuals = df_mod["temperature_anomaly"] - full_pred
    dof = len(df_mod) - 2
    s_err = np.sqrt(np.sum(residuals**2) / dof)
    x_mean = df_mod["year"].mean()
    ss_x = np.sum((df_mod["year"] - x_mean)**2)
    pi = 1.96 * s_err * np.sqrt(1 + 1 / len(df_mod) + (future_years - x_mean)**2 / ss_x)
    upper_pi = future_pred + pi
    lower_pi = future_pred - pi

    pre = df_nasa[df_nasa["year"] < 1970]
    fig6 = go.Figure()
    fig6.add_trace(go.Scatter(
        x=pre["year"], y=pre["temperature_anomaly"],
        mode="lines+markers", name="Lịch sử (1880–1969)",
        line=dict(color="#999999", width=1.5), marker=dict(size=4, color="#999999"),
        hovertemplate="Năm %{x}: %{y:.3f}°C<extra></extra>"
    ))
    fig6.add_trace(go.Scatter(
        x=train["year"], y=train["temperature_anomaly"],
        mode="markers", name="Huấn luyện (1970–2014)",
        marker=dict(size=6, color="#1f77b4"),
        hovertemplate="Năm %{x}: %{y:.3f}°C (Train)<extra></extra>"
    ))
    fig6.add_trace(go.Scatter(
        x=test["year"], y=test["temperature_anomaly"],
        mode="markers", name="Kiểm định thực tế (2015–2025)",
        marker=dict(size=8, symbol="square", color="#d62728"),
        hovertemplate="Năm %{x}: %{y:.3f}°C (Test)<extra></extra>"
    ))
    fig6.add_trace(go.Scatter(
        x=df_mod["year"], y=full_pred,
        mode="lines", name=f"Hồi quy OLS (+{slope_decade:.3f}°C/thập kỷ)",
        line=dict(color="#d95f02", width=2.5),
        hovertemplate="Hồi quy %{x}: %{y:.3f}°C<extra></extra>"
    ))
    fig6.add_trace(go.Scatter(
        x=future_years, y=future_pred,
        mode="lines", name="Dự báo đến 2050",
        line=dict(color="#e41a1c", width=2.5, dash="dash"),
        hovertemplate="Dự báo %{x}: %{y:.3f}°C<extra></extra>"
    ))
    fig6.add_trace(go.Scatter(
        x=np.concatenate([future_years, future_years[::-1]]),
        y=np.concatenate([upper_pi, lower_pi[::-1]]),
        fill="toself", fillcolor="rgba(228, 26, 28, 0.15)",
        line=dict(color="rgba(255,255,255,0)"),
        hoverinfo="skip", showlegend=True, name="Dải tin cậy 95%"
    ))
    fig6.add_hline(y=0, line_dash="dot", line_color="blue", annotation_text="Baseline 1951–1980 (0°C)")

    fig6.update_layout(
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
    fig6.write_html(OUT / "06_du_bao_hoi_quy_tuyen_tinh.html", include_plotlyjs="cdn")

    print("Plotly OK:", sorted(p.name for p in OUT.glob("*.html")))


if __name__ == "__main__":
    main()
