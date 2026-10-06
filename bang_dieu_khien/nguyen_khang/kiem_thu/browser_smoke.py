import json
import os
from pathlib import Path
from tempfile import gettempdir

from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:8050")
OUTPUT = Path(gettempdir())
PAGES = {
    "overview": "Tổng quan khí hậu",
    "earth": "Bản đồ khí hậu",
    "temperature": "Nhiệt độ",
    "co2": "Khí thải CO₂",
    "scenario": "Mô hình dự đoán",
    "insights": "Nhận định",
    "data": "Dữ liệu",
}

def check_eda_layout(page, gallery):
    cards = gallery.locator(".interactive .eda-artifact-card")
    for width in (1440, 1024, 390, 1440):
        page.set_viewport_size({"width": width, "height": 1000})
        page.wait_for_function("""() => [...document.querySelectorAll('.interactive .js-plotly-plot')].every(p => {
            const svg = p.querySelector('.main-svg');
            return p?._fullLayout && svg && !p.layout.title?.text && Math.abs(p._fullLayout.width - p.clientWidth) < 2
                && Math.abs(svg.getBoundingClientRect().width - p.clientWidth) < 2;
        })""")
        first, second = [cards.nth(i).bounding_box() for i in (0, 1)]
        if width > 1000:
            assert abs(first["y"] - second["y"]) < 2, "Hai biểu đồ phải cùng hàng"
            assert second["x"] >= first["x"] + first["width"], "Hai biểu đồ chồng nhau"
        else:
            assert second["y"] >= first["y"] + first["height"], "Màn hình nhỏ phải dùng một cột"
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), "Trang bị tràn ngang"
        check_eda_modal(page, gallery)

def check_eda_modal(page, gallery):
    read_data = "e => JSON.stringify(e._fullData.map(t => [t.x, t.y, t.z, t.locations, t.values, t.labels, t.parents]))"

    def geometry():
        return gallery.evaluate("""g => [scrollX, scrollY, document.body.clientWidth,
            ...[...g.querySelectorAll('.interactive .js-plotly-plot')].flatMap(e => {
                const b = e.getBoundingClientRect(), svg = e.querySelector('.main-svg').getBoundingClientRect();
                return [b.x, b.y, b.width, b.height, svg.x, svg.y, svg.width, svg.height,
                        ...Object.values(e._fullLayout._size)];
            })]""")

    cards = gallery.locator(".interactive .eda-artifact-card")
    for index in range(cards.count()):
        close = ("button", "escape", "backdrop")[index % 3]
        card = cards.nth(index)
        button = card.get_by_role("button", name="Mở rộng")
        button.scroll_into_view_if_needed()
        before = geometry()
        original = card.locator(".js-plotly-plot").evaluate(read_data)
        button.click()
        modal = page.locator("#eda-modal.open .js-plotly-plot")
        modal.wait_for()
        assert modal.evaluate(read_data) == original, "Mở rộng làm đổi số liệu"
        assert modal.bounding_box()["width"] > card.bounding_box()["width"]
        for state in ("open", "closed"):
            if state == "closed":
                if close == "button":
                    page.locator("#close-eda-modal").click()
                elif close == "escape":
                    page.keyboard.press("Escape")
                else:
                    page.locator("#eda-modal").click(position={"x": 2, "y": 2})
                page.locator("#eda-modal.open").wait_for(state="hidden")
            after = geometry()
            assert all(abs(a - b) < 1 for a, b in zip(before, after)), (index, state, before, after)

def check_year_slider(page):
    globe = page.locator("#overview-globe .js-plotly-plot")

    def frame():
        return globe.evaluate("""e => {
            const geo=e._fullLayout.geo, b=e.querySelector('.frame path').getBoundingClientRect();
            return [b.width,b.height,...[[0,0],[105,35],[-60,-30],[145,-15]].flatMap(p=>geo._subplot.projection(p))];
        }""")

    for i in range(20):
        globe.scroll_into_view_if_needed()
        box = page.locator("#overview-globe .geo").bounding_box()
        x, y = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
        page.mouse.move(x, y)
        page.mouse.down()
        page.mouse.move(x, y + box["height"] * (.32 if i < 10 else -.32), steps=12)
        page.mouse.up()
        before = frame()
        slider = page.locator("#overview-year [role=slider]")
        if i < 10:
            slider.press("Home" if i % 2 == 0 else "End")
        else:
            slider.scroll_into_view_if_needed()
            rail = page.locator("#overview-year .rc-slider-rail").bounding_box()
            slider.hover()
            page.mouse.down()
            page.mouse.move(rail["x"] + rail["width"] * (i % 2), rail["y"], steps=12)
            page.mouse.up()
        year = 1970 if i % 2 == 0 else 2024
        page.wait_for_function("y => document.querySelector('#overview-year-label').textContent===String(y) && document.querySelector('#overview-globe .js-plotly-plot').data.every(t=>t.customdata.every(r=>r[1]===y))", arg=year)
        after = frame()
        assert abs(after[0] - after[1]) < 1, (i, after)
        assert all(abs(a-b) < 1 for a, b in zip(before, after)), (i, before, after)
    page.locator("#overview-reset").click()
    page.wait_for_function("document.querySelector('#overview-globe .js-plotly-plot')._fullLayout.geo.projection.rotation.lat===15")

def check_map(page, map_id, controls, reset):
    globe = page.locator(f"#{map_id} .js-plotly-plot")
    page.wait_for_function("id => document.querySelectorAll('#'+id+' .choroplethlayer path').length > 200", arg=map_id)
    page.wait_for_function("id => { const e=document.querySelector('#'+id+' .js-plotly-plot'); return Math.abs(e.querySelector('.main-svg').getBoundingClientRect().width-e.clientWidth)<2; }", arg=map_id)

    def camera():
        return globe.evaluate("""e => {
            const g=e._fullLayout.geo, box=e.querySelector('.frame path').getBoundingClientRect();
            return [g.projection.rotation.lon, g.projection.rotation.lat, box.width, box.height];
        }""")

    def drag():
        globe.scroll_into_view_if_needed()
        box = page.locator(f"#{map_id} .geo").bounding_box()
        page.mouse.move(box["x"]+box["width"]*.5, box["y"]+box["height"]*.5)
        page.mouse.down()
        page.mouse.move(box["x"]+box["width"]*.68, box["y"]+box["height"]*.57, steps=12)
        page.mouse.up()

    def select_country(coordinates, code):
        x, y = globe.evaluate("""(e,coordinates) => {
            const [x,y]=e._fullLayout.geo._subplot.projection(coordinates), box=e.getBoundingClientRect();
            return [x+box.x,y+box.y];
        }""", coordinates)
        page.mouse.move(x, y)
        page.wait_for_timeout(150)
        page.mouse.click(x, y)
        page.wait_for_function("([id,code]) => document.querySelector('#'+id+' .js-plotly-plot').layout.meta.selected===code", arg=[map_id, code])

    selected = globe.evaluate("e => e.layout.meta.selected")
    before = camera()
    drag()
    rotated = camera()
    assert abs(rotated[0]-before[0]) > 1
    assert globe.evaluate("e => e.layout.meta.selected") == selected
    select_country([105, 35], "CHN")
    assert all(abs(a-b) < .1 for a, b in zip(camera(), rotated)), (map_id, rotated, camera())
    for _ in range(3):
        for label, projection in [("Bản đồ phẳng", "natural earth"), ("Địa cầu", "orthographic")]:
            page.locator(f"#{controls} label").filter(has_text=label).click()
            page.wait_for_function("([id,type]) => document.querySelector('#'+id+' .js-plotly-plot')._fullLayout.geo.projection.type===type", arg=[map_id, projection])
            if label == "Bản đồ phẳng":
                select_country([-64, -34], "ARG")
                drag()
        assert all(abs(a-b) < .1 for a, b in zip(camera(), rotated))
        assert abs(camera()[2]-camera()[3]) < 1
    page.locator(f"#{reset}").click()
    page.wait_for_function("id => document.querySelector('#'+id+' .js-plotly-plot')._fullLayout.geo.projection.rotation.lon===105", arg=map_id)
    assert globe.evaluate("e => e.layout.meta.selected") == "ARG"
    assert "Argentina" in page.locator("#country-filter").inner_text()
    if map_id == "globe":
        saved = camera()
        page.locator("#metric-filter").click()
        page.locator("#metric-filter").get_by_text("Khí thải CO₂", exact=True).click()
        page.wait_for_function("document.querySelector('#globe .js-plotly-plot').data.some(t=>t.name==='CO₂')")
        page.locator("#year-range").click()
        page.locator("#year-range").get_by_text("1990 – 2023", exact=True).click()
        page.wait_for_function("document.querySelector('#country-panel .selection-year').textContent==='2023'")
        assert page.locator("#country-panel h2").inner_text() == "Argentina"
        assert all(abs(a-b) < .1 for a, b in zip(camera(), saved))

def main() -> None:
    console_errors: list[str] = []
    page_errors: list[str] = []
    checked: dict[str, dict] = {}

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            channel=os.environ.get("BROWSER_CHANNEL"),
            headless=True,
            ignore_default_args=["--hide-scrollbars"],
            args=["--no-sandbox", "--disable-gpu"],
        )
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        page.on(
            "console",
            lambda message: console_errors.append(message.text)
            if message.type == "error" else None,
        )
        page.on("pageerror", lambda error: page_errors.append(str(error)))
        page.goto(BASE_URL, wait_until="networkidle")
        page.add_style_tag(content="::-webkit-scrollbar { width: 15px; height: 15px; }")
        page.locator("#page-title").wait_for(state="visible")

        check_map(page, "overview-globe", "overview-map-view", "overview-reset")
        check_year_slider(page)

        country_filter = page.locator("#country-filter")
        country_filter.click()
        country_filter.locator("input").fill("Vietnam")
        country_filter.locator("input").press("Enter")
        page.wait_for_function(
            "() => document.querySelector('#overview-map-selection')?.textContent.includes('Vietnam')"
        )
        checked["interactions"] = {
            "country": "Vietnam",
            "map_round_trips": 6,
            "selection_keeps_camera": True,
            "polar_drag_year_changes": 20,
        }

        page.locator('a[href="#earth"]').first.click()
        page.get_by_text("Bản đồ thế giới", exact=True).wait_for()
        check_map(page, "globe", "earth-map-view", "reset-globe")

        for route, expected_title in PAGES.items():
            page.locator(f'a[href="#{route}"]').first.click()
            page.wait_for_function(
                "expected => document.querySelector('#page-title')?.textContent.trim() === expected",
                arg=expected_title,
            )
            page.locator("#page-content").wait_for(state="visible")
            page.wait_for_timeout(250)
            checked[route] = {
                "title": page.locator("#page-title").inner_text(),
                "charts": page.locator(".js-plotly-plot").count(),
                "cards": page.locator(".card").count(),
            }

        page.locator('a[href="#data"]').first.click()
        page.locator("#export-data").wait_for()
        with page.expect_download() as download_info:
            page.locator("#export-data").click()
        download = download_info.value
        export_path = download.path()
        export_header = open(export_path, encoding="utf-8").readline().strip()
        if "temperature_anomaly" not in export_header or "co2" not in export_header:
            raise AssertionError(f"CSV xuất thiếu cột: {export_header}")
        checked["export"] = {"filename": download.suggested_filename}

        page.locator('a[href="#overview"]').first.click()
        country_filter.click()
        country_filter.locator("input").fill("Vietnam")
        country_filter.locator("input").press("Enter")
        page.wait_for_function("document.querySelector('#overview-summary h2')?.textContent==='Vietnam'")
        checked["interactions"]["fast_navigation_filter_sync"] = True

        page.locator('a[href="#co2"]').first.click()
        quan_gallery = page.locator("#quan-eda-gallery")
        quan_gallery.wait_for()
        quan_gallery.locator("summary").wait_for()
        quan_gallery.get_by_text("Biểu đồ tương tác", exact=True).wait_for()
        if quan_gallery.locator("img").count() != 5:
            raise AssertionError("Trang CO₂ chưa hiển thị đủ 5 biểu đồ tĩnh của Quân")
        if quan_gallery.locator(".js-plotly-plot").count() != 6:
            raise AssertionError("Trang CO₂ chưa hiển thị đủ 6 biểu đồ tương tác của Quân")
        assert page.locator("#filter-bar").is_visible()
        page.wait_for_function("document.querySelector('#quan-eda-gallery .js-plotly-plot')._fullData[0].x[0]===1990")
        assert "Vietnam" in page.locator("#page-subtitle").inner_text()
        check_eda_layout(page, quan_gallery)

        page.locator('a[href="#temperature"]').first.click()
        duc_gallery = page.locator("#duc-eda-gallery")
        duc_gallery.wait_for()
        duc_gallery.locator("summary").wait_for()
        duc_gallery.get_by_text("Biểu đồ tương tác", exact=True).wait_for()
        section_titles = duc_gallery.locator(".eda-format-heading h3").all_inner_texts()
        if section_titles != ["Biểu đồ tương tác"]:
            raise AssertionError(f"Sai thứ tự nhóm biểu đồ: {section_titles}")
        interactive_card = duc_gallery.locator(".eda-artifact-grid.interactive .eda-artifact-card").first
        check_eda_layout(page, duc_gallery)
        if not interactive_card.locator(".eda-artifact-heading h3").inner_text().strip():
            raise AssertionError("Biểu đồ tương tác bị mất tiêu đề")
        if duc_gallery.locator("img").count() != 5:
            raise AssertionError("Trang Nhiệt độ chưa hiển thị đủ 5 biểu đồ tĩnh của Đức")
        if duc_gallery.locator(".js-plotly-plot").count() != 6:
            raise AssertionError("Trang Nhiệt độ chưa hiển thị đủ 6 biểu đồ tương tác của Đức")
        assert page.locator("#filter-bar").is_visible()
        page.locator('a[href="#insights"]').first.click()
        page.locator(".insight-grid").wait_for()
        for width in (1440, 390):
            page.set_viewport_size({"width": width, "height": 1000})
            page.wait_for_function("document.documentElement.scrollWidth <= innerWidth")
            page.screenshot(path=OUTPUT / f"climate_insights_{width}.png", full_page=True)
        page.set_viewport_size({"width": 1440, "height": 1000})
        continent_filter = page.locator("#continent-filter")
        continent_filter.click()
        continent_filter.get_by_text("Châu Âu", exact=True).click()
        page.wait_for_function("document.querySelector('#page-subtitle').textContent==='Châu Âu · 1990–2023'")
        assert "Tất cả quốc gia" in country_filter.inner_text()
        assert "nan" not in page.locator(".insight-grid").inner_text().lower()

        page.locator('a[href="#scenario"]').first.click()
        page.locator("#scenario-temperature-chart").wait_for()
        if page.locator("#page-content .js-plotly-plot").count() != 3:
            raise AssertionError("Trang kịch bản phải có nhiệt độ, CO₂ và kiểm tra mô hình")
        page.locator("#scenario-choice label").filter(has_text="Giảm 5%/năm").click()
        page.wait_for_function(
            "() => document.querySelector('#scenario-difference-note')?.textContent.includes('Thấp hơn')"
        )
        page.locator("#scenario-choice label").filter(has_text="Tùy chỉnh").click()
        page.wait_for_function(
            "() => !document.querySelector('#scenario-custom-control')?.hidden"
        )
        page.locator('#scenario-rate [role="slider"]').press("End")
        page.wait_for_function(
            "() => document.querySelector('#scenario-emissions-note')?.textContent.includes('+5.00%')"
        )
        page.locator("#scenario-year label").filter(has_text="2030").click()
        page.wait_for_function(
            "() => document.querySelector('#scenario-temp-note')?.textContent.startsWith('2030')"
        )
        with page.expect_download() as scenario_download_info:
            page.locator("#download-scenarios-button").click()
        scenario_header = open(
            scenario_download_info.value.path(), encoding="utf-8"
        ).readline().strip()
        if "scenario_id" not in scenario_header or "temperature_prediction" not in scenario_header:
            raise AssertionError(f"CSV kịch bản thiếu cột: {scenario_header}")

        page.locator("#scenario-choice label").filter(has_text="Tiếp diễn").click()
        page.locator("#scenario-year label").filter(has_text="2050").click()
        page.wait_for_function(
            "() => document.querySelector('#scenario-temp-note')?.textContent.startsWith('2050')"
        )

        page.screenshot(path=OUTPUT / "climate_dashboard_desktop.png", full_page=True)

        page.set_viewport_size({"width": 390, "height": 844})
        page.goto(f"{BASE_URL}/#scenario", wait_until="networkidle")
        page.locator("#page-title").wait_for(state="visible")
        page.wait_for_timeout(300)
        dimensions = page.evaluate(
            "() => ({width: innerWidth, scrollWidth: document.documentElement.scrollWidth})"
        )
        page.screenshot(path=OUTPUT / "climate_dashboard_mobile.png", full_page=True)
        browser.close()

    if page_errors or console_errors:
        raise AssertionError({"page_errors": page_errors, "console_errors": console_errors})
    if dimensions["scrollWidth"] > dimensions["width"] + 2:
        raise AssertionError(f"Mobile bị tràn ngang: {dimensions}")

    result = {
        "pages": checked,
        "mobile": dimensions,
        "screenshots": [
            str(OUTPUT / "climate_dashboard_desktop.png"),
            str(OUTPUT / "climate_dashboard_mobile.png"),
        ],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
