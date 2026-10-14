import plotly.graph_objects as go

RED, BLUE, TEXT, MUTED = "#EF4444", "#1689E8", "#16324F", "#52677D"
MAP_BORDER = "#8EA4B2"
FONT_FAMILY = (
    "Inter, -apple-system, BlinkMacSystemFont, Segoe UI, "
    "Roboto, Helvetica, Arial, sans-serif"
)

def tao_kieu_bieu_do(fig, height=280):
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

def tao_bieu_do_trong(message="Chưa có dữ liệu", height=280):
    fig = go.Figure()
    tao_kieu_bieu_do(fig, height)
    fig.add_annotation(
        text=message, x=.5, y=.5, xref="paper", yref="paper",
        showarrow=False, font={"size": 14, "color": MUTED},
    )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return fig

def _tao_duong_xu_huong(series, field, *, color, marker, fill, name, hover, y_title, y_axis, height):
    data = series.sort_values("year")
    if not data[field].notna().any():
        return tao_bieu_do_trong(height=height)
    fig = go.Figure(go.Scatter(
        x=data.year, y=data[field], mode="lines+markers",
        text=data[field].map(("{:+.2f}" if field == "temperature_anomaly" else "{:,.1f}").format),
        line={"color": color, "width": 2.4}, marker=marker,
        fill="tozeroy", fillcolor=fill, name=name, hovertemplate=hover,
    ))
    tao_kieu_bieu_do(fig, height)
    fig.update_xaxes(dtick=10, tickformat="d", title=None)
    fig.update_yaxes(title=y_title, **y_axis)
    fig.update_layout(hovermode="x unified")
    return fig

def tao_bieu_do_nhiet_do(series, height=270, scope="Phạm vi đang xem"):
    return _tao_duong_xu_huong(
        series, "temperature_anomaly", color=RED,
        marker={"size": 5, "color": "white", "line": {"width": 2, "color": RED}},
        fill="rgba(239,68,68,.045)", name="Nhiệt độ ghi nhận",
        hover=(scope + " · Năm %{x}<br>Chênh nhiệt độ: <b>%{text} °C</b>"
               "<br>So với trung bình 1951–1980<extra>NASA / FAOSTAT</extra>"),
        y_title="Chênh lệch (°C)", y_axis={"tickformat": ".1f", "nticks": 5}, height=height,
    )

def tao_bieu_do_co2(series, height=270, scope="Phạm vi đang xem"):
    return _tao_duong_xu_huong(
        series, "co2", color=BLUE, marker={"size": 4, "color": BLUE},
        fill="rgba(22,137,232,.10)", name="Lượng CO₂ ghi nhận",
        hover=(scope + " · Năm %{x}<br>CO₂ trong năm: <b>%{text} triệu tấn</b>"
               "<extra>OWID / Global Carbon Project</extra>"),
        y_title="CO₂ (triệu tấn)", y_axis={"rangemode": "tozero", "tickformat": ",.0f", "nticks": 5},
        height=height,
    )

def tao_bieu_do_xep_hang(snapshot, selected="all", limit=7, height=290):
    valid = snapshot.dropna(subset=["co2"])
    if valid.empty:
        return tao_bieu_do_trong(height=height)
    data = valid.nlargest(limit, "co2").sort_values("co2")
    if selected != "all" and selected in set(valid.iso_alpha):
        selected_codes = set(data.iso_alpha) | {selected}
        data = valid[valid.iso_alpha.isin(selected_codes)].sort_values("co2")
    colors = [BLUE if iso == selected else "#70AFE0" for iso in data.iso_alpha]
    if selected == "all" and colors:
        colors[-1] = BLUE
    fig = go.Figure(go.Bar(
        y=data.country, x=data.co2, orientation="h", marker_color=colors,
        customdata=data[["iso_alpha", "year"]],
        text=data.co2.map("{:,.1f}".format), texttemplate="%{text}", textposition="outside",
        cliponaxis=False, textfont={"size": 12, "color": TEXT}, width=.55,
        hovertemplate=(
            "<b>%{y}</b> · Năm %{customdata[1]}<br>CO₂ trong năm: <b>%{text} triệu tấn</b>"
            "<br>Bấm để chọn quốc gia<extra>OWID / GCP</extra>"
        ),
    ))
    tao_kieu_bieu_do(fig, max(height, len(data) * 28 + 70))
    fig.update_layout(
        margin={"l": 14, "r": 60, "t": 8, "b": 48},
        uniformtext={"minsize": 12, "mode": "show"},
    )
    fig.update_xaxes(
        title="CO₂ (triệu tấn)", range=[0, max(float(data.co2.max()) * 1.23, 1)],
        tickformat=",.0f", nticks=5,
    )
    fig.update_yaxes(showgrid=False, showline=False, tickfont={"color": TEXT})
    return fig


def tao_ban_do_the_gioi(
    snapshot, selected="VNM", metric="temperature", reset=0, rotation=None,
    height=520, view_mode="globe", chu_thich_ngang=False,
):
    field = "co2" if metric == "co2" else "temperature_anomaly"
    is_co2 = metric == "co2"
    snapshot = snapshot.drop_duplicates("iso_alpha").sort_values("iso_alpha", key=lambda codes: codes.eq(selected))
    valid = snapshot.dropna(subset=[field])
    missing = snapshot[snapshot[field].isna()]
    temperature_colors = [(-6, "#164E89"), (-2, "#5BA4CF"), (0, "#F5F2ED"),
                          (1, "#F5B06E"), (2, "#E65C36"), (3, "#BD2A27"), (6, "#690F24")]
    colorscale = ([[0, "#e3effb"], [1, BLUE]] if is_co2 else
                  [[(value + 6) / 12, color] for value, color in temperature_colors])
    if is_co2 and not valid.empty:
        zmin, zmax = 0, max(float(valid[field].max()), 1)
    else:
        zmin, zmax = -6, 6
    fig = go.Figure()
    for rows, has_data in [(missing, False), (valid, True)]:
        if rows.empty:
            continue
        value_label = "CO₂: %{text} triệu tấn" if is_co2 else "So với 1951–1980: %{text} °C"
        fig.add_choropleth(
            locations=rows.iso_alpha, z=rows[field] if has_data else [0] * len(rows),
            locationmode="ISO-3", customdata=rows[["country", "year"]],
            text=(rows[field].map(("{:,.2f}" if is_co2 else "{:+.2f}").format) if has_data else
                  ["Ngoài châu lục đang chọn" if outside else "Chưa có số liệu"
                   for outside in rows.get("outside_scope", [False] * len(rows))]),
            colorscale=colorscale if has_data else [[0, "#dce3eb"], [1, "#dce3eb"]],
            zmin=zmin, zmax=zmax, showscale=has_data,
            marker_line_color=["#FFD54A" if iso == selected else MAP_BORDER for iso in rows.iso_alpha],
            marker_line_width=[3 if iso == selected else .75 for iso in rows.iso_alpha],
            name=("CO₂" if is_co2 else "Nhiệt độ") if has_data else "Chưa có dữ liệu",
            colorbar={
                "title": {"text": "triệu tấn" if is_co2 else "°C",
                          "side": "top", "font_size": 11, "font_color": TEXT},
                "orientation": "v", "xref": "container", "x": .99, "xanchor": "right", "y": .5,
                "yanchor": "middle", "len": .62, "thickness": 8,
                "tickfont": {"size": 10, "color": MUTED}, "outlinewidth": 0,
            },
            hovertemplate="<b>%{customdata[0]}</b> · %{customdata[1]}<br>"
                          + (value_label if has_data else "%{text}") + "<extra></extra>",
        )

    is_flat = view_mode == "flat"
    rotation = rotation or {"lon": 105, "lat": 15}
    initial_rotation = {"lon": 0, "lat": 0, "roll": 0} if is_flat else rotation
    fig.update_geos(
        projection_type="natural earth" if is_flat else "orthographic",
        projection_rotation=initial_rotation, projection_scale=1,
        center={"lon": initial_rotation["lon"], "lat": initial_rotation["lat"]},
        fitbounds=False,
        resolution=110, showcoastlines=True, coastlinecolor="#7893A3",
        coastlinewidth=.7, showcountries=True, countrycolor=MAP_BORDER, countrywidth=.75,
        showland=True, landcolor="#dce3eb",
        showocean=True, oceancolor="#163E5C", showlakes=False,
        showrivers=False, bgcolor="rgba(0,0,0,0)",
        showframe=True, framecolor="#87ACBB", framewidth=1,

        lonaxis={"showgrid": False, "range": [-180, 180]},
        lataxis={"showgrid": False, "range": [-90, 90]},
    )
    fig.update_layout(
        height=height, margin={"l": 48, "r": 48, "t": 4, "b": 4, "autoexpand": False},
        paper_bgcolor="white", font={"family": FONT_FAMILY, "color": MUTED},
        showlegend=False, geo_uirevision=f"{view_mode}-{reset}", clickmode="event",
        dragmode="pan", hovermode="closest", transition={"duration": 0},
        meta={"selected": selected, "globe_rotation": rotation, "metric": metric,
              "year": int(snapshot.year.max()) if not snapshot.empty else None,
              "chu_thich_ngang": chu_thich_ngang},
        hoverlabel={"bgcolor": "white", "bordercolor": "#DCE7F1", "font": {"color": TEXT, "size": 13}},
    )
    if chu_thich_ngang:
        fig.update_traces(colorbar={"orientation": "h", "xref": "paper", "x": .5, "xanchor": "center",
                                   "y": -.01, "yanchor": "top", "len": .5, "thickness": 6,
                                   "nticks": 4, "tickvals": None if is_co2 else [-6, -3, 0, 3, 6],
                                   "title": {"side": "right"}})
        fig.update_layout(margin={"l": 16, "r": 16, "t": 4, "b": 50, "autoexpand": False})
    return fig


def tao_bieu_do_nganh(totals, height=290):
    if totals.empty or totals.sum() <= 0:
        return tao_bieu_do_trong("Năm này chưa có dữ liệu theo ngành", height)
    shares = (totals / totals.sum() * 100).sort_values()
    fig = go.Figure(go.Bar(
        y=shares.index, x=shares, orientation="h", width=.55,
        customdata=totals.reindex(shares.index),
        marker_color=["#AECAC4"] * (len(shares) - 1) + ["#169873"],
        text=shares.map(lambda v: "<0.1%" if 0 < v < .05 else f"{v:.1f}%"),
        texttemplate="%{text}", textposition="outside",
        cliponaxis=False, hovertemplate=("<b>%{y}</b><br>CO₂: %{customdata:,.1f} triệu tấn"
                                        "<br>Tỷ trọng trong các ngành có số liệu: %{text}<extra>EDGAR</extra>"),
    ))
    tao_kieu_bieu_do(fig, height)
    fig.update_layout(margin={"l": 12, "r": 40, "t": 12, "b": 35})
    fig.update_xaxes(range=[0, shares.max() * 1.25], ticksuffix="%", nticks=4)
    fig.update_yaxes(showgrid=False, tickfont_size=11)
    return fig


def tao_bieu_do_ty_trong_chau_luc(snapshot, continent_names, selected="all", height=350):
    totals = (
        snapshot.dropna(subset=["continent", "co2"])
        .groupby("continent").co2.sum(min_count=1)
        .loc[lambda values: values > 0]
        .sort_values(ascending=False)
    )
    if totals.empty:
        return tao_bieu_do_trong("Năm này chưa có dữ liệu CO₂", height)
    names = [continent_names.get(name, name) for name in totals.index]
    colors = {
        "Africa": "#00A881", "Asia": "#E9604D", "Europe": "#9563CC",
        "North America": "#5575CE", "Oceania": "#19A5B8",
        "South America": "#E89741", "Antarctica": "#96A7BA",
    }
    fig = go.Figure(go.Pie(
        labels=names,
        values=totals.values,
        customdata=[[name, int(snapshot.year.iloc[0])] for name in totals.index],
        hole=.62,
        sort=False,
        direction="clockwise",
        rotation=-35,
        domain={"x": [0, .62], "y": [.06, .94]},
        marker={
            "colors": [colors.get(name, "#96A7BA") for name in totals.index],
            "line": {
                "color": [TEXT if name == selected else "white" for name in totals.index],
                "width": [2.5 if name == selected else 1.5 for name in totals.index],
            },
        },
        textinfo="none",
        hovertemplate=("<b>%{label}</b> · Năm %{customdata[1]}"
                       "<br>CO₂: %{value:,.1f} triệu tấn"
                       "<br>Tỷ trọng: %{percent:.1%}<br>Trong tổng các nước có số liệu"
                       "<extra>OWID / GCP</extra>"),
    ))
    tao_kieu_bieu_do(fig, height)
    fig.update_layout(
        margin={"l": 16, "r": 16, "t": 8, "b": 8},
        showlegend=True,
        legend={
            "orientation": "v", "x": .68, "xanchor": "left",
            "y": .5, "yanchor": "middle", "font": {"size": 11, "color": TEXT},
            "itemclick": False, "itemdoubleclick": False,
        },
        annotations=[{
            "text": (
                f"<span style='font-size:18px'><b>{totals.sum() / 1000:,.1f}</b></span><br>"
                "<span style='font-size:10px;color:#6B7F93'>tỷ tấn</span>"
            ),
            "x": .31, "y": .5, "showarrow": False,
            "xref": "paper", "yref": "paper", "xanchor": "center", "yanchor": "middle",
            "font": {"size": 12, "color": TEXT},
        }],
    )
    return fig


SCENARIO_COLORS = {
    "trend": "#E4572E", "stable": "#C08A20",
    "decline": "#169873", "custom": "#7656C9",
}


def tao_bieu_do_du_bao_nhiet_do(history, scenarios, active_id, milestone=2050):
    active = scenarios[scenarios.scenario_id == active_id]
    point = active[active.year == milestone].iloc[0]
    color = SCENARIO_COLORS[active_id]
    temperature_trend = history.temperature_anomaly.rolling(5).mean()
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=active.year, y=active.upper_90, mode="lines",
        line_width=0, hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=active.year, y=active.lower_90, mode="lines", line_width=0,
        fill="tonexty", fillcolor="rgba(118,140,163,.13)", hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=history.year, y=temperature_trend,
        text=temperature_trend.map("{:+.2f}".format),
        name="Thực tế · Trung bình 5 năm", mode="lines",
        line={"color": TEXT, "width": 2.5},
        hovertemplate=("Năm %{x} · Toàn cầu<br>Trung bình 5 năm: <b>%{text} °C</b>"
                       "<br>So với trung bình 1951–1980<extra>NASA GISTEMP</extra>"),
    ))
    for scenario_id, group in scenarios.groupby("scenario_id", sort=False):
        fig.add_trace(go.Scatter(
            x=group.year, y=group.temperature_prediction,
            name=group.scenario.iloc[0], mode="lines",
            line={"color": SCENARIO_COLORS[scenario_id],
                  "width": 3 if scenario_id == active_id else 1.8, "dash": "dash"},
            opacity=1 if scenario_id == active_id else .65,
            customdata=group[["scenario_id", "lower_90", "upper_90", "annual_change_pct"]],
            hovertemplate=("Năm %{x} · Toàn cầu<br>Xu hướng nhiệt độ: <b>%{y:+.2f} °C</b>"
                           "<br>So với trung bình 1951–1980"
                           "<br>Khoảng dự báo 90%: %{customdata[1]:+.2f} – %{customdata[2]:+.2f} °C"
                           "<br>Giả định CO₂ hằng năm: %{customdata[3]:+.2f}%/năm"
                           "<extra>%{fullData.name}</extra>"),
        ))
    tao_kieu_bieu_do(fig, 350)
    fig.add_vrect(x0=2024.5, x1=2051, fillcolor="#F2F6FA", opacity=.6,
                  line_width=0, layer="below")
    fig.add_vline(x=2024.5, line_color="#A5B4C4", line_dash="dot")
    fig.add_vline(x=milestone, line_color=color, line_width=1, line_dash="dot")
    fig.add_trace(go.Scatter(
        x=[milestone], y=[point.temperature_prediction], mode="markers",
        marker={"color": color, "size": 9, "line": {"color": "white", "width": 2}},
        hoverinfo="skip",
    ))
    fig.add_annotation(
        x=milestone, y=point.temperature_prediction,
        text=f"<b>{point.temperature_prediction:+.2f}°C</b> · {milestone}",
        showarrow=True, arrowhead=0, arrowcolor=color, ax=-45, ay=-35,
        bgcolor="white", bordercolor=color, borderpad=6, font_color=color,
    )
    start = int(history.year.min())
    for x, label in (((start + history.year.max()) / 2, "THỰC TẾ"), (2037, "DỰ ĐOÁN")):
        fig.add_annotation(x=x, y=1.06, yref="paper", text=label,
                           showarrow=False, font={"size": 10, "color": MUTED})
    fig.update_layout(hovermode="closest", margin={"l": 52, "r": 20, "t": 30, "b": 35})
    fig.update_xaxes(range=[start, 2052], tickvals=[*range(start, 2050, 40), 2050], showgrid=False)
    fig.update_yaxes(dtick=.5, tickformat=".1f", ticksuffix="°")
    return fig


def tao_bieu_do_kich_ban_co2(scenarios, active_id, milestone=2050):
    fig = go.Figure()
    for scenario_id, group in scenarios.groupby("scenario_id", sort=False):
        fig.add_trace(go.Scatter(
            x=group.year, y=group.co2 / 1000, name=group.scenario.iloc[0],
            text=(group.co2 / 1000).map("{:.1f}".format),
            customdata=group[["scenario_id", "annual_change_pct"]],
            mode="lines", line={"color": SCENARIO_COLORS[scenario_id],
                                 "width": 3 if scenario_id == active_id else 1.8},
            opacity=1 if scenario_id == active_id else .65,
            hovertemplate=("Năm %{x} · Toàn cầu<br>CO₂ trong năm: <b>%{text} tỷ tấn</b>"
                           "<br>Giả định thay đổi: %{customdata[1]:+.2f}%/năm"
                           "<extra>%{fullData.name}</extra>"),
        ))
    tao_kieu_bieu_do(fig, 230)
    fig.add_vline(x=milestone, line_color="#A5B4C4", line_dash="dot")
    fig.update_layout(hovermode="closest", margin={"l": 45, "r": 20, "t": 12, "b": 35})
    fig.update_xaxes(dtick=10, range=[2024, 2051], showgrid=False)
    fig.update_yaxes(rangemode="tozero", title="CO₂ (tỷ tấn)", nticks=4)
    return fig


def tao_bieu_do_kiem_tra_du_bao(backtest):
    fig = go.Figure()
    for field, name, color, dash in (
        ("temperature_trend_5y", "Thực tế", TEXT, "solid"),
        ("temperature_prediction", "Dự đoán", BLUE, "dash"),
    ):
        fig.add_trace(go.Scatter(
            x=backtest.year, y=backtest[field], name=name, mode="lines+markers",
            text=backtest[field].map("{:+.3f}".format),
            line={"color": color, "width": 2, "dash": dash}, marker_size=5,
            hovertemplate=("Năm %{x} · Toàn cầu<br>Trung bình 5 năm: <b>%{text} °C</b>"
                           "<br>So với trung bình 1951–1980<extra>%{fullData.name}</extra>"),
        ))
    tao_kieu_bieu_do(fig, 230)
    fig.update_layout(
        hovermode="x unified", showlegend=True,
        legend={"orientation": "h", "y": 1.02, "x": 0, "font_size": 11},
        margin={"l": 45, "r": 20, "t": 30, "b": 35},
    )
    fig.update_xaxes(dtick=3, showgrid=False)
    low = backtest[["temperature_trend_5y", "temperature_prediction"]].min().min()
    high = backtest[["temperature_trend_5y", "temperature_prediction"]].max().max()
    ticks = [i / 10 for i in range(int(low * 10), int(high * 10) + 2)]
    fig.update_yaxes(tickvals=ticks, ticktext=[f"{v:.1f}°" for v in ticks])
    return fig


def tao_bieu_do_phan_du(residuals):
    """Biểu đồ phần dư theo thời gian để nhận ra mẫu sai số và điểm ảnh hưởng."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=residuals.year, y=residuals.residual, mode="lines",
        line={"color": "#CBD5E1", "width": 1}, hoverinfo="skip", showlegend=False,
    ))
    for influential, name, color in (
        (False, "Thông thường", BLUE), (True, "Cần xem", "#E89741")
    ):
        data = residuals[residuals.influential == influential]
        fig.add_trace(go.Scatter(
            x=data.year, y=data.residual, name=name, mode="markers",
            customdata=data[["cooks_distance", "temperature_actual", "temperature_fitted"]],
            marker={"color": color, "size": 7 if influential else 5},
            hovertemplate=("Năm %{x} · Trung bình 5 năm<br>Thực tế: %{customdata[1]:+.3f} °C"
                           "<br>Mô hình: %{customdata[2]:+.3f} °C"
                           "<br>Phần dư (thực tế − dự đoán): <b>%{y:+.3f} °C</b>"
                           "<br>Mức ảnh hưởng (Cook): %{customdata[0]:.3f}<extra>%{fullData.name}</extra>"),
        ))
    tao_kieu_bieu_do(fig, 230)
    fig.add_hline(y=0, line_color="#64748B", line_width=1)
    fig.update_layout(
        showlegend=True, legend={"orientation": "h", "y": 1.02, "x": 0, "font_size": 11},
        margin={"l": 45, "r": 20, "t": 30, "b": 35},
    )
    fig.update_xaxes(dtick=20, showgrid=False)
    fig.update_yaxes(title="Phần dư (°C)", tickformat=".2f")
    return fig
