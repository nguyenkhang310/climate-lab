from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from climate_data import CONTINENTS, COUNTRY_NAMES

RED, BLUE, TEXT, MUTED = "#EF4444", "#1689E8", "#16324F", "#52677D"
FONT_FAMILY = (
    "Inter, -apple-system, BlinkMacSystemFont, Segoe UI, "
    "Roboto, Helvetica, Arial, sans-serif"
)
DIVERGING = [[0, "#388bd3"], [.5, "#f7f9fc"], [1, "#ef4444"]]
PALETTE = ["#1689E8", "#a98964", "#648aad", "#5c9e8a", "#9397b1", "#ca9c5b", "#76a56f"]
CONTINENT_COLORS = {
    continent: PALETTE[index % len(PALETTE)]
    for index, continent in enumerate(CONTINENTS)
}
LABELS = {
    "temperature_anomaly": "Biến đổi nhiệt độ (°C)",
    "co2": "Khí thải CO₂ (Mt)",
    "co2_per_capita": "CO₂ bình quân (tấn/người)",
}
LEGEND_TOP = {"orientation": "h", "x": 0, "y": 1.03, "yanchor": "bottom"}

def style_chart(fig, height=280):
    fig.update_layout(
        template="plotly_white", height=height, autosize=True,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="white",
        margin={"l": 48, "r": 22, "t": 16, "b": 42},
        font={"family": FONT_FAMILY, "size": 12, "color": MUTED},
        hoverlabel={
            "bgcolor": "white", "font_size": 14,
            "font_color": TEXT, "bordercolor": "#E3EAF2",
        },
        showlegend=False,
        legend={"orientation": "h", "y": 1.04, "yanchor": "bottom", "x": 0, "font_size": 12},
        modebar={"bgcolor": "rgba(0,0,0,0)", "color": "#9aabbc", "activecolor": BLUE},
    )
    fig.update_xaxes(
        gridcolor="#f0f3f7", zeroline=False, showline=True,
        linecolor="#e9eef4", tickfont_size=12, title_font_size=13,
        fixedrange=False, automargin=True,
    )
    fig.update_yaxes(
        gridcolor="#edf2f7", zerolinecolor="#dfe7f0",
        tickfont_size=12, title_font_size=13, automargin=True,
    )
    return fig

def empty_chart(message="Không có dữ liệu cho phạm vi đã chọn", height=280):
    fig = go.Figure()
    style_chart(fig, height)
    fig.add_annotation(
        text=message, x=.5, y=.5, xref="paper", yref="paper",
        showarrow=False, font={"size": 14, "color": MUTED},
    )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return fig

def _trend_line(series, field, *, color, marker, fill, name, hover, y_title, y_axis, height):
    data = series.dropna(subset=[field])
    if data.empty:
        return empty_chart(height=height)
    fig = go.Figure(go.Scatter(
        x=data.year, y=data[field], mode="lines+markers",
        line={"color": color, "width": 2.4}, marker=marker,
        fill="tozeroy", fillcolor=fill, name=name, hovertemplate=hover,
    ))
    style_chart(fig, height)
    if height <= 200:
        fig.update_layout(margin={"l": 39, "r": 10, "t": 6, "b": 29}, font_size=12)
    fig.update_xaxes(dtick=10, tickformat="d", title=None)
    fig.update_yaxes(title=y_title, **y_axis)
    fig.update_layout(hovermode="x unified")
    return fig

def create_temperature_chart(series, height=270):
    return _trend_line(
        series, "temperature_anomaly", color=RED,
        marker={"size": 5, "color": "white", "line": {"width": 2, "color": RED}},
        fill="rgba(239,68,68,.045)", name="Nhiệt độ quan trắc",
        hover=("%{x}<br>Độ lệch nhiệt độ: <b>%{y:+.2f} °C</b><extra>NASA / FAOSTAT</extra>"),
        y_title="Độ lệch (°C)", y_axis={"tickformat": ".1f", "nticks": 5}, height=height,
    )

def create_co2_chart(series, height=270):
    return _trend_line(
        series, "co2", color=BLUE, marker={"size": 4, "color": BLUE},
        fill="rgba(22,137,232,.10)", name="CO₂ quan trắc",
        hover=("%{x}<br>Khí thải CO₂: <b>%{y:,.1f} Mt</b><extra>OWID / Global Carbon Project</extra>"),
        y_title="CO₂ (Mt)", y_axis={"rangemode": "tozero", "tickformat": ",.0f", "nticks": 5},
        height=height,
    )

def create_ranking_chart(snapshot, selected="all", metric="co2", limit=7, height=290):
    valid = snapshot.dropna(subset=[metric])
    if valid.empty:
        return empty_chart(height=height)
    data = valid.nlargest(limit, metric).sort_values(metric)
    if selected != "all" and selected in set(valid.iso_alpha):
        selected_codes = set(data.iso_alpha) | {selected}
        data = valid[valid.iso_alpha.isin(selected_codes)].sort_values(metric)
    colors = [BLUE if iso == selected else "#70AFE0" for iso in data.iso_alpha]
    if selected == "all" and colors:
        colors[-1] = BLUE
    fig = go.Figure(go.Bar(
        y=data.country, x=data[metric], orientation="h", marker_color=colors,
        text=data[metric], texttemplate="%{text:,.1f}", textposition="outside",
        cliponaxis=False, textfont={"size": 12, "color": TEXT}, width=.55,
        hovertemplate=(
            "%{y}<br>" + LABELS[metric] + ": <b>%{x:,.2f}</b><extra>OWID / GCP</extra>"
        ),
    ))
    style_chart(fig, max(height, len(data) * 28 + 70))
    fig.update_layout(
        margin={"l": 14, "r": 60, "t": 8, "b": 48},
        uniformtext={"minsize": 12, "mode": "show"},
    )
    fig.update_xaxes(
        title=LABELS[metric], range=[0, max(float(data[metric].max()) * 1.23, 1)],
        tickformat=",.0f" if metric == "co2" else ".1f", nticks=5,
    )
    fig.update_yaxes(showgrid=False, showline=False, tickfont={"color": TEXT})
    return fig

def _continent_trace(group, continent, *, x, y, selected, size_sel, size_other,
                     custom_cols, hover, outline=False):
    sizes = [size_sel if iso == selected else size_other for iso in group.iso_alpha]
    marker = {
        "color": CONTINENT_COLORS.get(continent, "#9bacbd"),
        "size": sizes, "opacity": .85 if outline else .8,
    }
    if outline:
        marker["line"] = {
            "color": TEXT,
            "width": [2 if iso == selected else 0 for iso in group.iso_alpha],
        }
    return go.Scatter(
        x=group[x], y=group[y], mode="markers", name=continent,
        customdata=group[custom_cols], marker=marker, hovertemplate=hover,
    )

def create_scatter_chart(snapshot, selected="all", height=370, compact=False):
    data = snapshot.dropna(subset=["co2_per_capita", "temperature_anomaly", "continent"])
    if data.empty:
        return empty_chart(height=height)
    fig = go.Figure()
    hover = (
        "<b>%{customdata[0]}</b> · %{customdata[2]}"
        "<br>CO₂: %{x:.2f} tấn/người<br>Nhiệt độ: %{y:+.2f} °C<extra>OWID · FAOSTAT</extra>"
    )
    for continent, group in data.groupby("continent", sort=False):
        fig.add_trace(_continent_trace(
            group, continent, x="co2_per_capita", y="temperature_anomaly",
            selected=selected, size_sel=16, size_other=10,
            custom_cols=["country", "co2", "year"], hover=hover, outline=True,
        ))
    style_chart(fig, height)
    if compact:
        fig.update_layout(showlegend=False, margin={"l": 37, "r": 10, "b": 29, "t": 6})
        fig.update_xaxes(title=None, rangemode="tozero", nticks=5)
        fig.update_yaxes(title=None, nticks=4)
    else:
        fig.update_layout(
            showlegend=True, margin={"l": 58, "r": 20, "b": 48, "t": 38},
            legend={**LEGEND_TOP, "font_size": 12, "itemsizing": "constant"},
        )
        fig.update_xaxes(title="CO₂ bình quân (tấn/người)", rangemode="tozero")
        fig.update_yaxes(title="Độ lệch nhiệt độ (°C)")
    return fig

def create_globe(
    snapshot, selected="VNM", metric="temperature", reset=0, rotation=None,
    height=570, scale=1, view_mode="globe",
):
    field = "co2" if metric == "co2" else "temperature_anomaly"
    is_co2 = metric == "co2"
    snapshot = snapshot.drop_duplicates("iso_alpha").copy()
    valid = snapshot.dropna(subset=[field])
    missing = snapshot[snapshot[field].isna()]
    colorscale = (
        [[0, "rgba(142,202,238,.38)"], [1, "rgba(17,112,190,.72)"]]
        if is_co2 else
        [[0, "rgba(42,137,225,.55)"], [.5, "rgba(238,244,239,.35)"], [1, "rgba(239,68,68,.60)"]]
    )
    if is_co2 and not valid.empty:
        zmin, zmax = 0, max(float(valid[field].quantile(.98)), 1)
    else:
        zmin, zmax = (-2, 2)
    custom_columns = [
        "country", "year", "temperature_anomaly", "co2",
        "co2_per_capita", "population",
    ]
    def border_style(rows):
        colors = [
            "#73d7ff" if iso == selected else "rgba(183,215,219,.72)"
            for iso in rows.iso_alpha
        ]
        widths = [2.2 if iso == selected else .45 for iso in rows.iso_alpha]
        return colors, widths

    fig = go.Figure()
    if not missing.empty:
        colors, widths = border_style(missing)
        fig.add_choropleth(
            locations=missing.iso_alpha,
            z=[0] * len(missing),
            locationmode="ISO-3",
            customdata=missing[custom_columns],
            colorscale=[[0, "#49675d"], [1, "#49675d"]],
            zmin=0,
            zmax=1,
            marker_line_color=colors,
            marker_line_width=widths,
            showscale=False,
            name="Chưa có dữ liệu",
            hovertemplate="<b>%{customdata[0]}</b><br>Chưa có dữ liệu chỉ số này<extra></extra>",
        )
    colors, widths = border_style(valid)
    fig.add_choropleth(
        locations=valid.iso_alpha, z=valid[field], locationmode="ISO-3",
        customdata=valid[custom_columns], colorscale=colorscale,
        zmin=zmin, zmax=zmax, marker_line_color=colors, marker_line_width=widths,
        colorbar={
            "title": {
                "text": "CO₂ (Mt)" if is_co2 else "Nhiệt độ (°C)",
                "side": "top", "font_size": 12, "font_color": "#d7e9f2",
            },
            "orientation": "v", "x": .035, "xanchor": "left", "y": .16,
            "yanchor": "middle", "len": .26, "thickness": 10,
            "bgcolor": "rgba(4,24,40,.78)", "borderwidth": 0,
            "tickfont": {"size": 11, "color": "#d7e9f2"}, "outlinewidth": 0,
        },
        name="CO₂" if is_co2 else "Nhiệt độ",
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>%{customdata[1]}<br>"
            + ("CO₂: %{z:,.2f} Mt" if is_co2 else "Nhiệt độ: %{z:+.2f} °C")
            + "<extra></extra>"
        ),
    )

    is_flat = view_mode == "flat"
    initial_rotation = {"lon": 0, "lat": 0} if is_flat else (rotation or {"lon": 105, "lat": 15})
    safe_scale = max(.86, min(float(scale or 1), 1.08))
    fig.update_geos(
        projection_type="natural earth" if is_flat else "orthographic",
        projection_rotation=initial_rotation, projection_scale=1 if is_flat else safe_scale,
        resolution=110, showcoastlines=True, coastlinecolor="#88b6ae",
        coastlinewidth=.5, showland=True, landcolor="#365547",
        showocean=True, oceancolor="#061d32", showlakes=False,
        showrivers=False, showcountries=False, bgcolor="rgba(0,0,0,0)",
        showframe=True, framecolor="#4B718C" if is_flat else "#279be6",
        framewidth=1 if is_flat else 1.8,
        lonaxis={"showgrid": False}, lataxis={"showgrid": False},
    )
    fig.update_layout(
        height=height, margin={"l": 4, "r": 4, "t": 4, "b": 4},
        paper_bgcolor="rgba(0,0,0,0)", font={"family": FONT_FAMILY, "color": "#a6bfd3"},
        showlegend=False, geo_uirevision=f"{view_mode}-{reset}", clickmode="event",
        dragmode="pan", hovermode="closest", transition={"duration": 0},
        meta={"selected": selected},
        modebar={"color": "#96b6ce", "activecolor": "white", "bgcolor": "rgba(0,0,0,0)"},
    )
    return fig

def create_decade_chart(series):
    data = series.dropna(subset=["temperature_anomaly"]).copy()
    if data.empty:
        return empty_chart()
    data["decade"] = data.year // 10 * 10
    data = data.groupby("decade", as_index=False).temperature_anomaly.mean()
    fig = go.Figure(go.Bar(
        x=data.decade.astype(str), y=data.temperature_anomaly,
        marker={"color": data.temperature_anomaly, "colorscale": DIVERGING, "cmin": -2, "cmax": 2},
        width=.58,
        hovertemplate="Thập kỷ %{x}<br>Trung bình: %{y:+.2f} °C<extra>NASA / FAOSTAT</extra>",
    ))
    style_chart(fig)
    fig.update_yaxes(title="Độ lệch nhiệt độ (°C)")
    return fig

def create_box_chart(frame):
    data = frame.dropna(subset=["temperature_anomaly"]).copy()
    if data.empty:
        return empty_chart()
    data["decade"] = data.year // 10 * 10
    fig = go.Figure()
    for decade, group in data.groupby("decade"):
        fig.add_trace(go.Box(
            y=group.temperature_anomaly, name=str(decade),
            marker_color="#e89797", fillcolor="#fff3f3", line_width=1.3,
            boxpoints=False,
            hovertemplate=f"Thập kỷ {decade}<br>%{{y:+.2f}} °C<extra>FAOSTAT</extra>",
        ))
    style_chart(fig)
    fig.update_layout(showlegend=False)
    fig.update_yaxes(title="Độ lệch nhiệt độ (°C)")
    return fig

def create_heatmap(frame):
    data = frame.dropna(subset=["temperature_anomaly", "continent"]).copy()
    if data.empty:
        return empty_chart()
    data["decade"] = data.year // 10 * 10
    matrix = data.pivot_table(
        index="continent", columns="decade", values="temperature_anomaly", aggfunc="mean"
    )
    labels = [
        [f"{value:+.2f}°" if pd.notna(value) else "—" for value in row]
        for row in matrix.values
    ]
    fig = go.Figure(go.Heatmap(
        z=matrix.values, x=matrix.columns.astype(str), y=matrix.index,
        colorscale=DIVERGING, zmin=-2, zmax=2, xgap=4, ygap=4,
        text=labels, texttemplate="%{text}", textfont_size=12, showscale=False,
        hovertemplate="%{y} · thập kỷ %{x}<br>Trung bình: %{text}<extra>FAOSTAT</extra>",
    ))
    style_chart(fig)
    fig.update_layout(margin={"l": 14, "r": 16, "t": 8, "b": 36})
    fig.update_yaxes(showgrid=False, autorange="reversed")
    return fig

def create_composition_chart(snapshot):
    data = snapshot.dropna(subset=["continent", "co2"])
    if data.empty:
        return empty_chart(height=310)
    totals = data.groupby("continent").co2.sum(min_count=1).sort_values(ascending=False)
    fig = go.Figure(go.Treemap(
        labels=["Tổng phạm vi"] + list(totals.index),
        parents=[""] + ["Tổng phạm vi"] * len(totals),
        values=[totals.sum()] + list(totals), branchvalues="total",
        textinfo="label+percent parent", textfont_size=12,
        marker={"colors": [0] + list(totals), "colorscale": "Blues", "line": {"width": 3, "color": "white"}},
        pathbar_visible=False,
        hovertemplate="%{label}<br>%{value:,.1f} Mt CO₂<extra>OWID / GCP</extra>",
    ))
    style_chart(fig, 310)
    fig.update_layout(margin={"l": 12, "r": 12, "t": 0, "b": 12})
    return fig

def create_sector_chart(sector_data, height=310):
    data = sector_data.dropna(subset=["co2"])
    if data.empty:
        return empty_chart(height=height)
    totals = data.groupby(["year", "sector"], as_index=False).co2.sum(min_count=1)
    fig = go.Figure()
    for index, (sector, group) in enumerate(totals.groupby("sector")):
        fig.add_trace(go.Scatter(
            x=group.year, y=group.co2, name=sector, mode="lines",
            stackgroup="one", line={"width": .8, "color": PALETTE[index % len(PALETTE)]},
            hovertemplate=f"%{{x}}<br>{sector}: %{{y:,.1f}} Mt<extra>EDGAR</extra>",
        ))
    style_chart(fig, height)
    fig.update_layout(showlegend=True, legend={**LEGEND_TOP, "y": 1.03})
    fig.update_xaxes(title="Năm", dtick=10)
    fig.update_yaxes(title="CO₂ theo ngành (Mt)", rangemode="tozero")
    return fig

def create_renewable_scatter_chart(snapshot, selected="all", height=310):
    data = snapshot.dropna(subset=["renewable_percent", "co2_per_capita", "continent"])
    if data.empty:
        return empty_chart("Năm này chưa đủ dữ liệu năng lượng tái tạo", height)
    fig = go.Figure()
    hover = (
        "<b>%{customdata[0]}</b> · %{customdata[1]}"
        "<br>Năng lượng tái tạo: %{x:.1f}%<br>CO₂: %{y:.2f} tấn/người<extra>UN / OWID</extra>"
    )
    for continent, group in data.groupby("continent", sort=False):
        fig.add_trace(_continent_trace(
            group, continent, x="renewable_percent", y="co2_per_capita",
            selected=selected, size_sel=15, size_other=9,
            custom_cols=["country", "year"], hover=hover,
        ))
    style_chart(fig, height)
    fig.update_layout(showlegend=True, legend={**LEGEND_TOP, "y": 1.03})
    fig.update_xaxes(title="Tỷ trọng năng lượng tái tạo (%)", rangemode="tozero")
    fig.update_yaxes(title="CO₂ bình quân (tấn/người)", rangemode="tozero")
    return fig

def create_comparison_chart(frame, country_a, country_b, metric):
    fig = go.Figure()
    color = RED if metric == "temperature_anomaly" else BLUE
    for iso, tone in [(country_a, color), (country_b, "#9bacbd")]:
        data = frame[frame.iso_alpha == iso].dropna(subset=[metric])
        fig.add_trace(go.Scatter(
            x=data.year, y=data[metric], name=COUNTRY_NAMES.get(iso, iso),
            mode="lines+markers", line={"color": tone, "width": 2.5}, marker_size=5,
            hovertemplate=(
                "%{x}<br>%{y:,.2f}<extra>" + COUNTRY_NAMES.get(iso, iso) + "</extra>"
            ),
        ))
    style_chart(fig, 290)
    fig.update_xaxes(dtick=10)
    fig.update_yaxes(title=LABELS[metric])
    fig.update_layout(showlegend=True, legend={"y": 1.12}, hovermode="x unified", margin_t=32)
    return fig

def create_forecast_chart(history, scenarios, historical_predictions=None):
    data = history.dropna(subset=["temperature_anomaly"])
    fig = go.Figure(go.Scatter(
        x=data.year, y=data.temperature_anomaly, name="Nhiệt độ quan trắc",
        mode="lines", line={"color": TEXT, "width": 2.4},
        hovertemplate="%{x}<br>%{y:+.2f} °C<extra>NASA GISTEMP</extra>",
    ))
    if historical_predictions is not None:
        predicted = historical_predictions[historical_predictions.year >= 2015]
        if "prediction_cumulative_co2_linear" in predicted:
            fig.add_trace(go.Scatter(
                x=predicted.year, y=predicted.prediction_cumulative_co2_linear,
                name="Dự đoán tập kiểm tra", mode="lines",
                line={"color": "#9bacbd", "width": 2, "dash": "dot"},
                hovertemplate="%{x}<br>%{y:+.2f} °C<extra>Mô hình CO₂ tích lũy</extra>",
            ))
    scenario_colors = {
        "Xu hướng hiện tại": RED,
        "Giữ ổn định": "#F59E0B",
        "Giảm 3% mỗi năm": "#22A06B",
    }
    for scenario, group in scenarios.groupby("scenario", sort=False):
        fig.add_trace(go.Scatter(
            x=group.year, y=group.temperature_prediction, name=scenario,
            mode="lines", line={"color": scenario_colors.get(scenario, BLUE), "width": 2.4, "dash": "dash"},
            customdata=group[["co2"]],
            hovertemplate=(
                "%{x}<br>Nhiệt độ: %{y:+.2f} °C"
                "<br>CO₂ giả định: %{customdata[0]:,.0f} Mt<extra>" + scenario + "</extra>"
            ),
        ))
    style_chart(fig, 410)
    fig.add_vrect(x0=2024.5, x1=2050, fillcolor="#f2f6fb", opacity=.65, line_width=0, layer="below")
    fig.add_vline(x=2024.5, line_width=1, line_dash="dot", line_color="#8496AA")
    fig.update_layout(
        showlegend=True, hovermode="x unified",
        legend={**LEGEND_TOP, "y": 1.03},
        margin={"l": 48, "r": 22, "t": 54, "b": 42},
    )
    fig.update_xaxes(title="Năm", dtick=5)
    fig.update_yaxes(title="Độ lệch nhiệt độ (°C)")
    return fig
