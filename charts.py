"""Các biểu đồ dùng trong dashboard."""
import plotly.graph_objects as go

from mock_data import CONTINENTS, COORDINATES, COUNTRY_NAMES

RED, BLUE, TEXT, MUTED = "#EF4444", "#1689E8", "#16324F", "#52677D"
FONT_FAMILY = (
    "Inter, -apple-system, BlinkMacSystemFont, Segoe UI, "
    "Roboto, Helvetica, Arial, sans-serif"
)
DIVERGING = [[0, "#388bd3"], [.5, "#f7f9fc"], [1, "#ef4444"]]
CONTINENT_COLORS = dict(zip(
    CONTINENTS,
    ["#1689E8", "#a98964", "#648aad", "#5c9e8a", "#9397b1", "#ca9c5b"],
))
LABELS = {
    "temperature_anomaly": "Biến đổi nhiệt độ (°C)",
    "co2": "Khí thải CO₂ (Mt)",
    "co2_per_capita": "CO₂ bình quân (tấn/người)",
}


def style_chart(fig, height=280):
    fig.update_layout(
        template="plotly_white",
        height=height,
        autosize=True,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="white",
        margin={"l": 48, "r": 22, "t": 16, "b": 42},
        font={"family": FONT_FAMILY, "size": 12, "color": MUTED},
        hoverlabel={
            "bgcolor": "white",
            "font_size": 14,
            "font_color": TEXT,
            "bordercolor": "#E3EAF2",
        },
        showlegend=False,
        legend={
            "orientation": "h",
            "y": 1.04,
            "yanchor": "bottom",
            "x": 0,
            "font_size": 12,
        },
        modebar={
            "bgcolor": "rgba(0,0,0,0)",
            "color": "#9aabbc",
            "activecolor": BLUE,
        },
    )
    fig.update_xaxes(
        gridcolor="#f0f3f7",
        zeroline=False,
        showline=True,
        linecolor="#e9eef4",
        tickfont_size=12,
        title_font_size=13,
        fixedrange=False,
        automargin=True,
    )
    fig.update_yaxes(
        gridcolor="#edf2f7",
        zerolinecolor="#dfe7f0",
        tickfont_size=12,
        title_font_size=13,
        automargin=True,
    )
    return fig


def create_temperature_chart(series, height=270):
    line = go.Scatter(
        x=series.year,
        y=series.temperature_anomaly,
        mode="lines+markers",
        line={"color": RED, "width": 2.4},
        marker={
            "size": 5,
            "color": "white",
            "line": {"width": 2, "color": RED},
        },
        fill="tozeroy",
        fillcolor="rgba(239,68,68,.045)",
        name="Nhiệt độ",
        hovertemplate=(
            "%{x}<br>Biến đổi nhiệt độ: <b>%{y:+.2f} °C</b>"
            "<extra>Mô phỏng</extra>"
        ),
    )
    fig = go.Figure(line)
    style_chart(fig, height)
    if height <= 200:
        fig.update_layout(margin={"l": 39, "r": 10, "t": 6, "b": 29}, font_size=12)
    fig.update_xaxes(dtick=10, tickformat="d", title=None)
    fig.update_yaxes(tickformat=".1f", nticks=5, title="Độ lệch (°C)")
    fig.update_layout(hovermode="x unified")
    return fig


def create_co2_chart(series, height=270):
    unit = "Mt"
    line = go.Scatter(
        x=series.year,
        y=series.co2,
        mode="lines+markers",
        line={"color": BLUE, "width": 2.4},
        marker={"size": 4, "color": BLUE},
        fill="tozeroy",
        fillcolor="rgba(22,137,232,.10)",
        name="CO₂",
        hovertemplate=(
            "%{x}<br>Khí thải CO₂: <b>%{y:,.1f} "
            + unit
            + "</b><extra>Mô phỏng</extra>"
        ),
    )
    fig = go.Figure(line)
    style_chart(fig, height)
    if height <= 200:
        fig.update_layout(margin={"l": 39, "r": 10, "t": 6, "b": 29}, font_size=12)
    fig.update_xaxes(dtick=10, tickformat="d", title=None)
    fig.update_yaxes(
        rangemode="tozero",
        tickformat=",.0f",
        nticks=5,
        title=f"CO₂ ({unit})",
    )
    fig.update_layout(hovermode="x unified")
    return fig


def create_ranking_chart(snapshot, selected="all", metric="co2", limit=7, height=290):
    data = snapshot.nlargest(limit, metric).sort_values(metric)
    if selected != "all":
        selected_countries = set(data.iso_alpha) | {selected}
        data = snapshot[snapshot.iso_alpha.isin(selected_countries)].sort_values(metric)
    colors = [BLUE if iso == selected else "#70AFE0" for iso in data.iso_alpha]
    if selected == "all" and colors:
        colors[-1] = BLUE
    bars = go.Bar(
        y=data.country,
        x=data[metric],
        orientation="h",
        marker_color=colors,
        text=data[metric],
        texttemplate="%{text:,.1f}",
        textposition="outside",
        cliponaxis=False,
        textfont={"size": 12, "color": TEXT},
        width=.55,
        hovertemplate=(
            "%{y}<br>"
            + LABELS[metric]
            + ": <b>%{x:,.2f}</b><extra>Mô phỏng</extra>"
        ),
    )
    fig = go.Figure(bars)
    # Dành đủ chiều cao cho tên và giá trị của từng quốc gia.
    style_chart(fig, max(height, len(data) * 28 + 70))
    fig.update_layout(
        margin={"l": 14, "r": 60, "t": 8, "b": 48},
        uniformtext={"minsize": 12, "mode": "show"},
    )
    upper_limit = max(data[metric].max() * 1.23, 1)
    fig.update_xaxes(
        title=LABELS[metric],
        range=[0, upper_limit],
        tickformat=",.0f" if metric == "co2" else ".1f",
        nticks=5,
    )
    fig.update_yaxes(showgrid=False, showline=False, tickfont=dict(color=TEXT))
    return fig


def create_scatter_chart(snapshot, selected="all", height=370, compact=False):
    fig = go.Figure()
    for continent, group in snapshot.groupby("continent", sort=False):
        point_sizes = [16 if iso == selected else 10 for iso in group.iso_alpha]
        border_widths = [2 if iso == selected else 0 for iso in group.iso_alpha]
        marker = {
            "color": CONTINENT_COLORS[continent],
            "size": point_sizes,
            "opacity": .85,
            "line": {"color": TEXT, "width": border_widths},
        }
        fig.add_trace(go.Scatter(
            x=group.co2_per_capita,
            y=group.temperature_anomaly,
            mode="markers",
            name=continent,
            customdata=group[["country", "co2", "year"]],
            marker=marker,
            hovertemplate=(
                "<b>%{customdata[0]}</b> · %{customdata[2]}"
                "<br>CO₂: %{x:.2f} tấn/người"
                "<br>Nhiệt độ: %{y:+.2f} °C"
                "<extra>Mô phỏng</extra>"
            ),
        ))
    style_chart(fig, height)
    if compact:
        fig.update_layout(
            showlegend=False,
            margin={"l": 37, "r": 10, "b": 29, "t": 6},
            font_size=12,
        )
        fig.update_xaxes(title=None, rangemode="tozero", nticks=5)
        fig.update_yaxes(title=None, nticks=4)
    else:
        fig.update_layout(
            showlegend=True,
            margin={"l": 58, "r": 20, "b": 48, "t": 38},
            legend={
                "orientation": "h",
                "x": 0,
                "y": 1.03,
                "yanchor": "bottom",
                "font_size": 12,
                "itemsizing": "constant",
            },
        )
        fig.update_xaxes(title="CO₂ bình quân (tấn/người)", rangemode="tozero")
        fig.update_yaxes(title="Nhiệt độ (°C)")
    return fig


def create_globe(
    snapshot,
    selected="VNM",
    metric="temperature",
    reset=0,
    rotation=None,
    height=570,
    scale=1,
    view_mode="globe",
):
    """Tạo bản đồ khí hậu ở dạng địa cầu hoặc bản đồ thế giới phẳng."""
    field = "co2" if metric == "co2" else "temperature_anomaly"
    is_co2 = metric == "co2"
    if is_co2:
        colorscale = [
            [0, "rgba(142,202,238,.38)"],
            [1, "rgba(17,112,190,.62)"],
        ]
    else:
        colorscale = [
            [0, "rgba(42,137,225,.55)"],
            [.5, "rgba(238,244,239,.35)"],
            [1, "rgba(239,68,68,.60)"],
        ]
    zmin, zmax = (0, 11000) if is_co2 else (-2, 2)
    custom_columns = [
        "country",
        "year",
        "temperature_anomaly",
        "co2",
        "co2_per_capita",
        "population",
    ]
    custom = snapshot[custom_columns]
    borders = [
        "#73d7ff" if iso == selected else "rgba(183,215,219,.72)"
        for iso in snapshot.iso_alpha
    ]
    border_widths = [2.2 if iso == selected else .45 for iso in snapshot.iso_alpha]
    map_layer = go.Choropleth(
        locations=snapshot.iso_alpha,
        z=snapshot[field],
        locationmode="ISO-3",
        customdata=custom,
        colorscale=colorscale,
        zmin=zmin,
        zmax=zmax,
        marker_line_color=borders,
        marker_line_width=border_widths,
        colorbar={
            "title": {
                "text": "CO₂ (Mt)" if is_co2 else "Nhiệt độ (°C)",
                "side": "top",
                "font_size": 12, "font_color": "#d7e9f2",
            },
            "orientation": "v",
            "x": .035,
            "xanchor": "left",
            "y": .16,
            "yanchor": "middle",
            "len": .26,
            "thickness": 10,
            "bgcolor": "rgba(4,24,40,.78)",
            "borderwidth": 0,
            "tickfont": {"size": 11, "color": "#d7e9f2"},
            "outlinewidth": 0,
        },
        # Vẫn nhận sự kiện bấm vào quốc gia, không mở hộp số liệu trên bản đồ.
        hoverinfo="none",
    )
    fig = go.Figure(map_layer)
    chosen = snapshot[snapshot.iso_alpha == selected]
    if not chosen.empty:
        lon, lat = COORDINATES[selected]
        selected_marker = go.Scattergeo(
            lon=[lon],
            lat=[lat],
            mode="markers",
            marker={
                "size": 10,
                "color": "#00a6ff",
                "line": {"width": 2.5, "color": "white"},
            },
            customdata=[selected],
            hoverinfo="none",
            showlegend=False,
        )
        fig.add_trace(selected_marker)

    is_flat = view_mode == "flat"
    initial_rotation = {"lon": 0, "lat": 0} if is_flat else (rotation or {"lon": 105, "lat": 15})
    safe_scale = max(.86, min(float(scale or 1), 1.08))
    fig.update_geos(
        projection_type="natural earth" if is_flat else "orthographic",
        projection_rotation=initial_rotation,
        projection_scale=1 if is_flat else safe_scale,
        resolution=110,
        showcoastlines=True,
        coastlinecolor="#88b6ae",
        coastlinewidth=.5,
        showland=True,
        landcolor="#365547",
        showocean=True,
        oceancolor="#061d32",
        showlakes=False,
        showrivers=False,
        showcountries=False,
        bgcolor="rgba(0,0,0,0)",
        showframe=True,
        framecolor="#4B718C" if is_flat else "#279be6",
        framewidth=1 if is_flat else 1.8,
        lonaxis={"showgrid": False},
        lataxis={"showgrid": False},
    )
    fig.update_layout(
        height=height,
        margin={"l": 4, "r": 4, "t": 4, "b": 4},
        paper_bgcolor="rgba(0,0,0,0)",
        font={"family": FONT_FAMILY, "color": "#a6bfd3"},
        showlegend=False,
        geo_uirevision=f"{view_mode}-{reset}",
        clickmode="event",
        dragmode="pan",
        hovermode="closest",
        transition={"duration": 0},
        modebar={
            "color": "#96b6ce",
            "activecolor": "white",
            "bgcolor": "rgba(0,0,0,0)",
        },
    )
    return fig


def create_decade_chart(series):
    bars = go.Bar(
        x=series.year.astype(str),
        y=series.temperature_anomaly,
        marker={
            "color": series.temperature_anomaly,
            "colorscale": DIVERGING,
            "cmin": -2,
            "cmax": 2,
        },
        width=.48,
        hovertemplate=(
            "Thập kỷ %{x}<br>%{y:+.2f} °C"
            "<extra>Mốc đại diện mô phỏng</extra>"
        ),
    )
    fig = go.Figure(bars)
    style_chart(fig)
    fig.update_yaxes(title="Biến đổi nhiệt độ (°C)")
    return fig


def create_box_chart(frame):
    fig = go.Figure()
    for year, group in frame.groupby("year"):
        box = go.Box(
            y=group.temperature_anomaly,
            name=str(year),
            marker_color="#e89797",
            fillcolor="#fff3f3",
            line_width=1.3,
            boxpoints="all",
            jitter=.2,
            pointpos=0,
            customdata=group.country,
            hovertemplate=(
                "%{customdata}<br>%{y:+.2f} °C"
                "<extra>Phân bố mẫu</extra>"
            ),
        )
        fig.add_trace(box)
    style_chart(fig)
    fig.update_layout(showlegend=False)
    fig.update_yaxes(title="Biến đổi nhiệt độ (°C)")
    return fig


def create_heatmap(frame):
    matrix = frame.pivot_table(
        index="continent",
        columns="year",
        values="temperature_anomaly",
        aggfunc="mean",
    )
    labels = [[f"{value:+.2f}°" for value in row] for row in matrix.values]
    heatmap = go.Heatmap(
        z=matrix.values,
        x=matrix.columns.astype(str),
        y=matrix.index,
        colorscale=DIVERGING,
        zmin=-2,
        zmax=2,
        xgap=4,
        ygap=4,
        text=labels,
        texttemplate="%{text}",
        textfont_size=12,
        showscale=False,
        hovertemplate=(
            "%{y} · %{x}<br>Trung bình trong mẫu: %{text}C"
            "<extra>Mô phỏng</extra>"
        ),
    )
    fig = go.Figure(heatmap)
    style_chart(fig)
    fig.update_layout(margin=dict(l=14, r=16, t=8, b=36))
    fig.update_yaxes(showgrid=False, autorange="reversed")
    return fig


def create_composition_chart(snapshot):
    totals = snapshot.groupby("continent").co2.sum().sort_values(ascending=False)
    treemap = go.Treemap(
        labels=["Mẫu đang xem"] + list(totals.index),
        parents=[""] + ["Mẫu đang xem"] * len(totals),
        values=[totals.sum()] + list(totals),
        branchvalues="total",
        textinfo="label+percent parent",
        textfont_size=12,
        marker={
            "colors": [0] + list(totals),
            "colorscale": "Blues",
            "line": {"width": 3, "color": "white"},
        },
        pathbar_visible=False,
        hovertemplate=(
            "%{label}<br>%{value:,.1f} Mt CO₂"
            "<extra>Mô phỏng</extra>"
        ),
    )
    fig = go.Figure(treemap)
    style_chart(fig, 310)
    fig.update_layout(margin=dict(l=12, r=12, t=0, b=12))
    return fig


def create_comparison_chart(frame, country_a, country_b, metric):
    fig = go.Figure()
    color = RED if metric == "temperature_anomaly" else BLUE
    for iso, tone in [(country_a, color), (country_b, "#9bacbd")]:
        data = frame[frame.iso_alpha == iso]
        line = go.Scatter(
            x=data.year,
            y=data[metric],
            name=COUNTRY_NAMES[iso],
            mode="lines+markers",
            line={"color": tone, "width": 2.5},
            marker_size=5,
            hovertemplate=(
                "%{x}<br>%{y:,.2f}<extra>"
                + COUNTRY_NAMES[iso]
                + " · Mô phỏng</extra>"
            ),
        )
        fig.add_trace(line)
    style_chart(fig, 290)
    fig.update_xaxes(dtick=10)
    fig.update_yaxes(title=LABELS[metric])
    fig.update_layout(showlegend=True, legend=dict(y=1.12), hovermode="x unified", margin_t=32)
    return fig


def create_forecast_chart(series):
    """Phép nối tuyến tính minh họa bằng tay; không huấn luyện mô hình."""
    historical = create_temperature_chart(series, 380)
    last = series.iloc[-1]
    years = [int(last.year), int(last.year) + 10, int(last.year) + 20, int(last.year) + 30]
    values = [float(last.temperature_anomaly) + .18 * index for index in range(4)]
    forecast = go.Scatter(
        x=years,
        y=values,
        name="Dự báo giả định",
        mode="lines+markers",
        line={"color": RED, "width": 2.4, "dash": "dash"},
        marker_size=5,
        hovertemplate=(
            "%{x}<br>%{y:,.2f}"
            "<extra>Dữ liệu dự báo minh họa</extra>"
        ),
    )
    historical.add_trace(forecast)
    historical.add_vrect(
        x0=int(last.year),
        x1=years[-1],
        fillcolor="#f2f6fb",
        opacity=.6,
        line_width=0,
        layer="below",
    )
    historical.update_layout(showlegend=True, legend=dict(y=1.12), margin_t=32)
    return historical
