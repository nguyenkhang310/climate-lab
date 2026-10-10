import base64
import os
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

from dash import ALL, Dash, Input, Output, State, ctx, dcc, html, no_update
from dash.exceptions import MissingCallbackContextException
from flask import send_from_directory
from mo_hinh_du_doan.nguyen_khang.mo_hinh_nhiet_do import tao_kich_ban
from phan_tich_nhiet_do.duc.tao_bieu_do_plotly import CHARTS, build_figures as temperature_figures
from phan_tich_co2.quan.tao_bieu_do_plotly import (
    CHARTS as CO2_CHARTS, build_figures as co2_figures,
    renewable_coverage_note, sector_coverage_note,
)

from .bieu_do import (
    SCENARIO_COLORS,
    tao_bieu_do_kiem_tra_du_bao,
    tao_bieu_do_co2,
    tao_bieu_do_ty_trong_chau_luc,
    tao_bieu_do_nganh,
    tao_ban_do_the_gioi,
    tao_bieu_do_xep_hang,
    tao_bieu_do_phan_du,
    tao_bieu_do_kich_ban_co2,
    tao_bieu_do_du_bao_nhiet_do,
    tao_bieu_do_nhiet_do,
    tao_bieu_do_trong,
    tao_kieu_bieu_do,
)
from .du_lieu import (
    BACKTEST_DATA,
    CONTINENTS,
    CONTINENT_NAMES,
    COORDINATES,
    COUNTRY_NAMES,
    DATA,
    GLOBAL_DATA,
    GLOBAL_CO2,
    TEMPERATURE_DATA,
    MODEL_INFO,
    RESIDUAL_DATA,
    SCENARIO_DATA,
    tong_hop_du_lieu,
    loc_du_lieu,
    loc_du_lieu_thang,
    loc_du_lieu_nganh,
    tong_co2_theo_nganh,
    chuoi_nhiet_do,
)
from .thap_ky import tuy_chon_thap_ky

app = Dash(
    __name__,
    serve_locally=not os.environ.get("VERCEL"),
    assets_folder=str(Path(__file__).with_name("tai_nguyen")),
    assets_ignore=r".*\.json",
    suppress_callback_exceptions=True,
    title="Climate Lab · HCMUTE",
    update_title=None,
)
server = app.server
ROOT = Path(__file__).resolve().parents[2]
EDA_ROOT = {"duc": ROOT / "phan_tich_nhiet_do/duc/bieu_do",
            "quan": ROOT / "phan_tich_co2/quan/bieu_do"}


@server.get("/eda-files/<member>/<path:filename>")
def phuc_vu_tep_eda(member, filename):
    if member not in EDA_ROOT:
        return "Không có biểu đồ", 404
    return send_from_directory(EDA_ROOT[member], filename)


DUC_TEMPERATURE_ARTIFACTS = [
    (title, period, f"duc/{folder}/{name}.{extension}")
    for (name, title), period in zip(CHARTS, [
        "NASA GISTEMP · 1880–2025", "NASA GISTEMP · 1880–2025",
        "FAOSTAT · 2020–2025", "FAOSTAT · 1961–2025",
        "FAOSTAT · 1961–2025", "NASA GISTEMP · 1880–2025",
    ])
    for folder, extension in [("tinh", "png"), ("tuong_tac", "html")]
]

QUAN_ARTIFACTS = [
    ("Lượng CO₂ toàn cầu", "2024 gấp 2,59 lần năm 1970",
     "quan/tinh/01_line_co2_toan_cau.png"),
    ("Top 15 quốc gia thải CO₂", "2023 · Trung Quốc gấp 2,47 lần Mỹ",
     "quan/tinh/02_bar_top15_quoc_gia.png"),
    ("Lượng CO₂ theo ngành", "1970–2024 · Điện chiếm 40,8% năm 2024",
     "quan/tinh/03_area_co_cau_nganh.png"),
    ("CO₂/người và năng lượng tái tạo", "2023 · Tương quan −0,49; không phải nhân quả",
     "quan/tinh/04_scatter_co2pc_renewable.png"),
    ("Độ phủ dữ liệu theo năm", "Tái tạo năm 2024: 84 quốc gia có số liệu",
     "quan/tinh/05_line_do_phu_du_lieu.png"),
] + [(title, "", f"quan/tuong_tac/{name}.html") for name, title in CO2_CHARTS]

MENU = [
    ("overview", "Tổng quan", "grid"),
    ("earth", "Bản đồ khí hậu", "globe"),
    ("temperature", "Nhiệt độ", "thermometer"),
    ("co2", "Khí thải CO₂", "cloud"),
    ("scenario", "Mô hình dự đoán", "trend"),
    ("insights", "Nhận định", "bulb"),
    ("data", "Dữ liệu", "database"),
]

PAGE_INFO = {key: title for key, title, _ in MENU}
PAGE_INFO["overview"] = "Tổng quan khí hậu"
MAP_VIEW_OPTIONS = [
    {"label": "Địa cầu", "value": "globe"},
    {"label": "Bản đồ phẳng", "value": "flat"},
]
SCENARIO_LABELS = {"trend": "Tiếp diễn", "stable": "Giữ mức 2024",
                   "decline": "Giảm 5%/năm", "custom": "Tùy chỉnh"}
PATHS = {
    "grid": '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
    "globe": '<circle cx="12" cy="12" r="9"/><ellipse cx="12" cy="12" rx="4" ry="9"/><path d="M3 12h18M5 6.5h14M5 17.5h14"/>',
    "thermometer": '<path d="M9 14V5a3 3 0 0 1 6 0v9a5 5 0 1 1-6 0Z"/><path d="M12 8v10"/><circle cx="12" cy="18" r="1.5"/>',
    "cloud": '<path d="M6 18a4 4 0 0 1-.7-7.9A6 6 0 0 1 17 8a5 5 0 0 1 1 10Z"/>',
    "compare": '<path d="M4 7h15l-4-4M20 17H5l4 4M19 7l-4 4M5 17l4-4"/>',
    "scatter": '<path d="M4 3v17h17"/><circle cx="8" cy="15" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="15" cy="8" r="1"/><circle cx="19" cy="6" r="1"/>',
    "chart": '<path d="M3 21h18M6 17v-6M12 17V5M18 17v-9"/>',
    "trend": '<path d="m3 17 6-6 4 3 8-10M15 4h6v6"/>',
    "bulb": '<path d="M9 18h6M9 21h6M8 14a6 6 0 1 1 8 0l-1 2H9Z"/>',
    "database": '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 4 16 4 16 0V5M4 12c0 4 16 4 16 0"/>',
    "menu": '<path d="M4 6h16M4 12h16M4 18h16"/>',
    "calendar": '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M7 3v4M17 3v4M3 10h18M7 14h3M14 14h3"/>',
    "reset": '<path d="M3 10a9 9 0 1 1 1 8M3 3v7h7"/>',
    "download": '<path d="M12 3v12m-5-5 5 5 5-5M4 16v5h16v-5"/>',
}

def bieu_tuong(name, class_name="icon"):
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
        'fill="none" stroke="#708399" stroke-width="1.7" '
        f'stroke-linecap="round" stroke-linejoin="round">{PATHS[name]}</svg>'
    )
    encoded_svg = base64.b64encode(svg.encode()).decode()
    return html.Img(
        src="data:image/svg+xml;base64," + encoded_svg,
        className=class_name,
        alt="",
    )

def _tao_truong_loc(label, dropdown_id, options, value, symbol,
                  field_id=None, field_class="filter-field", **dropdown_props):
    wrapper = {"className": field_class}
    if field_id is not None:
        wrapper["id"] = field_id
    return html.Div([
        html.Label([bieu_tuong(symbol), label], htmlFor=dropdown_id),
        dcc.Dropdown(options, value, id=dropdown_id, clearable=False, **dropdown_props),
    ], **wrapper)

def cap_nhat_ban_do(snapshot, selected, metric, mode, resets, current, reset=False):
    layout = current["layout"]

    projection = layout["geo"]["projection"]
    rotation = (projection["rotation"] if projection["type"] == "orthographic"
                else layout["meta"]["globe_rotation"])
    if reset:
        rotation = {"lon": 105, "lat": 15}
    return tao_ban_do_the_gioi(snapshot, selected, metric, resets or 0, rotation, view_mode=mode or "globe")

def lay_du_lieu_ban_do(frame, year):
    snapshot = DATA[DATA.year.eq(year)].copy()
    snapshot["outside_scope"] = ~snapshot.iso_alpha.isin(frame.iso_alpha)
    snapshot.loc[snapshot.outside_scope, ["co2", "temperature_anomaly"]] = float("nan")
    return snapshot

def tao_tieu_de_ban_do(view_id, reset_id):
    return html.Div([
        html.Div([bieu_tuong("globe"), html.H3("Bản đồ thế giới")], className="globe-heading"),
        html.Div([
            dcc.RadioItems(id=view_id, options=MAP_VIEW_OPTIONS, value="globe", inline=True,
                           className="map-view-switch"),
            html.Button(bieu_tuong("reset"), id=reset_id, n_clicks=0, className="overview-reset",
                        title="Đặt lại góc nhìn", **{"aria-label": "Đặt lại góc nhìn"}),
        ], className="map-controls"),
    ], className="overview-map-header")

def tao_dau_trang():
    identity = html.Div([
        html.A([
            html.Img(src=app.get_asset_url("hcmute-logo.png"), className="school-logo", alt="Logo HCMUTE"),
            html.Div([
                html.Span("TRƯỜNG ĐẠI HỌC", className="school-top"),
                html.Strong("CÔNG NGHỆ KỸ THUẬT TP. HỒ CHÍ MINH"),
            ], className="school-name"),
        ], href="#overview", className="school-brand", **{"aria-label": "Về trang tổng quan"}),
        html.Span(className="header-divider"),
        html.Div([
            html.Strong("CLIMATE LAB"),
            html.Span("Phân tích dữ liệu khí hậu"),
        ], className="product-brand"),
    ], className="header-identity")
    actions = html.Div([
        html.Div([
            bieu_tuong("calendar"),
            html.Div([
                html.Span("Phạm vi dữ liệu"),
                html.Strong(f"{int(TEMPERATURE_DATA.year.min())}–{int(GLOBAL_DATA.year.max())}", id="header-data-range"),
            ]),
        ], className="header-data-range"),
        html.Button([bieu_tuong("download"), html.Span("Tải CSV")], id="header-export",
                    className="header-export", title="Tải dữ liệu đang lọc", n_clicks=0),
    ], className="header-actions")
    return html.Header([identity, actions], className="header")

def tao_thanh_ben():
    links = [
        html.A([bieu_tuong(symbol), html.Span(label, className="nav-label")],
               href=f"#{key}", title=label, id={"type": "nav", "index": key},
               className="nav-item" + (" active" if key == "overview" else ""))
        for key, label, symbol in MENU
    ]
    return [
        html.Div([
            html.Div([
                html.Strong("CLIMATE", className="sidebar-brand"),
                html.Span("DASHBOARD", className="sidebar-caption"),
            ], className="nav-label"),
            html.Button(bieu_tuong("menu"), id="collapse-sidebar", className="icon-button",
                        title="Thu gọn / mở rộng thanh điều hướng", n_clicks=0),
        ], className="sidebar-top"),
        html.Nav([html.Div("Khám phá dữ liệu", className="nav-section"), *links],
                 **{"aria-label": "Điều hướng chính"}),
        html.Footer([
            html.Div(html.Img(src=app.get_asset_url("shipcode-logo.png"), alt="Logo Team Shipcode",
                             className="sidebar-user-logo"), className="sidebar-user-avatar"),
            html.Div([
                html.Span("Phát triển bởi"),
                html.Strong("Nhóm 18"),
                html.Small("TEAM SHIPCODE"),
            ], className="sidebar-user-copy nav-label"),
        ], className="sidebar-credit"),
    ]

def tao_bo_loc():
    start, end = int(TEMPERATURE_DATA.year.min()), int(GLOBAL_DATA.year.max())
    return html.Div([
        _tao_truong_loc("Thập kỷ", "year-range", tuy_chon_thap_ky(start, end),
                      f"{start}-{end}", symbol="calendar", field_class="filter-years", searchable=False),
        _tao_truong_loc("Châu lục", "continent-filter", [
            {"label": "Tất cả châu lục", "value": "all"},
            *[{"label": CONTINENT_NAMES[name], "value": name} for name in CONTINENTS],
        ], "all", symbol="globe", searchable=False),
        _tao_truong_loc("Quốc gia", "country-filter", [
            {"label": "Tất cả quốc gia", "value": "all"},
            *[{"label": name, "value": iso} for iso, name in COUNTRY_NAMES.items()],
        ], "all", symbol="globe", field_id="country-field", placeholder="Tìm quốc gia…"),
        _tao_truong_loc("Màu bản đồ", "metric-filter", [
            {"label": "Nhiệt độ", "value": "temperature"},
            {"label": "Khí thải CO₂", "value": "co2"},
        ], "temperature", symbol="chart", field_id="metric-field", searchable=False),
    ], id="filter-bar", className="filter-bar")

def khung_bieu_do(figure, graph_id=None, globe=False):
    config = {
        "displayModeBar": False if globe else "hover",
        "displaylogo": False,
        "scrollZoom": False,
        "topojsonURL": "/assets/",
        "showTips": not globe,
        "doubleClick": False if globe else "reset+autosize",
        "modeBarButtonsToRemove": ["select2d", "lasso2d"],
        "toImageButtonOptions": {
            "filename": "climate-lab",
            "scale": 2,
        },
    }
    options = {
        "figure": figure,
        "config": config,
        "className": "chart",
        "responsive": True,
        "style": {"height": figure.layout.height},
    }
    if graph_id:
        options["id"] = graph_id
    return dcc.Graph(**options)

def tao_the_bieu_do(title, subtitle, figure, symbol="trend", graph_id=None):
    heading = html.Div([
        html.Div([bieu_tuong(symbol), html.H3(title)], className="chart-title"),
        html.P(subtitle),
    ], className="chart-heading")
    return html.Section([
        html.Div(heading, className="card-header"), khung_bieu_do(figure, graph_id),
    ], className="card chart-card")


def tao_noi_dung_eda(title, subtitle, path, large=False):
    source = f"/eda-files/{path}"
    label = title if not subtitle else f"{title} — {subtitle}"
    size = "modal" if large else "artifact"
    return html.Img(
        src=source,
        alt=label,
        className=f"eda-{size}-image",
    )


def tao_the_eda(title, subtitle, path, figure=None):
    heading = [html.H3(title)]
    if subtitle:
        heading.append(html.P(subtitle, className="small-meta"))
    return html.Article([
        html.Div([
            html.Div(heading),
            html.Button(
                "Mở rộng",
                id={"type": "expand-eda", "path": path},
                n_clicks=0,
                className="eda-expand-button",
                title=f"Mở rộng {title}",
            ),
        ], className="eda-artifact-heading"),
        khung_bieu_do(figure, {"type": "eda-chart", "path": path}) if figure is not None
        else tao_noi_dung_eda(title, subtitle, path),
    ], className="card eda-artifact-card")


def tao_thu_vien_eda_thanh_vien(artifacts, gallery_id, figures, notes, scope, period):
    cards = []
    fields = {"choropleth": "z", "heatmap": "z", "treemap": "values"}
    interactive = [item for item in artifacts if item[2].endswith(".html")]
    for (title, _, path), note in zip(interactive, notes):
        figure = figures[Path(path).stem]
        values = [getattr(trace, fields.get(trace.type, "y"), None) for trace in figure.data]
        if not any(value is not None and len(value) and pd.notna(value).any() for value in values):
            figure = tao_bieu_do_trong()
        chart_scope = f"{scope} · Dữ liệu {period} · {note}"
        tao_kieu_bieu_do(figure, 380)
        figure.update_layout(title=None,
                             meta=dict(scope=chart_scope),
                             showlegend=len(figure.data) > 1 and not path.endswith("05_phan_bo_nhiet_do_quoc_gia.html"),
                             legend=dict(y=-.23, yanchor="top", font_size=10, title=None),
                             margin=dict(l=16, r=24, t=16, b=90))
        figure.update_xaxes(nticks=7, title_font_size=11)
        figure.update_yaxes(nticks=6, title_font_size=11)
        figure.update_coloraxes(colorbar=dict(title=dict(side="right", font_size=10), thickness=10, len=.85))
        figure.update_geos(projection_type="natural earth", showframe=False, bgcolor="white")
        if figure.frames:
            figure.update_layout(margin_b=105)
            figure.layout.sliders[0].update(x=.05, len=1, pad=dict(t=48, b=0),
                                            currentvalue=dict(prefix="Thập kỷ: ", xanchor="right", font_size=12))
            figure.layout.updatemenus[0].update(x=0, xanchor="left", pad=dict(t=8, r=0))
        for trace in figure.data:
            trace.name = CONTINENT_NAMES.get(trace.name, trace.name)
        if figure.data and figure.data[0].type == "heatmap":
            figure.update_yaxes(tickvals=list(figure.data[0].y),
                                ticktext=[CONTINENT_NAMES.get(name, name) for name in figure.data[0].y])
        cards.append(tao_the_eda(title.replace(" toàn cầu", ""), chart_scope, path, figure))
    return html.Section([
        html.Div([
            html.Div([
                html.H3("Biểu đồ tương tác"),
                html.P(f"{scope} · {period}", className="small-meta"),
            ], className="eda-format-heading"),
            html.Div(cards, className="eda-artifact-grid interactive"),
        ], className="eda-format-section interactive"),
        html.Details([
            html.Summary("Biểu đồ tĩnh · Không áp dụng bộ lọc"),
            html.Div([tao_the_eda(*item) for item in artifacts if item[2].endswith(".png")],
                     className="eda-artifact-grid static"),
        ], className="eda-format-section static"),
    ], id=gallery_id, className="eda-gallery")

def ten_pham_vi(continent, country):
    return COUNTRY_NAMES.get(country, "Toàn cầu" if continent == "all" else CONTINENT_NAMES.get(continent, continent))

def dinh_dang_so(value, pattern, missing="—"):
    return missing if pd.isna(value) else format(value, pattern)

def lay_cac_nam_ban_do(frame, selected):
    chosen = frame if selected == "all" else frame[frame.iso_alpha == selected]
    return sorted(int(year) for year in chosen.year.unique())

def tao_moc_thanh_truot(years):
    first, last = years[0], years[-1]
    return {
        year: str(year)
        for year in years
        if year in (first, last) or (year % 10 == 0 and last - year >= 7)
    }

def lay_quoc_gia_duoc_chon(click_data, available):
    if not click_data or not click_data.get("points"):
        return None

    point = click_data["points"][0]
    country = point.get("location") or point.get("customdata")
    if isinstance(country, (list, tuple)):
        country = country[0] if country else None
    return country if isinstance(country, str) and country in available else None

def tao_chi_tiet_tong_quan(frame, selected, year, scope):
    chosen = frame if selected == "all" else frame[frame.iso_alpha == selected]
    series = tong_hop_du_lieu(chosen, use_global=selected == "all" and scope == "Toàn cầu")
    available_years = set(series.year.astype(int))
    if year not in available_years:
        year = int(series.year.max())
    row = series[series.year == year].iloc[0]
    period = f"{int(series.year.min())} – {int(series.year.max())}"
    if selected == "all":
        region = f"{chosen.iso_alpha.nunique()} quốc gia và vùng lãnh thổ"
    else:
        region = CONTINENT_NAMES.get(chosen.iloc[0].continent, "")
    metrics = [
        ("Chênh lệch nhiệt độ", dinh_dang_so(row.temperature_anomaly, "+.2f"), "°C so với 1951–1980", "red"),
        ("Lượng CO₂", dinh_dang_so(row.co2, ",.1f"), "triệu tấn", "blue"),
        ("CO₂ mỗi người", dinh_dang_so(row.co2_per_capita, ".2f"), "tấn/người", "blue"),
    ]
    summary = [
        html.Div([
            html.Div([
                html.H2(scope),
                html.P(region),
            ]),
            html.Span(str(year), className="selection-year"),
        ], className="selection-heading"),
        html.Div([
            html.Div([
                html.Span(label),
                html.Strong(value, className=tone),
                html.Small(unit),
            ])
            for label, value, unit, tone in metrics
        ], className="selection-metrics"),
    ]
    temperature = (tao_bieu_do_trong("Nhiệt độ quốc gia chỉ có từ 1961", 200)
                   if series.year.max() < 1961 and series.temperature_anomaly.isna().all()
                   else tao_bieu_do_nhiet_do(series, 200))
    co2 = tao_bieu_do_co2(series, 200)
    for figure in (temperature, co2):
        figure.add_vline(x=year, line_width=1, line_dash="dot", line_color="#8496AA")
    return summary, temperature, co2, f"{scope} · {period}"

def tao_so_sanh_tong_quan(frame, selected, year):
    snapshot = frame[frame.year == year]
    world = DATA[DATA.year == year]
    highlighted = "all"
    if selected != "all":
        highlighted = snapshot.loc[snapshot.iso_alpha.eq(selected), "continent"].iloc[0]
    elif frame.continent.nunique() == 1:
        highlighted = frame.continent.iloc[0]
    return html.Div([
        tao_the_bieu_do("Quốc gia thải CO₂ nhiều nhất", f"Top 5{' & quốc gia đang chọn' if selected != 'all' else ''} · {year} · OWID/GCP",
                          tao_bieu_do_xep_hang(snapshot, selected, limit=5, height=350),
                          "compare", "overview-ranking"),
        tao_the_bieu_do("CO₂ theo châu lục", f"Tổng quốc gia có dữ liệu · {year} · OWID/GCP",
                          tao_bieu_do_ty_trong_chau_luc(world, CONTINENT_NAMES, highlighted),
                          "globe", "overview-continents"),
    ], className="chart-grid")


def tao_trang_tong_quan(frame, selected, scope, metric):
    years = lay_cac_nam_ban_do(frame, selected)
    year = years[-1]
    snapshot = lay_du_lieu_ban_do(frame, year)
    lon, lat = COORDINATES.get(selected, (105, 15))
    globe = tao_ban_do_the_gioi(
        snapshot,
        selected,
        metric,
        rotation={"lon": lon, "lat": lat},
    )
    summary, temperature, co2, subtitle = tao_chi_tiet_tong_quan(frame, selected, year, scope)

    selection = html.Div([
        html.Span(className="selection-dot"),
        html.Span(scope, id="overview-map-selection"),
    ], className="overview-map-selection", **{"aria-live": "polite"})
    timeline = html.Div([
        html.Div([
            html.Label("Năm đang xem", htmlFor="overview-year"),
            html.Strong(str(year), id="overview-year-label"),
        ], className="overview-year-heading"),
        dcc.Slider(
            id="overview-year",
            min=years[0],
            max=years[-1],
            step=1,
            marks=tao_moc_thanh_truot(years),
            value=year,
            included=False,
            updatemode="drag",
        ),
    ], className="overview-timeline")
    map_card = html.Section([
        tao_tieu_de_ban_do("overview-map-view", "overview-reset"),
        selection,
        khung_bieu_do(globe, "overview-globe", globe=True),
        timeline,
    ], className="card overview-map-card")
    summary_card = html.Section(
        summary,
        id="overview-summary",
        className="card overview-summary",
        **{"aria-live": "polite", "aria-atomic": "true"},
    )
    temperature_card = tao_the_bieu_do(
        "Xu hướng nhiệt độ",
        html.Span(subtitle, id="overview-temperature-subtitle"),
        temperature,
        "thermometer",
        graph_id="overview-temperature",
    )
    co2_card = tao_the_bieu_do(
        "Lượng CO₂ theo thời gian",
        html.Span(subtitle, id="overview-co2-subtitle"),
        co2,
        "cloud",
        graph_id="overview-co2",
    )
    forecast = html.Section([
        html.Div([
            html.Div([html.H3("Nhiệt độ toàn cầu đến 2050"),
                      html.P("Mô hình dự đoán · Trung bình 5 năm · °C so với 1951–1980")]),
            dcc.Link("Khám phá mô hình →", href="#scenario", className="text-link"),
            tao_chu_thich_kich_ban(),
        ], className="forecast-heading"),
        khung_bieu_do(tao_bieu_do_du_bao_nhiet_do(GLOBAL_DATA, SCENARIO_DATA, "trend"), "overview-forecast"),
    ], className="card")
    return html.Div([
        html.Div([summary_card, map_card, temperature_card, co2_card], className="overview-grid"),
        html.Div(tao_so_sanh_tong_quan(frame, selected, year), id="overview-comparison"),
        forecast,
    ], className="overview-page")

def tao_chi_tiet_ban_do(frame, selected, scope):
    summary, temperature, co2, subtitle = tao_chi_tiet_tong_quan(frame, selected, int(frame.year.max()), scope)
    panel = summary
    charts = [
        tao_the_bieu_do(title, subtitle, figure.update_layout(height=260), symbol)
        for title, figure, symbol in [("Nhiệt độ qua các năm", temperature, "thermometer"),
                                     ("Lượng CO₂ qua các năm", co2, "cloud")]
    ]
    return panel, charts

def tao_trang_ban_do(frame, selected, metric, scope):
    panel, charts = tao_chi_tiet_ban_do(frame, selected, scope)
    lon, lat = COORDINATES.get(selected, (105, 15))
    figure = tao_ban_do_the_gioi(lay_du_lieu_ban_do(frame, int(frame.year.max())), selected, metric,
                          rotation={"lon": lon, "lat": lat})
    return [
        html.Div([
            html.Section([
                tao_tieu_de_ban_do("earth-map-view", "reset-globe"),
                khung_bieu_do(figure, "globe", globe=True),
            ], className="card globe-card"),
            html.Aside(panel, id="country-panel", className="card country-panel", **{"aria-live": "polite"}),
        ], className="earth-grid"),
        html.Div(charts, id="earth-lower", className="chart-grid"),
    ]


def tao_chu_thich_kich_ban():
    return html.Div([
        html.Span([html.I(style={"background": color}), SCENARIO_LABELS[key]],
                  id=f"legend-{key}", hidden=key == "custom")
        for key, color in SCENARIO_COLORS.items()
    ], className="forecast-legend")


def tao_trang_du_doan():
    def tao_chi_so(label, value_id, note_id, tone):
        return html.Div([
            html.Span(label, className="forecast-label"),
            html.Strong(id=value_id, className=tone),
            html.Small(id=note_id),
        ])

    controls = html.Section([
        html.Div([
            html.Label("Lượng CO₂ hằng năm"),
            dcc.RadioItems(
                id="scenario-choice", value="trend", className="forecast-options",
                options=[{"label": label, "value": key} for key, label in SCENARIO_LABELS.items()],
            ),
        ]),
        html.Div([
            html.Label("Mốc so sánh"),
            dcc.RadioItems(id="scenario-year", value=2050,
                           options=[2030, 2040, 2050], className="forecast-options"),
        ]),
        html.Button([bieu_tuong("download"), "CSV"], id="download-scenarios-button",
                    n_clicks=0, className="button", title="Tải dữ liệu các kịch bản"),
        html.Div([
            html.Label("Thay đổi CO₂ mỗi năm"),
            dcc.Slider(id="scenario-rate", min=-10, max=5, step=.5, value=-5,
                       updatemode="drag",
                       marks={-10: "−10%", -5: "−5%", 0: "0%", 5: "+5%"},
                       tooltip={"placement": "top"}),
        ], id="scenario-custom-control", hidden=True),
    ], className="card forecast-controls")

    main = html.Section([
        html.Div([
            tao_chi_so("Chênh lệch nhiệt độ", "scenario-temp", "scenario-temp-note", "forecast-warm"),
            tao_chi_so("So với tiếp diễn", "scenario-difference", "scenario-difference-note", "forecast-delta"),
            tao_chi_so("Lượng CO₂ / năm", "scenario-emissions", "scenario-emissions-note", "blue"),
        ], className="forecast-metrics", **{"aria-live": "polite"}),
        html.Div([
            html.Div([html.H3("Xu hướng nhiệt độ toàn cầu"),
                      html.P("Trung bình 5 năm · °C so với 1951–1980")]),
            tao_chu_thich_kich_ban(),
        ], className="forecast-heading"),
        khung_bieu_do(tao_bieu_do_du_bao_nhiet_do(GLOBAL_DATA, SCENARIO_DATA, "trend"),
              "scenario-temperature-chart"),
        html.Div([
            html.Span([html.I(style={"background": "#16324F"}), "Thực tế · Trung bình 5 năm"]),
            html.Span("Nét đứt: dự đoán · Vùng mờ: khoảng ước tính 90%"),
        ], className="forecast-chart-key"),
    ], className="card forecast-main")

    support = html.Div([
        tao_the_bieu_do("Lượng CO₂ đến 2050", "CO₂ hằng năm",
                          tao_bieu_do_kich_ban_co2(SCENARIO_DATA, "trend"),
                          "cloud", "scenario-co2-chart"),
        tao_the_bieu_do("Mô hình sát thực tế đến đâu?",
                          f"Kiểm tra 2015–2024 · Sai số trung bình {MODEL_INFO['mae_test']:.3f} °C",
                          tao_bieu_do_kiem_tra_du_bao(BACKTEST_DATA), "scatter", "scenario-backtest-chart"),
        tao_the_bieu_do("Phần dư có ngẫu nhiên không?",
                          f"Train {MODEL_INFO['train_period'][0]}–{MODEL_INFO['train_period'][1]} · "
                          f"DW {MODEL_INFO['train_durbin_watson']:.2f} · "
                          f"{MODEL_INFO['train_influential_count']} điểm cần xem",
                          tao_bieu_do_phan_du(RESIDUAL_DATA), "scatter", "scenario-residual-chart"),
    ], className="forecast-support")

    method = html.Details([
        html.Summary("Dữ liệu & phương pháp"),
        html.Div([
            html.P(f"NASA GISTEMP + OWID/GCP · Toàn cầu {MODEL_INFO['source_period'][0]}–{MODEL_INFO['source_period'][1]}."),
            html.P(f"Hồi quy CO₂ tích lũy → nhiệt độ trung bình 5 năm. R²: {MODEL_INFO['r2_test']:.3f} · "
                   f"MAE: {MODEL_INFO['mae_test']:.3f} °C · MSE: {MODEL_INFO['mse_test']:.4f} °C² · "
                   f"RMSE: {MODEL_INFO['rmse_test']:.3f} °C trên {MODEL_INFO['test_size']} giá trị "
                   "trung bình 5 năm chồng lấn."),
            html.P(f"So sánh lịch sử 1880, 1961, 1970 trên bốn giai đoạn 1995–2014: "
                   f"chọn {MODEL_INFO['selected_history_start']}, MAE {MODEL_INFO['rolling_validation_mae']:.3f} °C."),
            html.P(f"Mỗi 1.000 Gt CO₂ tích lũy đi cùng khoảng "
                   f"{MODEL_INFO['coefficient'] * 1000:.2f} °C theo mô hình. Phần dư còn tự tương quan "
                   f"(DW {MODEL_INFO['train_durbin_watson']:.2f}) và phương sai chưa đều "
                   f"(p={MODEL_INFO['train_breusch_pagan_p']:.3f}), nên không diễn giải đây là quan hệ nhân quả."),
            html.P(f"Kịch bản có điều kiện theo CO₂ và ngoại suy vượt miền dữ liệu đến 2024. "
                   f"Dải 5%–95% dùng bootstrap theo khối {MODEL_INFO['bootstrap_block_length']} năm; "
                   "chưa gồm bất định phát thải và không bảo đảm độ phủ tương lai 90%."),
        ]),
    ], className="forecast-method")
    return html.Div([controls, main, support, method,
                     dcc.Store(id="scenario-result-store")], className="forecast-page")

def tao_trang_nhan_dinh(frame, series, scope):
    start, end = int(series.year.min()), int(series.year.max())
    window = min(5, (end - start + 1) // 2)
    first = series[series.year < start + window].temperature_anomaly
    last = series[series.year > end - window].temperature_anomaly
    change = (last.mean() - first.mean() if window and len(first) == len(last) == window
              and first.notna().all() and last.notna().all() else float("nan"))
    temperature_note = (f"{start}–{start + window - 1}: {first.mean():+.2f} °C · "
                        f"{end - window + 1}–{end}: {last.mean():+.2f} °C") if pd.notna(change) else "Chưa có đủ hai giai đoạn để so sánh"
    temperature_chart = tao_bieu_do_nhiet_do(series, 320)
    if pd.notna(change):
        for left, right in [(start, start + window - 1), (end - window + 1, end)]:
            temperature_chart.add_vrect(x0=left - .5, x1=right + .5, fillcolor="#EF4444",
                                       opacity=.08, line_width=0, layer="below")
    co2 = series.dropna(subset=["co2"])
    growth, co2_note = float("nan"), "Chưa có đủ hai năm để so sánh"
    if len(co2) > 1 and co2.iloc[0].co2 > 0:
        first_co2, last_co2 = co2.iloc[0], co2.iloc[-1]
        growth = (last_co2.co2 / first_co2.co2 - 1) * 100
        co2_note = (f"{int(first_co2.year)}: {first_co2.co2:,.1f} · "
                    f"{int(last_co2.year)}: {last_co2.co2:,.1f} triệu tấn")
    totals = tong_co2_theo_nganh(frame, use_global=scope == "Toàn cầu")
    share = totals.iloc[0] / totals.sum() * 100 if not totals.empty and totals.sum() > 0 else float("nan")
    stories = [
        ("01", "Nhiệt độ", dinh_dang_so(change, "+.2f") + " °C" if pd.notna(change) else "—",
         ("Trung bình cuối kỳ cao hơn đầu kỳ" if change > 0 else "Trung bình cuối kỳ thấp hơn đầu kỳ" if change < 0
          else "Trung bình hai giai đoạn bằng nhau" if change == 0 else "Chưa đủ dữ liệu nhiệt độ"),
         temperature_note, temperature_chart, "red"),
        ("02", "Lượng CO₂", dinh_dang_so(growth, "+.1f") + "%" if pd.notna(growth) else "—",
         ("Lượng CO₂ tăng so với đầu kỳ" if growth > 0 else "Lượng CO₂ giảm so với đầu kỳ" if growth < 0
          else "Lượng CO₂ không đổi" if growth == 0 else "Chưa đủ dữ liệu CO₂"),
         co2_note, tao_bieu_do_co2(series, 290), "blue"),
        ("03", "CO₂ theo ngành", dinh_dang_so(share, ".1f") + "%" if pd.notna(share) else "—",
         f"{totals.index[0]} chiếm tỷ trọng cao nhất" if pd.notna(share) else "Chưa có dữ liệu theo ngành",
         (f"{end} · Tổng các ngành có số liệu: {totals.sum():,.1f} triệu tấn · "
          + sector_coverage_note(loc_du_lieu_nganh(frame[frame.year.eq(end)], scope == "Toàn cầu"))) if pd.notna(share) else str(end),
         tao_bieu_do_nganh(totals), "green"),
    ]
    source = ("NASA GISTEMP · Chênh nhiệt độ so với 1951–1980" if scope == "Toàn cầu"
              else "FAOSTAT · Trung bình đủ 12 tháng của năm lịch · So với trung bình 1951–1980" +
              (" · Trung bình các nước có số liệu" if frame.iso_alpha.nunique() > 1 else ""))
    return [
        html.Div([html.H2("Kết quả phân tích"), html.Span(f"{scope} · {start}–{end}")],
                 className="section-heading insight-heading"),
        html.Div([
            html.Article([
                html.Div([
                    html.Div([html.Small(label), html.Span(number)], className="insight-label"),
                    html.Strong(value, className=tone), html.H2(title), html.P(note),
                ], className="insight-copy"),
                khung_bieu_do(figure),
            ], className="card insight-card")
            for number, label, value, title, note, figure, tone in stories
        ], className="insight-grid"),
        html.Div([html.Span(source), html.Span("CO₂: OWID/GCP · Theo ngành: EDGAR")],
                 className="insight-source"),
    ]

def tao_trang_du_lieu(frame):
    columns = [
        ("country", "Quốc gia", ""),
        ("iso_alpha", "Mã quốc gia", ""),
        ("continent", "Châu lục", ""),
        ("year", "Năm", ""),
        ("temperature_anomaly", "Chênh nhiệt độ (°C)", ",.2f"),
        ("co2", "CO₂ (triệu tấn)", ",.2f"),
        ("co2_per_capita", "CO₂/người (tấn)", ",.2f"),
        ("population", "Dân số (người)", ",.0f"),
        ("renewable_percent", "Năng lượng tái tạo (%)", ",.2f"),
    ]
    ordered = frame.sort_values(["year", "country"], ascending=[False, True])
    visible = ordered.head(500)
    table_rows = [
        html.Tr([html.Td(dinh_dang_so(getattr(row, key), pattern)) for key, _, pattern in columns])
        for row in visible.itertuples()
    ]

    table = html.Table([
        html.Thead(html.Tr([html.Th(label) for _, label, _ in columns])),
        html.Tbody(table_rows),
    ], className="data-table")

    record_count = (
        f"{len(frame)} bản ghi · {frame.iso_alpha.nunique()} quốc gia · "
        f"{frame.year.nunique()} mốc năm · Hiển thị {len(visible)}/{len(frame)} dòng"
    )
    heading = html.Div([
        html.Div([
            html.Span(record_count, className="small-meta"),
        ]),
        html.Button(
            [bieu_tuong("download"), "Tải CSV đang lọc"],
            id="export-data",
            n_clicks=0,
            className="button",
        ),
    ], className="section-heading")
    source = html.Div(
        "Nguồn: NASA GISTEMP, FAOSTAT, OWID/GCP, EDGAR và UN Statistics.",
        className="card data-note",
    )
    return [
        heading,
        html.Div(table, className="card table-wrap scroll-table"),
        source,
    ]

page_heading = html.Header([
    html.Div([
        html.H1("Tổng quan khí hậu", id="page-title"),
        html.P(
            "Nhiệt độ và CO₂ theo thời gian, khu vực và quốc gia.",
            id="page-subtitle",
        ),
    ], className="page-heading-copy"),
], className="page-heading")

page_content = dcc.Loading(
    html.Div(id="page-content"),
    target_components={"page-content": "children"},
    type="circle",
    color="#0878BE",
    delay_show=250,
    overlay_style={"visibility": "visible", "opacity": .6},
)

main_content = html.Main([
    html.Div([
        page_heading,
        tao_bo_loc(),
    ], id="content-topbar", className="content-topbar"),
    page_content,
], id="main", className="main")

eda_modal = html.Div(
    html.Div([
        html.Button(
            "×", id="close-eda-modal", n_clicks=0,
            className="eda-modal-close", title="Đóng",
            **{"aria-label": "Đóng biểu đồ mở rộng"},
        ),
        html.Div(id="eda-modal-content", className="eda-modal-content"),
    ], className="eda-modal-box"),
    id="eda-modal",
    className="eda-modal",
    role="dialog",
    **{"aria-modal": "true", "aria-label": "Biểu đồ mở rộng"},
)

app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    dcc.Store(id="filter-store", data={}),
    dcc.Download(id="download-data"),
    dcc.Download(id="download-scenarios"),
    tao_dau_trang(),
    html.Aside(tao_thanh_ben(), id="sidebar", className="sidebar"),
    main_content,
    eda_modal,
], id="app-shell", className="app-shell")

@app.callback(
    Output("app-shell", "className"),
    Input("collapse-sidebar", "n_clicks"),
)
def cap_nhat_hien_thi(clicks):
    return "app-shell collapsed" if clicks and clicks % 2 else "app-shell"

@app.callback(
    Output("eda-modal", "className"),
    Output("eda-modal-content", "children"),
    Input({"type": "expand-eda", "path": ALL}, "n_clicks"),
    Input("close-eda-modal", "n_clicks"),
    Input("url", "hash"),
    Input("year-range", "value"),
    Input("continent-filter", "value"),
    Input("country-filter", "value"),
    State({"type": "eda-chart", "path": ALL}, "figure"),
    State({"type": "eda-chart", "path": ALL}, "id"),
    State("page-subtitle", "children"),
    prevent_initial_call=True,
)
def bat_tat_cua_so_eda(open_clicks, _, route, years, continent, country, figures, ids, scope):

    trigger = ctx.triggered_id
    if not isinstance(trigger, dict):
        return "eda-modal", None
    if not any(open_clicks or []):
        return no_update, no_update

    path = trigger["path"]
    artifacts = DUC_TEMPERATURE_ARTIFACTS + QUAN_ARTIFACTS
    title, subtitle, _ = next(item for item in artifacts if item[2] == path)
    if path.endswith(".html"):
        figure = next((figure for figure, graph_id in zip(figures, ids) if graph_id["path"] == path), None)
        if figure is None:
            return no_update, no_update
        media = khung_bieu_do(go.Figure(figure).update_layout(height=None))
        media.style = {"height": "100%", "minHeight": 0}
        media.className = "chart eda-modal-chart"
        title, subtitle = title.replace(" toàn cầu", ""), figure.get("layout", {}).get("meta", {}).get("scope", scope)
    else:
        media = tao_noi_dung_eda(title, subtitle, path, large=True)
    heading = [html.H2(title)]
    if subtitle:
        heading.append(html.P(subtitle))
    return "eda-modal open", [
        html.Div(heading, className="eda-modal-heading"),
        media,
    ]

def lay_giai_doan_trang(route):
    if route == "#temperature":
        return int(TEMPERATURE_DATA.year.min()), int(TEMPERATURE_DATA.year.max())
    if route == "#co2":
        return max(1850, int(GLOBAL_CO2.year.min())), int(GLOBAL_CO2.year.max())
    if route == "#scenario":
        return tuple(MODEL_INFO["source_period"])
    return int(TEMPERATURE_DATA.year.min()), int(GLOBAL_DATA.year.max())


@app.callback(
    Output("year-range", "options"),
    Output("year-range", "value"),
    Output("header-data-range", "children"),
    Output("filter-store", "data"),
    Output("country-filter", "options"),
    Output("country-filter", "value"),
    Output("continent-filter", "value"),
    Output("metric-filter", "value"),
    Input("url", "hash"),
    Input("year-range", "value"),
    Input("continent-filter", "value"),
    Input("country-filter", "value"),
    Input("metric-filter", "value"),
    Input("overview-globe", "clickData", allow_optional=True),
    Input("globe", "clickData", allow_optional=True),
    Input({"type": "eda-chart", "path": ALL}, "clickData"),
    State("filter-store", "data"),
    State({"type": "eda-chart", "path": ALL}, "id"),
)
def cap_nhat_bo_loc(route, years, continent, country, metric, overview_click=None,
                   earth_click=None, eda_clicks=None, saved=None, eda_ids=None):
    route = route if route in {"#" + key for key in PAGE_INFO} else "#overview"
    saved = saved or {}
    choices = dict(saved.get("pages", {}))
    previous = saved.get("page")
    current = dict(years=years, continent=continent, country=country, metric=metric)
    start, end = lay_giai_doan_trang(route)
    year_options = tuy_chon_thap_ky(start, end)
    if previous != route:
        if previous:
            choices[previous] = current
        current = choices.get(route, dict(years=year_options[0]["value"],
                                         continent="all", country="all", metric="temperature")).copy()
    years, continent, country, metric = (current[key] for key in ("years", "continent", "country", "metric"))
    if years not in {option["value"] for option in year_options}:
        years = year_options[0]["value"]
    available = loc_du_lieu(years, temperature=route == "#temperature")[
        ["iso_alpha", "country", "continent"]].drop_duplicates().sort_values("country")
    try:
        trigger = ctx.triggered_id
    except MissingCallbackContextException:
        trigger = None
    if trigger in ("overview-globe", "globe") or isinstance(trigger, dict):
        click = earth_click if trigger == "globe" else overview_click
        if isinstance(trigger, dict):
            click = next((value for graph_id, value in zip(eda_ids or [], eda_clicks or [])
                          if graph_id == trigger and Path(graph_id["path"]).name.startswith("03_")), None)
        selected = lay_quoc_gia_duoc_chon(click, set(available.iso_alpha))
        if not selected or selected == country:
            return (no_update,) * 8
        country = selected
        if continent != "all":
            continent = available.loc[available.iso_alpha.eq(country), "continent"].iloc[0]
    if continent != "all":
        available = available[available.continent.eq(continent)]
    country_options = [{"label": "Tất cả quốc gia", "value": "all"}] + [
        {"label": row.country, "value": row.iso_alpha} for row in available.itertuples()
    ]
    if country not in set(available.iso_alpha):
        country = "all"
    choices[route] = dict(years=years, continent=continent, country=country, metric=metric)
    return (year_options, years, f"{start}–{end}", {"page": route, "pages": choices},
            country_options, country, continent, metric)

@app.callback(
    Output("page-content", "children"),
    Output("page-title", "children"),
    Output("page-subtitle", "children"),
    Output({"type": "nav", "index": ALL}, "className"),
    Output("header-export", "hidden"),
    Output("country-field", "className"),
    Output("metric-filter", "disabled"),
    Output("metric-field", "style"),
    Output("filter-bar", "className"),
    Input("url", "hash"),
    Input("year-range", "value"),
    Input("continent-filter", "value"),
    Input("country-filter", "value"),
    Input("metric-filter", "value"),
    State("overview-globe", "id", allow_optional=True),
    State("globe", "id", allow_optional=True),
)
def hien_thi_trang(route, years, continent, country, metric, overview_id=None, earth_id=None):
    page = (route or "#overview").lstrip("#")
    if page not in PAGE_INFO:
        page = "overview"
    is_map = page in ("overview", "earth")
    scope = ten_pham_vi(continent, country)
    subtitle = ("Toàn cầu · Kiểm tra 2015–2024 · Dự đoán đến 2050" if page == "scenario"
                else f"{scope} · {years.replace('-', '–')}")

    try:
        trigger = ctx.triggered_id
    except MissingCallbackContextException:
        trigger = None

    map_ready = overview_id if page == "overview" else earth_id
    if map_ready and is_map and trigger in {
        "year-range", "continent-filter", "country-filter", "metric-filter"
    }:
        return (no_update, no_update, subtitle, [no_update] * len(MENU)) + (no_update,) * 5

    title = PAGE_INFO[page]
    filterless = page == "scenario"

    country_filter = "all" if is_map else country
    frame = loc_du_lieu(years, continent, country_filter, temperature=page == "temperature")
    use_global = country_filter == "all" and continent == "all"
    series = (chuoi_nhiet_do(frame, years, use_global) if page == "temperature"
              else tong_hop_du_lieu(frame, use_global=use_global, co2_only=page == "co2"))

    invalid_country = is_map and country != "all" and country not in frame.iso_alpha.values
    if page == "scenario":
        content = tao_trang_du_doan()
    elif series.empty or invalid_country:
        content = html.Div([
            html.H2("Chưa có dữ liệu trong phạm vi này"),
            html.P("Nhiệt độ quốc gia: 1961–2025." if page == "temperature" else ""),
        ], className="card empty-state")
    elif page == "overview":
        content = tao_trang_tong_quan(frame, country, scope, metric)
    elif page == "earth":
        content = tao_trang_ban_do(frame, country, metric, scope)
    elif page == "temperature":
        source = "NASA GISTEMP" if scope == "Toàn cầu" else "FAOSTAT"
        if frame.iso_alpha.nunique() > 1 and scope != "Toàn cầu":
            source += " · Trung bình các nước có số liệu"
        year_basis = "Năm lịch" if use_global else "Năm khí tượng (tháng 12–11)"
        notes = [f"{source} · {year_basis} · So với trung bình 1951–1980",
                 f"{source} · Trung bình các năm có số liệu",
                 "FAOSTAT · Trung bình thập kỷ · Năm khí tượng",
                 "FAOSTAT · Trung bình quốc gia–năm", "FAOSTAT · Theo quốc gia–năm",
                 f"{source} · Trung bình từng tháng · So với trung bình 1951–1980"]
        if frame.empty:
            notes[2:5] = ["FAOSTAT · Nhiệt độ theo quốc gia chỉ có từ 1961"] * 3
        content = tao_thu_vien_eda_thanh_vien(DUC_TEMPERATURE_ARTIFACTS, "duc-eda-gallery",
                                            temperature_figures(series, frame, loc_du_lieu_thang(frame, use_global, years)),
                                            notes, scope, years.replace("-", "–"))
    elif page == "co2":
        period = years.replace("-", "–")
        paired = frame.dropna(subset=["co2_per_capita", "renewable_percent"])
        sectors = loc_du_lieu_nganh(frame, scope == "Toàn cầu")
        coverage = sector_coverage_note(sectors)
        if sectors.empty and frame.iso_alpha.isin(["SRB", "MNE"]).any():
            coverage = "EDGAR chỉ có chuỗi Serbia và Montenegro gộp chung; không có số liệu ngành riêng từng nước"
        notes = ["OWID / GCP · Hằng năm",
                 "CO₂ trung bình năm · Tối đa 15 quốc gia",
                 "OWID / GCP · Trung bình thập kỷ",
                 "OWID / GCP · Tổng quốc gia có dữ liệu theo châu lục · Hằng năm",
                 "EDGAR từ 1970 · Tỷ trọng CO₂ trung bình năm · " + coverage,
                 f"{paired.iso_alpha.nunique()} quốc gia · Các năm có đủ hai chỉ số · "
                 "Tái tạo: % tiêu thụ năng lượng cuối cùng · " + renewable_coverage_note(frame)]
        content = tao_thu_vien_eda_thanh_vien(QUAN_ARTIFACTS, "quan-eda-gallery",
                                            co2_figures(series, frame, sectors),
                                            notes, scope, period)
    elif page == "insights":
        content = tao_trang_nhan_dinh(frame, series, scope)
    else:
        content = tao_trang_du_lieu(frame)

    content = html.Div(content, key=page)
    navigation_classes = [
        "nav-item" + (" active" if key == page else "")
        for key, _, _ in MENU
    ]
    country_field_class = "filter-field hidden-filter" if filterless else "filter-field"
    if filterless:
        filter_class = "filter-bar hidden-filter"
    elif is_map:
        filter_class = "filter-bar"
    else:
        filter_class = "filter-bar three-filters"
    return (
        content, title, subtitle,
        navigation_classes,
        filterless,
        country_field_class,
        not is_map,
        {} if is_map else {"display": "none"},
        filter_class,
    )

@app.callback(
    Output("overview-summary", "children"),
    Output("overview-temperature", "figure"),
    Output("overview-co2", "figure"),
    Output("overview-temperature-subtitle", "children"),
    Output("overview-co2-subtitle", "children"),
    Output("overview-globe", "figure"),
    Output("overview-map-selection", "children"),
    Output("overview-year", "min"),
    Output("overview-year", "max"),
    Output("overview-year", "marks"),
    Output("overview-year", "value"),
    Output("overview-year-label", "children"),
    Output("overview-comparison", "children"),
    Input("year-range", "value"),
    Input("continent-filter", "value"),
    Input("country-filter", "value"),
    Input("metric-filter", "value"),
    Input("overview-map-view", "value", allow_optional=True),
    Input("overview-year", "value", allow_optional=True),
    Input("overview-reset", "n_clicks", allow_optional=True),
    State("url", "hash"),
    State("overview-globe", "figure", allow_optional=True),
    prevent_initial_call=True,
)
def cap_nhat_tong_quan(year_range, continent, selected, metric, map_view, year, resets, route, current_figure):
    if route not in (None, "", "#overview") or current_figure is None:
        return (no_update,) * 13
    frame = loc_du_lieu(year_range, continent)
    if frame.empty or (selected != "all" and selected not in frame.iso_alpha.values):
        return (no_update,) * 13

    years = lay_cac_nam_ban_do(frame, selected)
    year = years[-1] if ctx.triggered_id == "year-range" else max(
        years[0], min(year or years[-1], years[-1])
    )
    figure = cap_nhat_ban_do(lay_du_lieu_ban_do(frame, year), selected, metric, map_view, resets,
                        current_figure, reset=ctx.triggered_id == "overview-reset")

    if ctx.triggered_id in ("overview-map-view", "overview-reset", "metric-filter"):
        return (no_update,) * 5 + (figure,) + (no_update,) * 7
    scope = ten_pham_vi(continent, selected)
    summary, temperature, co2, subtitle = tao_chi_tiet_tong_quan(frame, selected, year, scope)
    return (
        summary, temperature, co2, subtitle, subtitle, figure, scope,
        years[0], years[-1], tao_moc_thanh_truot(years), year, str(year),
        tao_so_sanh_tong_quan(frame, selected, year),
    )

@app.callback(
    Output("country-panel", "children"),
    Output("earth-lower", "children"),
    Output("globe", "figure"),
    Input("country-filter", "value"),
    Input("metric-filter", "value"),
    Input("year-range", "value"),
    Input("continent-filter", "value"),
    Input("reset-globe", "n_clicks", allow_optional=True),
    Input("earth-map-view", "value", allow_optional=True),
    State("globe", "figure", allow_optional=True),
    State("url", "hash"),
    prevent_initial_call=True,
)
def cap_nhat_trang_ban_do(selected, metric, years, continent, resets, map_view, current_figure, route):
    if route != "#earth" or current_figure is None:
        return (no_update,) * 3
    frame = loc_du_lieu(years, continent)
    if frame.empty or (selected != "all" and selected not in frame.iso_alpha.values):
        return (no_update,) * 3
    figure = cap_nhat_ban_do(lay_du_lieu_ban_do(frame, int(frame.year.max())), selected, metric, map_view,
                        resets, current_figure, reset=ctx.triggered_id == "reset-globe")
    if ctx.triggered_id in ("earth-map-view", "reset-globe", "metric-filter"):
        return no_update, no_update, figure
    panel, charts = tao_chi_tiet_ban_do(frame, selected, ten_pham_vi(continent, selected))
    return panel, charts, figure


@app.callback(
    Output("scenario-custom-control", "hidden"),
    Output("legend-custom", "hidden"),
    Input("scenario-choice", "value"),
)
def cau_hinh_toc_do_kich_ban(scenario_id):
    return scenario_id != "custom", scenario_id != "custom"


@app.callback(
    Output("scenario-temperature-chart", "figure"),
    Output("scenario-co2-chart", "figure"),
    Output("scenario-temp", "children"),
    Output("scenario-temp-note", "children"),
    Output("scenario-difference", "children"),
    Output("scenario-difference-note", "children"),
    Output("scenario-emissions", "children"),
    Output("scenario-emissions-note", "children"),
    Output("scenario-result-store", "data"),
    Input("scenario-choice", "value"),
    Input("scenario-rate", "value"),
    Input("scenario-year", "value"),
)
def cap_nhat_trang_du_doan(scenario_id, annual_rate, milestone):
    scenarios = SCENARIO_DATA
    if scenario_id == "custom":
        scenarios = pd.concat([scenarios, tao_kich_ban(MODEL_INFO, float(annual_rate or 0) / 100)])
    point = scenarios[(scenarios.scenario_id == scenario_id) & (scenarios.year == milestone)].iloc[0]
    base = scenarios[(scenarios.scenario_id == "trend") & (scenarios.year == milestone)].iloc[0]
    difference = point.temperature_prediction - base.temperature_prediction
    comparison = "Bằng kịch bản tiếp diễn" if abs(difference) < .005 else (
        "Thấp hơn tiếp diễn" if difference < 0 else "Cao hơn tiếp diễn")
    return (
        tao_bieu_do_du_bao_nhiet_do(GLOBAL_DATA, scenarios, scenario_id, milestone),
        tao_bieu_do_kich_ban_co2(scenarios, scenario_id, milestone),
        f"{point.temperature_prediction:+.2f} °C",
        f"{milestone} · Khoảng 90%: {point.lower_90:.2f}–{point.upper_90:.2f} °C · "
        f"Ngoại suy CO₂ {point.extrapolation_ratio:.2f}× mức 2024",
        f"{difference:+.2f} °C" if abs(difference) >= .005 else "0.00 °C",
        comparison,
        f"{point.co2 / 1000:.1f} tỷ tấn",
        f"{milestone} · {point.annual_change_pct:+.2f}%/năm",
        scenarios.to_dict("records"),
    )


@app.callback(
    Output("download-scenarios", "data"),
    Input("download-scenarios-button", "n_clicks"),
    State("scenario-result-store", "data"),
    prevent_initial_call=True,
)
def xuat_kich_ban(clicks, records):
    if not clicks or not records:
        return no_update
    return dcc.send_data_frame(
        pd.DataFrame(records).to_csv,
        "kich-ban-khi-hau-2025-2050.csv",
        index=False,
    )

@app.callback(
    Output("download-data", "data"),
    Input("header-export", "n_clicks"),
    Input("export-data", "n_clicks", allow_optional=True),
    State("year-range", "value"),
    State("continent-filter", "value"),
    State("country-filter", "value"),
    State("url", "hash"),
    prevent_initial_call=True,
)
def xuat_du_lieu(header_clicks, page_clicks, years, continent, country, route=None):
    if not header_clicks and not page_clicks:
        return no_update
    frame = loc_du_lieu(years, continent, country, temperature=route == "#temperature")
    if route == "#temperature" and continent == country == "all":
        frame = chuoi_nhiet_do(frame, years, use_global=True)
    elif route == "#co2" and continent == country == "all":
        start, end = map(int, years.split("-"))
        frame = GLOBAL_CO2[GLOBAL_CO2.year.between(start, end)]
    elif route in ("#overview", "") and continent == country == "all":
        start, end = map(int, years.split("-"))
        frame = GLOBAL_DATA[GLOBAL_DATA.year.between(start, end)]
    return dcc.send_data_frame(
        frame.to_csv,
        "nhiet-do.csv" if route == "#temperature" else "du-lieu-khi-hau.csv",
        index=False,
    )
