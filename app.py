"""Ứng dụng dashboard khí hậu viết bằng Dash."""
import base64
import os

from dash import ALL, Dash, Input, Output, State, ctx, dcc, html, no_update
from dash.exceptions import MissingCallbackContextException

from charts import (
    create_box_chart,
    create_co2_chart,
    create_comparison_chart,
    create_composition_chart,
    create_decade_chart,
    create_forecast_chart,
    create_globe,
    create_heatmap,
    create_ranking_chart,
    create_scatter_chart,
    create_temperature_chart,
)
from mock_data import (
    CONTINENTS,
    COORDINATES,
    COUNTRY_NAMES,
    aggregate,
    filter_data,
)

app = Dash(
    __name__,
    assets_folder="tainguyen",
    suppress_callback_exceptions=True,
    title="Climate Lab · HCMUTE",
    update_title=None,
)
server = app.server

MENU = [
    ("overview", "Tổng quan", "grid"),
    ("earth", "Bản đồ khí hậu", "globe"),
    ("temperature", "Nhiệt độ", "thermometer"),
    ("co2", "Khí thải CO₂", "cloud"),
    ("forecast", "Dự báo", "trend"),
    ("insights", "Nhận định", "bulb"),
    ("data", "Dữ liệu", "database"),
    ("settings", "Cài đặt", "settings"),
]

PAGE_INFO = {
    "overview": (
        "Tổng quan khí hậu",
        "Theo dõi nhiệt độ và phát thải CO₂ theo thời gian, khu vực và quốc gia.",
    ),
    "earth": ("Bản đồ khí hậu", "Khám phá dữ liệu theo quốc gia"),
    "temperature": ("Nhiệt độ", "Xu hướng nhiệt độ theo thời gian và khu vực"),
    "co2": ("Khí thải CO₂", "Phát thải tổng và bình quân đầu người"),
    "forecast": ("Dự báo", "Kịch bản xu hướng cho các giai đoạn tiếp theo"),
    "insights": ("Nhận định", "Các tín hiệu đáng chú ý trong dữ liệu"),
    "data": ("Dữ liệu", "Bảng dữ liệu và công cụ xuất tệp"),
    "settings": ("Cài đặt", "Tùy chỉnh trải nghiệm dashboard"),
    "comparison": ("So sánh quốc gia", "Đối chiếu hai quốc gia trên cùng thước đo"),
    "relationship": ("Tương quan dữ liệu", "Mối liên hệ giữa phát thải và nhiệt độ"),
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
            html.Strong("1960–2020"),
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
                    src=app.get_asset_url("shipcode logo sáng.png"),
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
        {"label": "1960 – 2020", "value": "1960-2020"},
        {"label": "1980 – 2020", "value": "1980-2020"},
        {"label": "2000 – 2020", "value": "2000-2020"},
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
        {"label": "Khí thải CO₂", "value": "co2"},
    ]

    year_filter = html.Div([
        html.Label([icon("calendar"), "Khoảng năm"], htmlFor="year-range"),
        dcc.Dropdown(
            year_options,
            "1960-2020",
            id="year-range",
            clearable=False,
            searchable=False,
        ),
    ], className="filter-years")
    continent_filter = html.Div([
        html.Label("Châu lục", htmlFor="continent-filter"),
        dcc.Dropdown(
            continent_options,
            "all",
            id="continent-filter",
            clearable=False,
        ),
    ], className="filter-field hidden-filter")
    country_filter = html.Div([
        html.Label(
            [icon("globe"), "Phạm vi / Quốc gia"],
            htmlFor="country-filter",
        ),
        dcc.Dropdown(
            country_options,
            "all",
            id="country-filter",
            clearable=False,
            placeholder="Tìm quốc gia…",
        ),
    ], id="country-field", className="filter-field")
    metric_filter = html.Div([
        html.Label(
            [icon("chart"), "Chỉ số hiển thị"],
            htmlFor="metric-filter",
        ),
        dcc.Dropdown(
            metric_options,
            "temperature",
            id="metric-filter",
            clearable=False,
            searchable=False,
        ),
    ], id="metric-field", className="filter-field")

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
            "filename": "climate-lab-demo",
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


def choose_country(frame, requested="all", fallback="VNM"):
    """Chọn một mã quốc gia chắc chắn có trong dữ liệu đang lọc."""
    available = set(frame.iso_alpha.unique())
    if requested in available:
        return requested
    if fallback in available:
        return fallback
    return frame.iloc[0].iso_alpha


def country_from_click(click_data, available):
    """Lấy mã quốc gia từ sự kiện bấm trên bản đồ."""
    if not click_data or not click_data.get("points"):
        return None

    point = click_data["points"][0]
    country = point.get("location") or point.get("customdata")
    return country if isinstance(country, str) and country in available else None


def overview_details(frame, selected, year, scope):
    """Tính chỉ số và hai biểu đồ từ cùng một phạm vi dữ liệu."""
    chosen = frame if selected == "all" else frame[frame.iso_alpha == selected]
    series = aggregate(chosen)
    row = series[series.year == year].iloc[0]
    period = f"{int(series.year.min())} – {int(series.year.max())}"
    if selected == "all":
        region = f"{chosen.iso_alpha.nunique()} quốc gia trong mẫu"
    else:
        region = chosen.iloc[0].continent
    metrics = [
        ("Độ lệch nhiệt độ", f"{row.temperature_anomaly:+.2f}", "°C", "red"),
        ("Tổng phát thải CO₂", f"{row.co2:,.1f}", "Mt", "blue"),
        ("CO₂ bình quân", f"{row.co2_per_capita:.2f}", "tấn/người", "blue"),
    ]
    summary = [
        html.Div([
            html.Div([
                html.Span("ĐANG XEM", className="selection-eyebrow"),
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
    # Giữ nguyên toàn bộ xu hướng; đường dọc chỉ mốc năm đang xem trên bản đồ.
    for figure in (temperature, co2):
        figure.add_vline(x=year, line_width=1, line_dash="dot", line_color="#8496AA")
    return summary, temperature, co2, f"{scope} · {period}"


def create_overview(frame, selected, scope, metric):
    """Địa cầu là điểm nhấn, bên cạnh là số liệu và hai xu hướng chính."""
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
        html.Span("Dữ liệu mô phỏng", className="overview-demo-label"),
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
            step=None,
            marks={value: str(value) for value in years},
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
        html.P("Vùng có màu: có dữ liệu · Mt = triệu tấn", className="overview-map-note"),
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
        html.Span("VỊ TRÍ ĐANG CHỌN", className="eyebrow"),
        html.Span(f"{int(latest.year)} · Mô phỏng", className="small-meta"),
    ], className="country-eyebrow")
    metrics = html.Div([
        html.Div([
            html.Span("Nhiệt độ"),
            html.Strong(f"{latest.temperature_anomaly:+.2f} °C", className="red"),
        ]),
        html.Div([
            html.Span("Tổng CO₂"),
            html.Strong(f"{latest.co2:,.1f} Mt", className="blue"),
        ]),
        html.Div([
            html.Span("CO₂ / người"),
            html.Strong(f"{latest.co2_per_capita:.2f} tấn"),
        ]),
    ], className="country-metrics")
    country_card = html.Section(
        [heading, html.H2(country_name), metrics],
        className="card country-card",
    )
    temperature_card = create_chart_card(
        "Biến đổi nhiệt độ",
        f"{country_name} · °C so với mốc mô phỏng",
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
        f"Các quốc gia trong mẫu · {year}",
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

    co2_share = row.co2 / snapshot.co2.sum() * 100
    summary = html.Section([
        html.Div([
            html.Div("HỒ SƠ QUỐC GIA", className="eyebrow"),
            html.H2(row.country),
            html.P(f"{row.continent} · {year} · Dữ liệu giả định"),
        ]),
        html.Div([
            html.Span("Dân số mô phỏng"),
            html.Strong(f"{row.population / 1e6:,.1f} triệu"),
        ]),
        html.Div([
            html.Span("Năng lượng tái tạo"),
            html.Strong(f"{row.renewable_percent:.1f}%", className="green"),
        ]),
        html.Div([
            html.Span("Tỷ trọng CO₂ trong mẫu"),
            html.Strong(f"{co2_share:.1f}%"),
        ]),
    ], className="card country-summary")
    return [charts, summary]


def create_earth(frame, selected, metric):
    selected = choose_country(frame, selected)
    layer = "co2" if metric == "co2" else "temperature"
    year = int(frame.year.max())
    snapshot = frame[frame.year == year]
    lon, lat = COORDINATES[selected]
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
                html.P(f"{snapshot.iso_alpha.nunique()} quốc gia có dữ liệu"),
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
    globe_footer = html.Div([
        html.Span("BẢN ĐỒ TƯƠNG TÁC", className="globe-caption"),
        html.Span("● Quốc gia đang chọn", className="globe-selected-key"),
    ], className="globe-footer")
    globe_card = html.Section([
        globe_header,
        globe_toolbar,
        graph(figure, "globe", globe=True),
        globe_footer,
    ], className="globe-card")
    country_panel = html.Div(
        create_country_panel(frame, selected),
        id="country-panel",
        className="country-panel",
        **{"aria-live": "polite"},
    )

    return [
        html.Div([
            html.H2("Bản đồ khí hậu theo quốc gia"),
            html.Span("Kéo để xoay, bấm vào quốc gia để xem chi tiết"),
        ], className="section-heading"),
        html.Div([globe_card, country_panel], className="earth-grid"),
        html.Div(create_earth_lower(frame, selected), id="earth-lower"),
    ]


def create_temperature_page(frame, series, scope):
    first, last = series.iloc[0], series.iloc[-1]
    change = last.temperature_anomaly - first.temperature_anomaly
    kpis = [
        create_kpi_card(
            "Biến đổi nhiệt độ hiện tại",
            f"{last.temperature_anomaly:+.2f}",
            "°C",
            f"{scope} · Mô phỏng",
            "thermometer",
            "red",
        ),
        create_kpi_card(
            "Thay đổi từ đầu giai đoạn",
            f"{change:+.2f}",
            "°C",
            f"So với mốc {int(first.year)} trong mẫu",
            "trend",
            "red",
        ),
        create_kpi_card(
            "Thập kỷ đang xem",
            str(int(last.year)),
            "s",
            "Một mốc dữ liệu cho mỗi thập kỷ",
            "calendar",
            "navy",
        ),
    ]
    charts = [
        create_chart_card(
            "Nhiệt độ qua các thập kỷ",
            f"{scope} · °C so với mốc tham chiếu",
            create_temperature_chart(series, 280),
            "thermometer",
        ),
        create_chart_card(
            "Nhiệt độ trung bình theo thập kỷ",
            "Trung bình có trọng số dân số",
            create_decade_chart(series),
            "compare",
        ),
        create_chart_card(
            "Phân bố nhiệt độ trong mẫu",
            f"{frame.iso_alpha.nunique()} quốc gia trong phạm vi lọc",
            create_box_chart(frame),
            "scatter",
        ),
        create_chart_card(
            "Châu lục × Thập kỷ",
            "Nhiệt độ trung bình theo khu vực",
            create_heatmap(frame),
            "grid",
        ),
    ]
    return [
        html.Div(kpis, className="kpi-grid three"),
        html.Div(charts, className="chart-grid"),
    ]


def create_co2_page(frame, series, scope, selected):
    first, last = series.iloc[0], series.iloc[-1]
    growth = (last.co2 / first.co2 - 1) * 100
    snapshot = frame[frame.year == last.year]
    kpis = [
        create_kpi_card(
            "Tổng phát thải CO₂",
            f"{last.co2:,.1f}",
            "Mt",
            f"{scope} · Tổng trong mẫu",
            "cloud",
        ),
        create_kpi_card(
            "Phát thải bình quân",
            f"{last.co2_per_capita:.2f}",
            "tấn/người",
            "CO₂ chia cho dân số",
            "leaf",
            "green",
        ),
        create_kpi_card(
            "Tăng trưởng trong giai đoạn",
            f"{growth:+.1f}",
            "%",
            f"Từ {int(first.year)} đến {int(last.year)}",
            "trend",
        ),
    ]
    charts = [
        create_chart_card(
            "Xu hướng phát thải",
            f"{scope} · Mt CO₂",
            create_co2_chart(series, 310),
            "cloud",
        ),
        create_chart_card(
            "Xếp hạng tổng phát thải",
            f"Top 10 năm {int(last.year)}",
            create_ranking_chart(snapshot, selected, limit=10, height=310),
            "compare",
        ),
        create_chart_card(
            "Phát thải theo châu lục",
            "Tỷ trọng CO₂ trong mẫu",
            create_composition_chart(snapshot),
            "grid",
        ),
        create_chart_card(
            "Bình quân đầu người",
            "Đơn vị: tấn/người",
            create_ranking_chart(snapshot, selected, "co2_per_capita", 10, 310),
            "compare",
        ),
    ]
    return [
        html.Div(kpis, className="kpi-grid three"),
        html.Div(charts, className="chart-grid"),
    ]


def create_comparison_results(frame, country_a, country_b):
    if country_a == country_b:
        return html.Div([
            html.H3("Chọn hai quốc gia khác nhau"),
            html.P("Thay quốc gia A hoặc B để bắt đầu so sánh."),
        ], className="card empty-state")

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
            "So sánh biến đổi nhiệt độ",
            "Đối chiếu cùng giai đoạn · °C",
            create_comparison_chart(frame, country_a, country_b, "temperature_anomaly"),
            "thermometer",
        ),
        create_chart_card(
            "So sánh lượng khí thải CO₂",
            "Đối chiếu cùng giai đoạn · Mt CO₂",
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
        return html.Div([
            html.H3("Cần ít nhất hai quốc gia để so sánh"),
            html.P("Hãy chọn phạm vi có nhiều quốc gia hơn."),
        ], className="card empty-state")

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
        html.P("Chọn hai quốc gia để so sánh."),
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
    if valid:
        explanation = (
            "Các hệ số được tính từ dữ liệu đang hiển thị. "
            "Tương quan không thể hiện quan hệ nhân quả."
        )
    else:
        explanation = "Cần ít nhất 3 quốc gia có giá trị khác nhau để tính tương quan."

    stats = html.Section([
        html.Div("ĐỌC BIỂU ĐỒ", className="eyebrow"),
        html.H2("Mối liên hệ trong mẫu"),
        html.P(f"{len(snapshot)} quốc gia · Năm {frame.year.max()}", className="small-meta"),
        html.Div([
            html.Div([html.Span("Pearson R"), html.Strong(correlation_text)]),
            html.Div([html.Span("R²"), html.Strong(r_squared_text)]),
        ], className="correlation-values"),
        html.P(explanation, className="body-copy"),
        html.Div("Các chỉ số dưới đây được tính từ dữ liệu minh họa.", className="demo-notice"),
        html.P(
            "Mỗi điểm là một quốc gia. Màu thể hiện châu lục.",
            className="body-copy",
        ),
    ], className="card research-note")
    chart = create_chart_card(
        "CO₂ bình quân và biến đổi nhiệt độ",
        "So sánh giữa các quốc gia",
        create_scatter_chart(snapshot, selected, 420),
        "scatter",
    )
    return html.Div([chart, stats], className="relationship-grid")


def create_forecast_page(series, scope):
    notice = html.Div(
        "Đường dự báo và các chỉ số chỉ dùng để minh họa giao diện.",
        className="demo-notice",
    )
    kpis = html.Div([
        create_kpi_card("R² minh họa", "0.92", "", "Chưa đánh giá mô hình", "scatter"),
        create_kpi_card("MAE minh họa", "0.08", "°C", "Chưa đánh giá mô hình", "compare"),
        create_kpi_card("RMSE minh họa", "0.11", "°C", "Chưa đánh giá mô hình", "trend"),
    ], className="kpi-grid three")
    chart = create_chart_card(
        "Kịch bản nhiệt độ",
        f"{scope} · Nét liền: lịch sử · Nét đứt: dự báo",
        create_forecast_chart(series),
        "trend",
    )
    note = html.P(
        "Vùng nền nhạt biểu thị 30 năm tiếp theo sau mốc đang chọn.",
        className="body-copy",
    )
    return [notice, kpis, chart, note]


def create_insights_page(frame, series, scope, selected):
    first, last = series.iloc[0], series.iloc[-1]
    snapshot = frame[frame.year == last.year]
    temperature_change = last.temperature_anomaly - first.temperature_anomaly
    stories = [
        (
            "01",
            "Nhiệt độ qua thời gian",
            "XU HƯỚNG NHIỆT ĐỘ",
            f"Trong phạm vi {scope}, mức thay đổi là {temperature_change:+.2f} °C "
            f"từ {int(first.year)} đến {int(last.year)}.",
            create_temperature_chart(series, 200),
            "temperature",
            "red",
        ),
        (
            "02",
            "Quy mô phát thải",
            "PHÁT THẢI CO₂",
            f"Tổng CO₂ đang hiển thị là {last.co2:,.1f} Mt "
            f"tại mốc {int(last.year)}.",
            create_co2_chart(series, 200),
            "co2",
            "blue",
        ),
        (
            "03",
            "Khác biệt giữa các quốc gia",
            "SO SÁNH QUỐC GIA",
            "Tổng phát thải và phát thải bình quân có thể cho thứ hạng khác nhau.",
            create_ranking_chart(snapshot, selected, "co2_per_capita", 5, 200),
            "comparison",
            "green",
        ),
        (
            "04",
            "CO₂ và nhiệt độ",
            "TƯƠNG QUAN DỮ LIỆU",
            "Biểu đồ phân tán cho thấy vị trí của từng quốc gia trong mẫu.",
            create_scatter_chart(snapshot, selected, 240, compact=True),
            "relationship",
            "blue",
        ),
    ]

    articles = []
    for number, title, eyebrow, text, figure, target, tone in stories:
        story_text = html.Div([
            html.Span(number, className=f"story-number {tone}"),
            html.Div(eyebrow, className="eyebrow"),
            html.H2(title),
            html.P(text),
            html.A(
                ["Khám phá dữ liệu", icon("arrow")],
                href="#" + target,
                className="text-link story-link",
            ),
        ], className="story-copy")
        articles.append(html.Article(
            [story_text, graph(figure)],
            className="card story-card",
        ))

    notice = html.Div(
        "Nội dung được tổng hợp từ phạm vi dữ liệu đang chọn.",
        className="demo-notice",
    )
    return [notice, html.Div(articles, className="stories")]


def format_table_value(row, key):
    decimal_columns = {
        "temperature_anomaly",
        "co2",
        "co2_per_capita",
        "renewable_percent",
    }
    value = getattr(row, key)
    if key in decimal_columns:
        return f"{value:,.2f}"
    if key == "population":
        return f"{value:,}"
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
    table_rows = []
    for row in ordered.itertuples():
        cells = [html.Td(format_table_value(row, key)) for key, _ in columns]
        table_rows.append(html.Tr(cells))

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
            html.H2("Bộ dữ liệu mô phỏng"),
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
        "Dữ liệu cố định dùng để kiểm thử giao diện, không phải số liệu quan trắc.",
        className="demo-notice",
    )
    guide = html.Div([
        html.H3("Cách đọc dữ liệu"),
        html.P("CO₂ dùng đơn vị Mt; dân số tính theo người; CO₂ bình quân tính theo tấn/người."),
        html.P("Nhiệt độ là mức chênh lệch so với mốc tham chiếu giả định."),
    ], className="card data-note")
    return [
        heading,
        notice,
        html.Div(table, className="card table-wrap scroll-table"),
        guide,
    ]


def create_settings_page(preferences):
    heading = html.Div([
        html.Div("KHÔNG GIAN LÀM VIỆC", className="eyebrow"),
        html.H2("Tùy chỉnh hiển thị"),
        html.P("Các lựa chọn được lưu trên trình duyệt này.", className="body-copy"),
    ])
    density_options = [
        {"label": "Thoáng", "value": "comfortable"},
        {"label": "Gọn", "value": "compact"},
    ]
    density = html.Div([
        html.Div([
            html.H3("Mật độ giao diện"),
            html.P("Điều chỉnh khoảng cách trong các thẻ dữ liệu."),
        ]),
        dcc.RadioItems(
            id="setting-density",
            options=density_options,
            value=preferences.get("density", "comfortable"),
            className="settings-radio",
            inline=True,
        ),
    ], className="setting-row")
    grid_options = [
        {"label": "Hiển thị", "value": "show"},
        {"label": "Ẩn", "value": "hide"},
    ]
    grid = html.Div([
        html.Div([
            html.H3("Đường lưới biểu đồ"),
            html.P("Bật đường tham chiếu để đọc và so sánh giá trị."),
        ]),
        dcc.RadioItems(
            id="setting-grid",
            options=grid_options,
            value=preferences.get("grid", "show"),
            className="settings-radio",
            inline=True,
        ),
    ], className="setting-row")
    data_info = html.Div([
        html.Div([
            html.H3("Chế độ dữ liệu"),
            html.P("15 quốc gia · 7 mốc năm · 6 châu lục"),
        ]),
    ], className="setting-row")
    return html.Div([heading, density, grid, data_info], className="card settings-card")


page_heading = html.Header([
    html.Div([
        html.Div("Phân tích dữ liệu", className="page-eyebrow"),
        html.H1("Tổng quan khí hậu", id="page-title"),
        html.P(
            "Theo dõi nhiệt độ và phát thải CO₂ theo thời gian, khu vực và quốc gia.",
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
        return (no_update,) * 9

    title, subtitle = PAGE_INFO[page]

    pages_with_all_countries = {"overview", "earth", "comparison", "relationship"}
    country_filter = "all" if page in pages_with_all_countries else country
    frame = filter_data(years, continent, country_filter)
    series = aggregate(frame)
    scope = scope_name(continent, country)

    invalid_overview_country = (
        page == "overview"
        and country != "all"
        and country not in frame.iso_alpha.values
    )
    if frame.empty or invalid_overview_country:
        content = html.Div([
            html.H2("Chưa có dữ liệu trong phạm vi này"),
            html.P("Chọn quốc gia hoặc khoảng năm khác trong bộ lọc phía trên."),
        ], className="card empty-state")
    elif page == "overview":
        content = create_overview(frame, country, scope, metric)
    elif page == "earth":
        content = create_earth(frame, country if country != "all" else previous_country, metric)
    elif page == "temperature":
        content = create_temperature_page(frame, series, scope)
    elif page == "co2":
        content = create_co2_page(frame, series, scope, country)
    elif page == "comparison":
        content = create_comparison_page(frame)
    elif page == "relationship":
        content = create_relationship_page(frame, country)
    elif page == "forecast":
        content = create_forecast_page(series, scope)
    elif page == "insights":
        content = create_insights_page(frame, series, scope, country)
    elif page == "data":
        content = create_data_page(frame)
    else:
        content = create_settings_page(preferences or {})

    # Tạo vùng nội dung riêng khi đổi trang để Dash không dùng lại biểu đồ cũ.
    content = html.Div(content, key=page)
    navigation_classes = [
        "nav-item" + (" active" if key == page else "")
        for key, _, _ in MENU
    ]
    country_field_class = (
        "filter-field hidden-filter"
        if page in ("comparison", "settings")
        else "filter-field"
    )
    if page == "settings":
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
        page in ("comparison", "settings"),
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
            rotation = {
                axis: view.get(f"geo.projection.rotation.{axis}", rotation.get(axis, 0))
                for axis in ("lon", "lat", "roll")
            }
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
        years[0], years[-1], {value: str(value) for value in years}, year, str(year),
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
    State("globe", "relayoutData"),
    State("globe", "figure"),
    prevent_initial_call=True,
)
def update_selected_country(
    click, resets, map_view, metric, years, continent, country, view, current_figure
):
    frame = filter_data(years, continent)
    available = set(frame.iso_alpha.unique())
    default = choose_country(frame, country)

    figure_data = current_figure.get("data", []) if current_figure else []
    marker_data = figure_data[-1].get("customdata", [default]) if figure_data else [default]
    selected = marker_data[0] if marker_data else default
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
            rotation = {
                key: view.get(f"geo.projection.rotation.{key}", 0)
                for key in ("lon", "lat", "roll")
            }
    if rotation is None:
        if ctx.triggered_id == "reset-globe":
            lon, lat = COORDINATES[default]
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
