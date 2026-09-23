import base64
import os
from pathlib import Path

import pandas as pd

from dash import ALL, Dash, Input, Output, State, ctx, dcc, html, no_update
from dash.exceptions import MissingCallbackContextException
from flask import send_from_directory

from charts import (
    create_co2_chart,
    create_comparison_chart,
    create_forecast_chart,
    create_globe,
    create_ranking_chart,
    create_scatter_chart,
    create_temperature_chart,
)
from climate_data import (
    CONTINENTS,
    COORDINATES,
    COUNTRY_NAMES,
    DATA,
    FORECAST_DATA,
    GLOBAL_DATA,
    HISTORICAL_PREDICTIONS,
    MODEL_METRICS,
    aggregate,
    filter_data,
)

app = Dash(
    __name__,
    assets_folder="assets",
    suppress_callback_exceptions=True,
    title="Climate Lab · HCMUTE",
    update_title=None,
)
server = app.server
ROOT = Path(__file__).resolve().parent
EDA_ROOT = ROOT / "eda"


@server.get("/eda-files/<path:filename>")
def serve_eda_file(filename):
    """Phục vụ đúng các sản phẩm EDA đã bàn giao, không sao chép sang assets/."""
    return send_from_directory(EDA_ROOT, filename)


DUC_TEMPERATURE_ARTIFACTS = [
    ("Xu hướng nhiệt độ toàn cầu", "1880–2025",
     "duc/bieu_do_tinh/01_xu_huong_nhiet_do_toan_cau.png"),
    ("Xu hướng nhiệt độ toàn cầu", "1880–2025",
     "duc/bieu_do_tuong_tac/01_xu_huong_nhiet_do_toan_cau.html"),
    ("Nhiệt độ trung bình theo thập kỷ", "",
     "duc/bieu_do_tinh/02_nhiet_do_theo_thap_ky.png"),
    ("Nhiệt độ trung bình theo thập kỷ", "",
     "duc/bieu_do_tuong_tac/02_nhiet_do_theo_thap_ky.html"),
    ("Bản đồ nhiệt độ theo quốc gia", "",
     "duc/bieu_do_tinh/03_ban_do_nhiet_do.png"),
    ("Bản đồ nhiệt độ theo quốc gia", "",
     "duc/bieu_do_tuong_tac/03_ban_do_nhiet_do.html"),
    ("Nhiệt độ theo châu lục và thập kỷ", "",
     "duc/bieu_do_tinh/04_heatmap_chau_luc_thap_ky.png"),
    ("Nhiệt độ theo châu lục và thập kỷ", "",
     "duc/bieu_do_tuong_tac/04_heatmap_chau_luc_thap_ky.html"),
    ("Phân bố nhiệt độ giữa các quốc gia", "Theo thập kỷ",
     "duc/bieu_do_tinh/05_phan_bo_nhiet_do_quoc_gia.png"),
    ("Phân bố nhiệt độ giữa các quốc gia", "Theo thập kỷ",
     "duc/bieu_do_tuong_tac/05_phan_bo_nhiet_do_quoc_gia.html"),
]

DUC_FORECAST_ARTIFACTS = [
    ("Hồi quy tuyến tính theo năm", "",
     "duc/bieu_do_tinh/06_du_bao_hoi_quy_tuyen_tinh.png"),
    ("Hồi quy tuyến tính theo năm", "",
     "duc/bieu_do_tuong_tac/06_du_bao_hoi_quy_tuyen_tinh.html"),
]

QUAN_ARTIFACTS = [
    ("Phát thải CO₂ toàn cầu", "1970–2024",
     "quan/bieu_do_tinh/01_line_co2_toan_cau.png"),
    ("Top 15 quốc gia phát thải", "2023",
     "quan/bieu_do_tinh/02_bar_top15_quoc_gia.png"),
    ("Cơ cấu phát thải theo ngành", "1970–2024",
     "quan/bieu_do_tinh/03_area_co_cau_nganh.png"),
    ("CO₂/người và năng lượng tái tạo", "2023",
     "quan/bieu_do_tinh/04_scatter_co2pc_renewable.png"),
    ("Độ phủ dữ liệu theo năm", "",
     "quan/bieu_do_tinh/05_line_do_phu_du_lieu.png"),
    ("Phát thải CO₂ toàn cầu", "1970–2024",
     "quan/bieu_do_tuong_tac/01_line_co2_toan_cau.html"),
    ("Top 15 quốc gia phát thải", "2023",
     "quan/bieu_do_tuong_tac/02_bar_top15.html"),
    ("CO₂ bình quân đầu người", "2023",
     "quan/bieu_do_tuong_tac/03_choropleth_co2pc.html"),
    ("Cơ cấu phát thải theo ngành", "1970–2024",
     "quan/bieu_do_tuong_tac/04_stacked_area_nganh.html"),
    ("Tỷ trọng phát thải theo ngành", "2024",
     "quan/bieu_do_tuong_tac/05_treemap_nganh.html"),
    ("CO₂/người và năng lượng tái tạo", "2023",
     "quan/bieu_do_tuong_tac/06_scatter_co2pc_renewable.html"),
]

MENU = [
    ("overview", "Tổng quan", "grid"),
    ("earth", "Bản đồ khí hậu", "globe"),
    ("temperature", "Nhiệt độ", "thermometer"),
    ("co2", "Phát thải CO₂", "cloud"),
    ("forecast", "Dự báo", "trend"),
    ("insights", "Nhận định", "bulb"),
    ("data", "Dữ liệu", "database"),
    ("settings", "Cài đặt", "settings"),
]

PAGE_INFO = {
    "overview": (
        "Tổng quan khí hậu",
        "Nhiệt độ và CO₂ theo thời gian, khu vực và quốc gia.",
    ),
    "earth": ("Bản đồ khí hậu", "Dữ liệu theo quốc gia"),
    "temperature": ("Nhiệt độ", "1880–2025 · theo năm, thập kỷ, châu lục"),
    "co2": ("Phát thải CO₂", "1970–2024 · theo quốc gia, ngành"),
    "forecast": ("Dự báo", "Xu hướng đến năm 2050"),
    "insights": ("Nhận định", "Điểm nổi bật trong dữ liệu"),
    "data": ("Dữ liệu", "Bảng dữ liệu và xuất CSV"),
    "settings": ("Cài đặt", "Tùy chỉnh hiển thị"),
    "comparison": ("So sánh quốc gia", "Đối chiếu hai quốc gia"),
    "relationship": ("Tương quan dữ liệu", "Phát thải và nhiệt độ"),
}
MAP_VIEW_OPTIONS = [
    {"label": "Địa cầu", "value": "globe"},
    {"label": "Bản đồ ngang", "value": "flat"},
]
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
    "settings": '<path d="m9 3-1 3-3 1-2 4 2 2v4l4 3 3-1 3 1 4-3v-4l2-2-2-4-3-1-1-3Z"/><circle cx="12" cy="12" r="3"/>',
    "menu": '<path d="M4 6h16M4 12h16M4 18h16"/>',
    "arrow": '<path d="M4 12h16m-6-6 6 6-6 6"/>',
    "calendar": '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M7 3v4M17 3v4M3 10h18M7 14h3M14 14h3"/>',
    "leaf": '<path d="M20 3C8 2 2 8 5 15s14 6 15-12ZM5 21l10-12"/>',
    "reset": '<path d="M3 10a9 9 0 1 1 1 8M3 3v7h7"/>',
    "download": '<path d="M12 3v12m-5-5 5 5 5-5M4 16v5h16v-5"/>',
}

def icon(name, class_name="icon"):
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

def _empty(*children):
    if len(children) == 1 and isinstance(children[0], str):
        children = children[0]
    else:
        children = list(children)
    return html.Div(children, className="card empty-state")

def _select_field(label, dropdown_id, options, value, symbol=None,
                  field_id=None, field_class="filter-field", **dropdown_props):
    text = [icon(symbol), label] if symbol else label
    wrapper = {"className": field_class}
    if field_id is not None:
        wrapper["id"] = field_id
    return html.Div([
        html.Label(text, htmlFor=dropdown_id),
        dcc.Dropdown(options, value, id=dropdown_id, clearable=False, **dropdown_props),
    ], **wrapper)

def _setting_row(title, desc, control_id, options, value):
    copy = [html.H3(title)]
    if desc:
        copy.append(html.P(desc))
    return html.Div([
        html.Div(copy),
        dcc.RadioItems(
            id=control_id, options=options, value=value,
            className="settings-radio", inline=True,
        ),
    ], className="setting-row")

def _stat_row(label, value, tone=None):
    strong = {"className": tone} if tone else {}
    return html.Div([html.Span(label), html.Strong(value, **strong)])

def _rotation_from_keys(view, fallback):
    return {
        axis: view.get(f"geo.projection.rotation.{axis}", fallback.get(axis, 0))
        for axis in ("lon", "lat", "roll")
    }

def create_header():
    logo = html.Img(
        src=app.get_asset_url("hcmute-logo.png"),
        className="school-logo",
        alt="Logo HCMUTE",
    )
    school_name = html.Div([
        html.Span("TRƯỜNG ĐẠI HỌC", className="school-top"),
        html.Strong("CÔNG NGHỆ KỸ THUẬT TP. HỒ CHÍ MINH"),
    ], className="school-name")
    brand = html.A(
        [logo, school_name],
        href="#overview",
        className="school-brand",
        **{"aria-label": "Về trang tổng quan"},
    )
    product_brand = html.Div([
        html.Strong("CLIMATE LAB"),
        html.Span("Phân tích dữ liệu khí hậu"),
    ], className="product-brand")
    identity = html.Div([
        brand,
        html.Span(className="header-divider"),
        product_brand,
    ], className="header-identity")
    data_range = html.Div([
        icon("calendar"),
        html.Div([
            html.Span("Dữ liệu bao phủ"),
            html.Strong(f"{int(DATA.year.min())}–{int(DATA.year.max())}"),
        ]),
    ], className="header-data-range")
    export_button = html.Button(
        [icon("download"), html.Span("Tải CSV")],
        id="header-export",
        className="header-export",
        title="Tải dữ liệu đang lọc",
        n_clicks=0,
    )
    actions = html.Div([data_range, export_button], className="header-actions")
    return html.Header([identity, actions], className="header")

def create_sidebar():
    links = []
    for index, (key, label, symbol) in enumerate(MENU):
        if index == 6:
            links.append(html.Div(className="nav-separator"))
            links.append(html.Div("Hệ thống", className="nav-section"))
        link_class = "nav-item" + (" active" if key == "overview" else "")
        link_content = [
            icon(symbol),
            html.Span(label, className="nav-label"),
        ]
        links.append(html.A(
            link_content,
            href=f"#{key}",
            className=link_class,
            title=label,
            id={"type": "nav", "index": key},
        ))

    sidebar_title = html.Div([
        html.Strong("CLIMATE", className="sidebar-brand"),
        html.Span("DASHBOARD", className="sidebar-caption"),
    ], className="nav-label")
    menu_button = html.Button(
        icon("menu"),
        id="collapse-sidebar",
        className="icon-button",
        title="Thu gọn / mở rộng thanh điều hướng",
        n_clicks=0,
    )
    sidebar_top = html.Div([sidebar_title, menu_button], className="sidebar-top")
    navigation = html.Nav(
        [html.Div("Khám phá dữ liệu", className="nav-section")] + links,
        **{"aria-label": "Điều hướng chính"},
    )
    credit = html.Footer(
        [
            html.Div(
                html.Img(
                    src=app.get_asset_url("shipcode-logo.png"),
                    alt="Logo Team Shipcode",
                    className="sidebar-user-logo",
                ),
                className="sidebar-user-avatar",
            ),
            html.Div([
                html.Span("Phát triển bởi"),
                html.Strong("Nhóm 18"),
                html.Small("TEAM SHIPCODE"),
            ], className="sidebar-user-copy nav-label"),
        ],
        className="sidebar-credit",
    )
    return [sidebar_top, navigation, credit]

def create_filters():
    year_options = [
        {"label": "1970 – 2024", "value": "1970-2024"},
        {"label": "1990 – 2023", "value": "1990-2023"},
        {"label": "2000 – 2024", "value": "2000-2024"},
        {"label": "2015 – 2024", "value": "2015-2024"},
    ]
    continent_options = [
        {"label": "Tất cả châu lục", "value": "all"},
        *[{"label": name, "value": name} for name in CONTINENTS],
    ]
    country_options = [
        {"label": "Toàn cầu", "value": "all"},
        *[
            {"label": name, "value": iso}
            for iso, name in COUNTRY_NAMES.items()
        ],
    ]
    metric_options = [
        {"label": "Nhiệt độ", "value": "temperature"},
        {"label": "Phát thải CO₂", "value": "co2"},
    ]

    year_filter = _select_field(
        "Khoảng năm", "year-range", year_options, "1970-2024",
        symbol="calendar", field_class="filter-years", searchable=False,
    )
    continent_filter = _select_field(
        "Châu lục", "continent-filter", continent_options, "all",
        field_class="filter-field hidden-filter",
    )
    country_filter = _select_field(
        "Quốc gia", "country-filter", country_options, "all",
        symbol="globe", field_id="country-field", placeholder="Tìm quốc gia…",
    )
    metric_filter = _select_field(
        "Chỉ số", "metric-filter", metric_options, "temperature",
        symbol="chart", field_id="metric-field", searchable=False,
    )

    return html.Div(
        [year_filter, continent_filter, country_filter, metric_filter],
        id="filter-bar",
        className="filter-bar",
    )

def graph(figure, graph_id=None, globe=False):
    config = {
        "displayModeBar": False if globe else "hover",
        "displaylogo": False,
        "scrollZoom": False,
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

def create_chart_card(
    title,
    subtitle,
    figure,
    symbol="trend",
    graph_id=None,
):
    heading = html.Div([
        html.Div([icon(symbol), html.H3(title)], className="chart-title"),
        html.P(subtitle),
    ], className="chart-heading")
    header = html.Div(heading, className="card-header")
    return html.Section(
        [header, graph(figure, graph_id)],
        className="card chart-card",
    )


def create_eda_media(title, subtitle, path, large=False):
    source = f"/eda-files/{path}"
    label = title if not subtitle else f"{title} — {subtitle}"
    size = "modal" if large else "artifact"
    if path.endswith(".html"):
        return html.Iframe(
            src=source,
            title=label,
            className=f"eda-{size}-frame",
        )
    return html.Img(
        src=source,
        alt=label,
        className=f"eda-{size}-image",
    )


def create_eda_artifact_card(title, subtitle, path):
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
        create_eda_media(title, subtitle, path),
    ], className="card eda-artifact-card")


def create_member_eda_gallery(artifacts, gallery_id):
    # Tương tác xếp trước để người xem khám phá trước, ảnh tĩnh để sau.
    formats = [
        ("Biểu đồ tương tác", "interactive",
         [item for item in artifacts if item[2].endswith(".html")]),
        ("Biểu đồ tĩnh", "static",
         [item for item in artifacts if not item[2].endswith(".html")]),
    ]
    return html.Section([
        *[
            html.Div([
                html.Div(html.H3(title), className="eda-format-heading"),
                html.Div(
                    [create_eda_artifact_card(*item) for item in items],
                    className=f"eda-artifact-grid {kind}",
                ),
            ], className=f"eda-format-section {kind}")
            for title, kind, items in formats if items
        ],
    ], id=gallery_id, className="eda-gallery")

def create_kpi_card(label, value, unit, note, symbol, tone="blue"):
    value_row = html.Div([
        html.Strong(value, className=tone),
        html.Span(unit),
    ], className="kpi-value")
    content = html.Div([
        html.Div(label, className="kpi-label"),
        value_row,
        html.Div(note, className="kpi-note"),
    ], className="kpi-content")
    return html.Div([
        html.Div(icon(symbol), className=f"kpi-icon {tone}"),
        content,
    ], className="card kpi-card")

def scope_name(continent, country):
    return COUNTRY_NAMES.get(country, "Toàn cầu" if continent == "all" else continent)

def format_number(value, pattern, missing="—"):
    return missing if pd.isna(value) else format(value, pattern)

def slider_marks(years):
    first, last = years[0], years[-1]
    return {
        year: str(year)
        for year in years
        if year in (first, last) or (year % 10 == 0 and last - year >= 7)
    }

def choose_country(frame, requested="all", fallback="VNM"):
    available = set(frame.iso_alpha.unique())
    if requested in available:
        return requested
    if fallback in available:
        return fallback
    return frame.iloc[0].iso_alpha

def country_from_click(click_data, available):
    if not click_data or not click_data.get("points"):
        return None

    point = click_data["points"][0]
    country = point.get("location") or point.get("customdata")
    if isinstance(country, (list, tuple)):
        country = country[0] if country else None
    return country if isinstance(country, str) and country in available else None

def overview_details(frame, selected, year, scope):
    chosen = frame if selected == "all" else frame[frame.iso_alpha == selected]
    series = aggregate(chosen, use_global=selected == "all" and scope == "Toàn cầu")
    available_years = set(series.year.astype(int))
    if year not in available_years:
        year = int(series.year.max())
    row = series[series.year == year].iloc[0]
    period = f"{int(series.year.min())} – {int(series.year.max())}"
    if selected == "all":
        region = f"{chosen.iso_alpha.nunique()} quốc gia"
    else:
        region = chosen.iloc[0].continent
    metrics = [
        ("Độ lệch nhiệt độ", format_number(row.temperature_anomaly, "+.2f"), "°C", "red"),
        ("Tổng phát thải CO₂", format_number(row.co2, ",.1f"), "Mt", "blue"),
        ("CO₂ bình quân", format_number(row.co2_per_capita, ".2f"), "tấn/người", "blue"),
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
    temperature = create_temperature_chart(series, 200)
    co2 = create_co2_chart(series, 200)
    for figure in (temperature, co2):
        figure.add_vline(x=year, line_width=1, line_dash="dot", line_color="#8496AA")
    return summary, temperature, co2, f"{scope} · {period}"

def create_overview(frame, selected, scope, metric):
    years = sorted(int(year) for year in frame.year.unique())
    year = years[-1]
    snapshot = frame[frame.year == year]
    lon, lat = COORDINATES.get(selected, (105, 15))
    globe = create_globe(
        snapshot,
        selected,
        metric,
        rotation={"lon": lon, "lat": lat},
        height=490,
    )
    summary, temperature, co2, subtitle = overview_details(frame, selected, year, scope)

    map_header = html.Div([
        html.Div([
            icon("globe"),
            html.Div([
                html.H3("Bản đồ khí hậu tương tác"),
                html.P("Kéo để xoay · Bấm quốc gia để xem dữ liệu"),
            ]),
        ], className="globe-heading"),
        dcc.RadioItems(
            id="overview-map-view",
            options=MAP_VIEW_OPTIONS,
            value="globe",
            inline=True,
            className="map-view-switch",
        ),
        html.Button(
            icon("reset"),
            id="overview-reset",
            n_clicks=0,
            className="overview-reset",
            title="Đặt lại góc nhìn",
            **{"aria-label": "Đặt lại góc nhìn"},
        ),
    ], className="overview-map-header")
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
            marks=slider_marks(years),
            value=year,
            included=False,
            updatemode="mouseup",
        ),
    ], className="overview-timeline")
    map_card = html.Section([
        map_header,
        selection,
        graph(globe, "overview-globe", globe=True),
        timeline,
    ], className="overview-map-card")
    summary_card = html.Section(
        summary,
        id="overview-summary",
        className="card overview-summary",
        **{"aria-live": "polite", "aria-atomic": "true"},
    )
    temperature_card = create_chart_card(
        "Xu hướng nhiệt độ",
        html.Span(subtitle, id="overview-temperature-subtitle"),
        temperature,
        "thermometer",
        graph_id="overview-temperature",
    )
    co2_card = create_chart_card(
        "Xu hướng phát thải CO₂",
        html.Span(subtitle, id="overview-co2-subtitle"),
        co2,
        "cloud",
        graph_id="overview-co2",
    )
    return html.Div([map_card, summary_card, temperature_card, co2_card], className="overview-grid")

def create_country_panel(frame, selected):
    series = aggregate(frame[frame.iso_alpha == selected])
    latest = series.iloc[-1]
    country_name = COUNTRY_NAMES[selected]
    heading = html.Div([
        html.Span(f"{int(latest.year)}", className="small-meta"),
    ], className="country-eyebrow")
    metrics = html.Div([
        _stat_row("Nhiệt độ", f"{format_number(latest.temperature_anomaly, '+.2f')} °C", "red"),
        _stat_row("Tổng CO₂", f"{format_number(latest.co2, ',.1f')} Mt", "blue"),
        _stat_row("CO₂ / người", f"{format_number(latest.co2_per_capita, '.2f')} tấn"),
    ], className="country-metrics")
    country_card = html.Section(
        [heading, html.H2(country_name), metrics],
        className="card country-card",
    )
    temperature_card = create_chart_card(
        "Biến đổi nhiệt độ",
        f"{country_name} · °C so với trung bình 1951–1980",
        create_temperature_chart(series, 230),
        "thermometer",
    )
    emission_card = create_chart_card(
        "Xu hướng phát thải CO₂",
        f"{country_name} · Mt CO₂",
        create_co2_chart(series, 230),
        "cloud",
    )
    return [country_card, temperature_card, emission_card]

def create_earth_lower(frame, selected):
    year = frame.year.max()
    snapshot = frame[frame.year == year]
    row = snapshot[snapshot.iso_alpha == selected].iloc[0]
    scatter_card = create_chart_card(
        "CO₂ và nhiệt độ",
        f"{len(snapshot)} quốc gia · {year}",
        create_scatter_chart(snapshot, selected, 310),
        "scatter",
    )
    ranking_card = create_chart_card(
        "Quốc gia phát thải nhiều nhất",
        f"Top 10 năm {year}",
        create_ranking_chart(snapshot, selected, limit=10, height=310),
        "compare",
    )
    charts = html.Div([scatter_card, ranking_card], className="chart-grid")

    co2_total = snapshot.co2.sum(min_count=1)
    co2_share = row.co2 / co2_total * 100 if pd.notna(row.co2) and co2_total else float("nan")
    summary = html.Section([
        html.Div([
            html.P(f"{row.continent} · {year}", className="small-meta"),
        ]),
        _stat_row(
            "Dân số",
            "—" if pd.isna(row.population) else f"{row.population / 1e6:,.1f} triệu",
        ),
        _stat_row(
            "Năng lượng tái tạo",
            "—" if pd.isna(row.renewable_percent) else f"{row.renewable_percent:.1f}%",
            "green",
        ),
        _stat_row(
            "Tỷ trọng CO₂",
            "—" if pd.isna(co2_share) else f"{co2_share:.1f}%",
        ),
    ], className="card country-summary")
    return [charts, summary]

def create_earth(frame, selected, metric):
    selected = choose_country(frame, selected)
    layer = "co2" if metric == "co2" else "temperature"
    year = int(frame.year.max())
    snapshot = frame[frame.year == year]
    lon, lat = COORDINATES.get(selected, (105, 15))
    figure = create_globe(
        snapshot,
        selected,
        layer,
        rotation={"lon": lon, "lat": lat},
    )

    globe_header = html.Div([
        html.Div([
            icon("globe"),
            html.Div([
                html.H3("Bản đồ khí hậu tương tác"),
            ]),
        ], className="globe-heading"),
        html.Span(str(year), className="globe-year"),
    ], className="globe-header")
    globe_toolbar = html.Div([
        html.Span("CO₂ (triệu tấn)" if layer == "co2" else "Độ lệch nhiệt độ (°C)"),
        dcc.RadioItems(
            id="earth-map-view",
            options=MAP_VIEW_OPTIONS,
            value="globe",
            inline=True,
            className="map-view-switch",
        ),
        html.Button(
            [icon("reset"), "Đặt lại"],
            id="reset-globe",
            n_clicks=0,
            className="globe-reset",
        ),
    ], className="globe-toolbar")
    globe_card = html.Section([
        globe_header,
        globe_toolbar,
        graph(figure, "globe", globe=True),
    ], className="globe-card")
    country_panel = html.Div(
        create_country_panel(frame, selected),
        id="country-panel",
        className="country-panel",
        **{"aria-live": "polite"},
    )

    return [
        html.Div([globe_card, country_panel], className="earth-grid"),
        html.Div(create_earth_lower(frame, selected), id="earth-lower"),
    ]

def create_temperature_page():
    return [
        create_member_eda_gallery(
            DUC_TEMPERATURE_ARTIFACTS,
            "duc-eda-gallery",
        ),
    ]


def create_co2_page():
    return [
        create_member_eda_gallery(
            QUAN_ARTIFACTS,
            "quan-eda-gallery",
        ),
    ]

def create_comparison_results(frame, country_a, country_b):
    if country_a == country_b:
        return _empty(
            html.H3("Chọn hai quốc gia khác nhau"),
            html.P("Thay quốc gia A hoặc B để bắt đầu so sánh."),
        )

    snapshot = frame[frame.year == frame.year.max()].set_index("iso_alpha")
    indicators = [
        ("Biến đổi nhiệt độ", "temperature_anomaly", "°C"),
        ("Tổng CO₂", "co2", "Mt"),
        ("CO₂ / người", "co2_per_capita", "tấn/người"),
    ]

    table_rows = []
    for label, field, unit in indicators:
        value_a = snapshot.loc[country_a, field]
        value_b = snapshot.loc[country_b, field]
        table_rows.append(html.Tr([
            html.Td(label),
            html.Td(f"{value_a:,.2f} {unit}", className="blue"),
            html.Td(f"{value_b:,.2f} {unit}"),
        ]))

    table_header = html.Tr([
        html.Th(f"Chỉ số · {frame.year.max()}"),
        html.Th(COUNTRY_NAMES[country_a]),
        html.Th(COUNTRY_NAMES[country_b]),
    ])
    table = html.Table([
        html.Thead(table_header),
        html.Tbody(table_rows),
    ], className="data-table comparison-table")

    charts = [
        create_chart_card(
            "Biến đổi nhiệt độ",
            "°C",
            create_comparison_chart(frame, country_a, country_b, "temperature_anomaly"),
            "thermometer",
        ),
        create_chart_card(
            "Phát thải CO₂",
            "Mt CO₂",
            create_comparison_chart(frame, country_a, country_b, "co2"),
            "cloud",
        ),
    ]
    return [
        html.Div(table, className="card table-wrap"),
        html.Div(charts, className="chart-grid"),
    ]

def create_comparison_page(frame):
    available = frame[["iso_alpha", "country"]].drop_duplicates()
    options = [{"label": row.country, "value": row.iso_alpha} for row in available.itertuples()]
    values = available.iso_alpha.tolist()
    if len(values) < 2:
        return _empty(
            html.H3("Cần ít nhất hai quốc gia để so sánh"),
            html.P("Hãy chọn phạm vi có nhiều quốc gia hơn."),
        )

    country_a = "VNM" if "VNM" in values else values[0]
    country_b = "THA" if "THA" in values else next(iso for iso in values if iso != country_a)

    controls = html.Div([
        html.Div([
            html.Label("Quốc gia A", htmlFor="compare-a"),
            dcc.Dropdown(options, country_a, id="compare-a", clearable=False),
        ]),
        html.Span("VS", className="vs-badge"),
        html.Div([
            html.Label("Quốc gia B", htmlFor="compare-b"),
            dcc.Dropdown(options, country_b, id="compare-b", clearable=False),
        ]),
    ], className="card compare-controls")
    results = html.Div(
        create_comparison_results(frame, country_a, country_b),
        id="comparison-results",
    )
    return [controls, results]

def create_relationship_page(frame, selected):
    snapshot = frame[frame.year == frame.year.max()]
    valid = (
        len(snapshot) > 2
        and snapshot.co2_per_capita.nunique() > 1
        and snapshot.temperature_anomaly.nunique() > 1
    )
    correlation = snapshot.co2_per_capita.corr(snapshot.temperature_anomaly) if valid else None
    correlation_text = f"{correlation:.2f}" if valid else "—"
    r_squared_text = f"{correlation ** 2:.2f}" if valid else "—"
    # Chỉ hiện câu hướng dẫn khi không đủ dữ liệu để tính.
    note = None
    if not valid:
        note = html.P(
            "Cần ít nhất 3 quốc gia có giá trị khác nhau để tính tương quan.",
            className="body-copy",
        )

    stats = html.Section([
        html.H2("Hệ số tương quan"),
        html.P(f"{len(snapshot)} quốc gia · Năm {frame.year.max()}", className="small-meta"),
        html.Div([
            html.Div([html.Span("Pearson R"), html.Strong(correlation_text)]),
            html.Div([html.Span("R²"), html.Strong(r_squared_text)]),
        ], className="correlation-values"),
        note,
    ], className="card research-note")
    chart = create_chart_card(
        "CO₂ bình quân và biến đổi nhiệt độ",
        f"Năm {frame.year.max()}",
        create_scatter_chart(snapshot, selected, 420),
        "scatter",
    )
    return html.Div([chart, stats], className="relationship-grid")

def create_forecast_page():
    selected_name = MODEL_METRICS["selected_model"]
    metrics = MODEL_METRICS[selected_name]
    scenario_2050 = FORECAST_DATA[FORECAST_DATA.year == 2050].sort_values(
        "temperature_prediction", ascending=False
    )
    notice = html.Div(
        "Mô phỏng sau 2024 theo giả định phát thải, không phải kịch bản IPCC chính thức.",
        className="demo-notice",
    )
    kpi_specs = [
        ("R² kiểm tra", f"{metrics['r2']:.3f}", "", "2015–2024", "scatter", "blue"),
        ("MAE kiểm tra", f"{metrics['mae']:.3f}", "°C", "2015–2024", "compare", "blue"),
        ("RMSE kiểm tra", f"{metrics['rmse']:.3f}", "°C", "2015–2024", "trend", "blue"),
    ]
    kpis = html.Div([
        create_kpi_card(label, value, unit, note, symbol, tone)
        for label, value, unit, note, symbol, tone in kpi_specs
    ], className="kpi-grid three")
    chart = create_chart_card(
        "Kịch bản nhiệt độ toàn cầu đến 2050",
        "Quan trắc và kịch bản",
        create_forecast_chart(GLOBAL_DATA, FORECAST_DATA, HISTORICAL_PREDICTIONS),
        "trend",
    )
    scenario_rows = [
        html.Tr([
            html.Td(row.scenario),
            html.Td(f"{row.co2:,.0f} Mt"),
            html.Td(f"{row.temperature_prediction:+.2f} °C"),
        ])
        for row in scenario_2050.itertuples()
    ]
    scenario_table = html.Div([
        html.H3("Kết quả năm 2050"),
        html.Table([
            html.Thead(html.Tr([
                html.Th("Giả định"), html.Th("CO₂ năm 2050"),
                html.Th("Nhiệt độ dự báo"),
            ])),
            html.Tbody(scenario_rows),
        ], className="data-table comparison-table"),
    ], className="card table-wrap")
    reference = create_member_eda_gallery(
        DUC_FORECAST_ARTIFACTS,
        "duc-forecast-gallery",
    )
    return [notice, kpis, chart, scenario_table, reference]

def create_insights_page(frame, series, scope, selected):
    first, last = series.iloc[0], series.iloc[-1]
    snapshot = frame[frame.year == last.year]
    temperature_change = last.temperature_anomaly - first.temperature_anomaly
    top_pc = snapshot.sort_values("co2_per_capita", ascending=False).iloc[0] if len(snapshot) else None
    if top_pc is not None and pd.notna(top_pc.co2_per_capita):
        top_text = f"{top_pc.country} cao nhất: {top_pc.co2_per_capita:.2f} tấn/người ({int(last.year)})."
    else:
        top_text = f"Số liệu năm {int(last.year)}."
    valid = (
        len(snapshot) > 2
        and snapshot.co2_per_capita.nunique() > 1
        and snapshot.temperature_anomaly.nunique() > 1
    )
    corr = snapshot.co2_per_capita.corr(snapshot.temperature_anomaly) if valid else None
    corr_text = f"R = {corr:.2f} trên {len(snapshot)} quốc gia ({int(last.year)})." if corr is not None and pd.notna(corr) else f"{len(snapshot)} quốc gia ({int(last.year)})."
    stories = [
        (
            "Nhiệt độ qua thời gian",
            f"{scope}: {temperature_change:+.2f} °C từ {int(first.year)} đến {int(last.year)}.",
            create_temperature_chart(series, 200),
            "red",
        ),
        (
            "Quy mô phát thải",
            f"Tổng CO₂ năm {int(last.year)}: {last.co2:,.1f} Mt.",
            create_co2_chart(series, 200),
            "blue",
        ),
        (
            "CO₂ bình quân cao nhất",
            top_text,
            create_ranking_chart(snapshot, selected, "co2_per_capita", 5, 200),
            "green",
        ),
        (
            "CO₂ và nhiệt độ",
            corr_text,
            create_scatter_chart(snapshot, selected, 240, compact=True),
            "blue",
        ),
    ]

    articles = []
    for title, text, figure, tone in stories:
        story_text = html.Div([
            html.H2(title),
            html.P(text),
        ], className="story-copy")
        articles.append(html.Article(
            [story_text, graph(figure)],
            className="card story-card",
        ))

    return [html.Div(articles, className="stories")]

def format_table_value(row, key):
    decimal_columns = {
        "temperature_anomaly",
        "co2",
        "co2_per_capita",
        "renewable_percent",
    }
    value = getattr(row, key)
    if pd.isna(value):
        return "—"
    if key in decimal_columns:
        return f"{value:,.2f}"
    if key == "population":
        return f"{value:,.0f}"
    return str(value)

def create_data_page(frame):
    columns = [
        ("country", "Quốc gia"),
        ("iso_alpha", "ISO"),
        ("continent", "Châu lục"),
        ("year", "Năm"),
        ("temperature_anomaly", "Nhiệt độ (°C)"),
        ("co2", "CO₂ (Mt)"),
        ("co2_per_capita", "CO₂/người (tấn)"),
        ("population", "Dân số (người)"),
        ("renewable_percent", "Tái tạo (%)"),
    ]
    ordered = frame.sort_values(["year", "country"], ascending=[False, True])
    visible = ordered.head(500)
    table_rows = [
        html.Tr([html.Td(format_table_value(row, key)) for key, _ in columns])
        for row in visible.itertuples()
    ]

    table = html.Table([
        html.Thead(html.Tr([html.Th(label) for _, label in columns])),
        html.Tbody(table_rows),
    ], className="data-table")

    record_count = (
        f"{len(frame)} bản ghi · {frame.iso_alpha.nunique()} quốc gia · "
        f"{frame.year.nunique()} mốc năm"
    )
    heading = html.Div([
        html.Div([
            html.Span(record_count, className="small-meta"),
        ]),
        html.Button(
            [icon("download"), "Tải CSV đang lọc"],
            id="export-data",
            n_clicks=0,
            className="button",
        ),
    ], className="section-heading")
    notice = html.Div(
        f"Hiển thị {len(visible):,}/{len(ordered):,} dòng gần nhất. Tải CSV để lấy toàn bộ.",
        className="demo-notice",
    )
    source = html.Div(
        "Nguồn: NASA GISTEMP, FAOSTAT, OWID/GCP, EDGAR và UN Statistics.",
        className="card data-note",
    )
    return [
        heading,
        notice,
        html.Div(table, className="card table-wrap scroll-table"),
        source,
    ]

def create_settings_page(preferences):
    heading = html.Div([
        html.H2("Hiển thị"),
    ])
    density_options = [
        {"label": "Thoáng", "value": "comfortable"},
        {"label": "Gọn", "value": "compact"},
    ]
    density = _setting_row(
        "Mật độ giao diện",
        "",
        "setting-density", density_options, preferences.get("density", "comfortable"),
    )
    grid_options = [
        {"label": "Hiển thị", "value": "show"},
        {"label": "Ẩn", "value": "hide"},
    ]
    grid = _setting_row(
        "Đường lưới biểu đồ",
        "",
        "setting-grid", grid_options, preferences.get("grid", "show"),
    )
    return html.Div([heading, density, grid], className="card settings-card")

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
    type="circle",
    color="#0878BE",
    delay_show=250,
    overlay_style={"visibility": "visible", "opacity": .6},
)

main_content = html.Main([
    html.Div([
        page_heading,
        create_filters(),
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
    dcc.Store(id="selected-country", data="VNM"),
    dcc.Store(
        id="preferences",
        storage_type="local",
        data={"density": "comfortable", "grid": "show"},
    ),
    dcc.Download(id="download-data"),
    create_header(),
    html.Aside(create_sidebar(), id="sidebar", className="sidebar"),
    main_content,
    eda_modal,
], id="app-shell", className="app-shell")

@app.callback(
    Output("app-shell", "className"),
    Input("collapse-sidebar", "n_clicks"),
    Input("preferences", "data"),
)
def update_display(clicks, preferences):
    preferences = preferences or {}
    classes = ["app-shell"]
    if clicks and clicks % 2:
        classes.append("collapsed")
    if preferences.get("density") == "compact":
        classes.append("compact")
    if preferences.get("grid") == "hide":
        classes.append("hide-grid")
    return " ".join(classes)

@app.callback(
    Output("eda-modal", "className"),
    Output("eda-modal-content", "children"),
    Input({"type": "expand-eda", "path": ALL}, "n_clicks"),
    Input("close-eda-modal", "n_clicks"),
    prevent_initial_call=True,
)
def toggle_eda_modal(open_clicks, _):
    # Bấm "Mở rộng" thì mở popup với đúng biểu đồ đó, bấm × thì đóng.
    trigger = ctx.triggered_id
    if trigger == "close-eda-modal":
        return "eda-modal", None
    if not isinstance(trigger, dict) or not any(open_clicks or []):
        return no_update, no_update

    path = trigger["path"]
    artifacts = DUC_TEMPERATURE_ARTIFACTS + DUC_FORECAST_ARTIFACTS + QUAN_ARTIFACTS
    title, subtitle, _ = next(item for item in artifacts if item[2] == path)
    heading = [html.H2(title)]
    if subtitle:
        heading.append(html.P(subtitle))
    return "eda-modal open", [
        html.Div(heading, className="eda-modal-heading"),
        create_eda_media(title, subtitle, path, large=True),
    ]

@app.callback(
    Output("country-filter", "options"),
    Output("country-filter", "value"),
    Input("continent-filter", "value"),
    State("country-filter", "value"),
)
def update_country_options(continent, selected):
    available = filter_data(continent=continent)[["iso_alpha", "country"]].drop_duplicates()
    options = [{"label": "Toàn cầu", "value": "all"}] + [
        {"label": row.country, "value": row.iso_alpha}
        for row in available.itertuples()
    ]
    return options, selected if selected in available.iso_alpha.values else "all"

@app.callback(
    Output("page-content", "children"),
    Output("page-title", "children"),
    Output("page-subtitle", "children"),
    Output({"type": "nav", "index": ALL}, "className"),
    Output("country-filter", "disabled"),
    Output("country-field", "className"),
    Output("metric-filter", "disabled"),
    Output("metric-field", "style"),
    Output("filter-bar", "className"),
    Input("url", "hash"),
    Input("year-range", "value"),
    Input("continent-filter", "value"),
    Input("country-filter", "value"),
    Input("metric-filter", "value"),
    State("preferences", "data"),
    State("selected-country", "data"),
)
def render_page(route, years, continent, country, metric, preferences=None, previous_country="VNM"):
    page = (route or "#overview").lstrip("#")
    if page not in PAGE_INFO:
        page = "overview"

    try:
        trigger = ctx.triggered_id
    except MissingCallbackContextException:
        trigger = None

    if page == "overview" and trigger in {
        "year-range", "continent-filter", "country-filter", "metric-filter"
    }:
        return (
            no_update,
            no_update,
            no_update,
            [no_update] * len(MENU),
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
        )

    title, subtitle = PAGE_INFO[page]
    filterless = page in ("temperature", "co2", "forecast", "settings")

    pages_with_all_countries = {"overview", "earth", "comparison", "relationship", "forecast"}
    country_filter = "all" if page in pages_with_all_countries else country
    frame = filter_data(years, continent, country_filter)
    series = aggregate(
        frame,
        use_global=country_filter == "all" and continent == "all",
    )
    scope = scope_name(continent, country)

    invalid_overview_country = (
        page == "overview"
        and country != "all"
        and country not in frame.iso_alpha.values
    )
    if page == "temperature":
        content = create_temperature_page()
    elif page == "co2":
        content = create_co2_page()
    elif page == "forecast":
        content = create_forecast_page()
    elif page == "settings":
        content = create_settings_page(preferences or {})
    elif frame.empty or invalid_overview_country:
        content = _empty(
            html.H2("Chưa có dữ liệu trong phạm vi này"),
            html.P("Chọn quốc gia hoặc khoảng năm khác trong bộ lọc phía trên."),
        )
    elif page == "overview":
        content = create_overview(frame, country, scope, metric)
    elif page == "earth":
        content = create_earth(frame, country if country != "all" else previous_country, metric)
    elif page == "comparison":
        content = create_comparison_page(frame)
    elif page == "relationship":
        content = create_relationship_page(frame, country)
    elif page == "insights":
        content = create_insights_page(frame, series, scope, country)
    else:
        content = create_data_page(frame)

    content = html.Div(content, key=page)
    navigation_classes = [
        "nav-item" + (" active" if key == page else "")
        for key, _, _ in MENU
    ]
    country_field_class = (
        "filter-field hidden-filter"
        if filterless or page == "comparison" else "filter-field"
    )
    if filterless:
        filter_class = "filter-bar hidden-filter"
    elif page == "comparison":
        filter_class = "filter-bar one-filter"
    elif page in ("overview", "earth"):
        filter_class = "filter-bar"
    else:
        filter_class = "filter-bar two-filters"
    return (
        content, title, subtitle,
        navigation_classes,
        filterless or page == "comparison",
        country_field_class,
        page not in ("overview", "earth"),
        {} if page in ("overview", "earth") else {"display": "none"},
        filter_class,
    )

@app.callback(
    Output("country-filter", "value", allow_duplicate=True),
    Input("overview-globe", "clickData"),
    State("continent-filter", "value"),
    State("country-filter", "value"),
    prevent_initial_call=True,
)
def select_overview_country(click, continent, current_country):
    available = set(filter_data(continent=continent).iso_alpha)
    selected = country_from_click(click, available)
    return selected if selected and selected != current_country else no_update

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
    Input("year-range", "value"),
    Input("continent-filter", "value"),
    Input("country-filter", "value"),
    Input("metric-filter", "value"),
    Input("overview-map-view", "value", allow_optional=True),
    Input("overview-year", "value", allow_optional=True),
    Input("overview-reset", "n_clicks", allow_optional=True),
    State("url", "hash"),
    State("overview-globe", "figure", allow_optional=True),
    State("overview-globe", "relayoutData", allow_optional=True),
    prevent_initial_call=True,
)
def update_overview(
    year_range,
    continent,
    selected,
    metric,
    map_view,
    year,
    resets,
    route,
    current_figure,
    view,
):
    if route not in (None, "", "#overview") or current_figure is None:
        return (no_update,) * 12
    frame = filter_data(year_range, continent)
    if frame.empty or (selected != "all" and selected not in frame.iso_alpha.values):
        return (no_update,) * 12

    years = sorted(int(value) for value in frame.year.unique())
    year = max(years[0], min(year or years[-1], years[-1]))
    scope = scope_name(continent, selected)
    summary, temperature, co2, subtitle = overview_details(frame, selected, year, scope)

    projection = current_figure["layout"]["geo"]["projection"]
    rotation = projection["rotation"]
    if view:
        rotation = view.get("geo.projection.rotation", rotation)
        if "geo.projection.rotation.lon" in view:
            rotation = _rotation_from_keys(view, rotation)
    if ctx.triggered_id in ("country-filter", "overview-reset"):
        lon, lat = COORDINATES.get(selected, (105, 15))
        rotation = {"lon": lon, "lat": lat}
    figure = create_globe(
        frame[frame.year == year], selected, metric,
        reset=f"{selected}-{resets or 0}", rotation=rotation, height=490,
        view_mode=map_view or "globe",
    )
    return (
        summary, temperature, co2, subtitle, subtitle, figure, scope,
        years[0], years[-1], slider_marks(years), year, str(year),
    )

@app.callback(
    Output("country-panel", "children"),
    Output("earth-lower", "children"),
    Output("globe", "figure"),
    Output("selected-country", "data"),
    Input("globe", "clickData"),
    Input("reset-globe", "n_clicks"),
    Input("earth-map-view", "value", allow_optional=True),
    State("metric-filter", "value"),
    State("year-range", "value"),
    State("continent-filter", "value"),
    State("country-filter", "value"),
    State("selected-country", "data"),
    State("globe", "relayoutData"),
    State("globe", "figure"),
    prevent_initial_call=True,
)
def update_selected_country(
    click, resets, map_view, metric, years, continent, country,
    selected, view, current_figure,
):
    frame = filter_data(years, continent)
    available = set(frame.iso_alpha.unique())
    default = choose_country(frame, country)
    shown = (current_figure or {}).get("layout", {}).get("meta", {}).get("selected")
    selected = shown if shown in available else selected
    if selected not in available:
        selected = default

    if ctx.triggered_id == "reset-globe":
        selected = default
    elif ctx.triggered_id == "globe" and click:
        clicked_country = country_from_click(click, available)
        if clicked_country:
            selected = clicked_country

    rotation = None
    if view and ctx.triggered_id != "reset-globe":
        rotation = view.get("geo.projection.rotation")
        if rotation is None and "geo.projection.rotation.lon" in view:
            rotation = _rotation_from_keys(view, {})
    if rotation is None:
        if ctx.triggered_id == "reset-globe":
            lon, lat = COORDINATES.get(default, (105, 15))
            rotation = {"lon": lon, "lat": lat}
        else:
            rotation = current_figure["layout"]["geo"]["projection"]["rotation"]
    figure = create_globe(
        frame[frame.year == frame.year.max()],
        selected,
        metric,
        resets,
        rotation,
        view_mode=map_view or "globe",
    )
    return (
        create_country_panel(frame, selected),
        create_earth_lower(frame, selected),
        figure,
        selected,
    )

@app.callback(
    Output("comparison-results", "children"),
    Input("compare-a", "value"),
    Input("compare-b", "value"),
    State("year-range", "value"),
    State("continent-filter", "value"),
)
def update_comparison(country_a, country_b, years, continent):
    return create_comparison_results(filter_data(years, continent), country_a, country_b)

@app.callback(
    Output("download-data", "data"),
    Input("header-export", "n_clicks"),
    Input("export-data", "n_clicks", allow_optional=True),
    State("year-range", "value"),
    State("continent-filter", "value"),
    State("country-filter", "value"),
    prevent_initial_call=True,
)
def export_data(header_clicks, page_clicks, years, continent, country):
    if not header_clicks and not page_clicks:
        return no_update
    return dcc.send_data_frame(
        filter_data(years, continent, country).to_csv,
        "du-lieu-khi-hau.csv",
        index=False,
    )

@app.callback(
    Output("preferences", "data"),
    Input("setting-density", "value", allow_optional=True),
    Input("setting-grid", "value", allow_optional=True),
    prevent_initial_call=True,
)
def save_preferences(density, grid):
    if density is None or grid is None:
        return no_update
    return {"density": density, "grid": grid}

if __name__ == "__main__":
    app.run(debug=False, host="127.0.0.1", port=int(os.environ.get("PORT", 8050)))
