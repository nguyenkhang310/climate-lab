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

def check_eda_country_click(page, gallery):
    page.wait_for_load_state("networkidle")
    field = page.locator("#country-filter")
    previous = field.inner_text().strip()
    field.click()
    field.locator("input").fill("Tất cả quốc gia")
    field.locator("input").press("Enter")
    plot = gallery.locator(".interactive .eda-artifact-card").nth(2).locator(".js-plotly-plot")
    page.wait_for_function("id => document.querySelector('#'+id+' .interactive .eda-artifact-card:nth-child(3) .js-plotly-plot')?.data?.some(t=>t.locations?.includes('AUS'))", arg=gallery.get_attribute("id"))
    stop = plot.get_by_text("■ Dừng", exact=True)
    if stop.count():
        stop.click()
        page.wait_for_function("id => !document.querySelector('#'+id+' .interactive .eda-artifact-card:nth-child(3) .js-plotly-plot')?._transitionData?._frameQueue?.length", arg=gallery.get_attribute("id"))
    plot.scroll_into_view_if_needed()
    x, y = plot.evaluate("""e => {
        const [x,y]=e._fullLayout.geo._subplot.projection([134,-25]), b=e.getBoundingClientRect();
        return [x+b.x,y+b.y];
    }""")
    page.mouse.move(x, y)
    page.wait_for_timeout(150)
    page.mouse.click(x, y)
    page.wait_for_function("document.querySelector('#country-filter').innerText.trim()==='Australia'")
    page.wait_for_function("document.querySelector('#page-subtitle').textContent.startsWith('Australia ·')")
    page.wait_for_function("id => [...document.querySelectorAll('#'+id+' .js-plotly-plot')].every(p=>p._fullLayout?.meta?.scope.startsWith('Australia ·'))", arg=gallery.get_attribute("id"))
    field.click()
    field.locator("input").fill(previous)
    field.locator("input").press("Enter")
    page.wait_for_function("([id,name]) => [...document.querySelectorAll('#'+id+' .js-plotly-plot')].every(p=>p._fullLayout?.meta?.scope.startsWith(name+' ·'))", arg=[gallery.get_attribute("id"), "Toàn cầu" if previous == "Tất cả quốc gia" else previous])
    page.wait_for_load_state("networkidle")

def check_eda_layout(page, gallery):
    cards = gallery.locator(".interactive .eda-artifact-card")
    animated = cards.nth(2).locator(".js-plotly-plot").evaluate("e => !!e._transitionData?._frames?.length")
    if animated:
        for _ in range(3):
            cards.nth(2).get_by_text("▶ Phát", exact=True).click()
            page.wait_for_function("id => document.querySelector('#' + id + ' .interactive .eda-artifact-card:nth-child(3) .js-plotly-plot')?.layout?.sliders?.[0]?.active > 0",
                                   arg=gallery.get_attribute("id"))
            cards.nth(2).get_by_text("■ Dừng", exact=True).click()
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
        plot = card.locator(".js-plotly-plot")
        original = plot.evaluate(read_data)
        animated = plot.evaluate("e => !!e._transitionData?._frames?.length")
        button.click()
        modal = page.locator("#eda-modal.open .js-plotly-plot")
        modal.wait_for()
        if not animated:
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
        year = 1961 if i % 2 == 0 else 2024
        page.wait_for_function("y => document.querySelector('#overview-year-label').textContent===String(y) && document.querySelector('#overview-globe .js-plotly-plot').data.every(t=>t.customdata.every(r=>r[1]===y))", arg=year)
        after = frame()
        assert abs(after[0] - after[1]) < 1, (i, after)
        assert all(abs(a-b) < 1 for a, b in zip(before, after)), (i, before, after)
    page.locator("#overview-reset").click()
    page.wait_for_function("document.querySelector('#overview-globe .js-plotly-plot')._fullLayout.geo.projection.rotation.lat===15")

def check_overview_links(page):
    def check_focus(lon, lat):
        page.wait_for_function("""([lon,lat]) => {
            const p=document.querySelector('#overview-globe .js-plotly-plot');
            const r=p._fullLayout.geo.projection.rotation;
            return Math.abs(r.lon-lon)<.01 && Math.abs(r.lat-lat)<.01;
        }""", arg=[lon, lat])
        offset = page.locator("#overview-globe .js-plotly-plot").evaluate("""(p, coords) => {
            const b=p.getBoundingClientRect(), f=p.querySelector('.frame path').getBoundingClientRect();
            const [x,y]=p._fullLayout.geo._subplot.projection(coords);
            return [x+b.x-f.x-f.width/2,y+b.y-f.y-f.height/2,f.width-f.height];
        }""", [lon, lat])
        assert all(abs(v)<1 for v in offset), offset

    ranking = page.locator("#overview-ranking .js-plotly-plot")
    name, code = ranking.evaluate("e => [e.data[0].y[0], e.data[0].customdata[0][0]]")
    bar = ranking.locator(".barlayer .point path").first
    bar.hover(force=True)
    page.wait_for_function("document.querySelector('#overview-ranking .hoverlayer').textContent.includes('triệu tấn')")
    assert "Năm 2024" in ranking.locator(".hoverlayer").text_content()
    bar.click(force=True)
    page.wait_for_function("name => document.querySelector('#overview-summary h2').textContent === name", arg=name)
    page.wait_for_function("code => document.querySelector('#overview-globe .js-plotly-plot').layout.meta.selected === code", arg=code)
    world = json.loads(Path(__file__).parents[1].joinpath("tai_nguyen/world_110m.json").read_text())
    coordinates = next(g["properties"]["ct"] for g in world["objects"]["countries"]["geometries"] if g.get("id") == code)
    check_focus(*coordinates)
    bar.click(force=True)
    page.wait_for_function("document.querySelector('#overview-summary h2').textContent === 'Toàn cầu'")
    pie = page.locator("#overview-continents .js-plotly-plot")
    index = pie.evaluate("e => e.data[0].labels.indexOf('Châu Âu')")
    pie.locator(".slice").nth(index).click()
    page.wait_for_function("document.querySelector('#overview-summary h2').textContent === 'Châu Âu'")
    page.wait_for_function("document.querySelector('#overview-ranking-note').textContent.startsWith('Châu Âu')")
    check_focus(15, 50)
    paths = pie.locator(".slice .surface").evaluate_all("nodes=>nodes.map(e=>e.getAttribute('d'))")
    for expected in ("Toàn cầu", "Châu Âu", "Toàn cầu"):
        page.mouse.down()
        page.mouse.up()
        page.wait_for_function("v=>document.querySelector('#overview-summary h2').textContent===v", arg=expected)
        assert pie.locator(".slice .surface").evaluate_all("nodes=>nodes.map(e=>e.getAttribute('d'))") == paths
    for region, label, lon, lat in (
        ("Africa", "Châu Phi", 20, 0), ("Asia", "Châu Á", 100, 30),
        ("Europe", "Châu Âu", 15, 50), ("North America", "Bắc Mỹ", -100, 45),
        ("South America", "Nam Mỹ", -60, -20), ("Oceania", "Châu Đại Dương", 140, -25),
    ):
        index = pie.evaluate("(e, name)=>e.data[0].customdata.findIndex(d=>d[0]===name)", region)
        for expected in (label, "Toàn cầu"):
            pie.scroll_into_view_if_needed()
            x, y = pie.evaluate("""(e,i) => {
                const d=e.calcdata[0], p=d[i], r=d[0].r*.81, b=e.getBoundingClientRect();
                return [b.x+d[0].cx+r*Math.sin(p.midangle), b.y+d[0].cy-r*Math.cos(p.midangle)];
            }""", index)
            page.mouse.click(x, y)
            page.wait_for_function("v=>document.querySelector('#overview-summary h2').textContent===v", arg=expected)
            check_focus(lon if expected == label else 105, lat if expected == label else 15)
    for chart, year in [("overview-temperature", 2000), ("overview-co2", 2010)]:
        plot = page.locator(f"#{chart} .js-plotly-plot")
        index = plot.evaluate("(e, year) => Array.from(e._fullData[0].x).indexOf(year)", year)
        point = plot.locator(".scatterlayer .points path").nth(index)
        point.hover(force=True)
        page.wait_for_function("([id,y]) => document.querySelector('#'+id+' .hoverlayer').textContent.includes('Năm '+y)", arg=[chart, year])
        point.click(force=True)
        page.wait_for_function("y => document.querySelector('#overview-year-label').textContent === String(y)", arg=year)
        page.wait_for_function("y => document.querySelector('#overview-ranking-note').textContent.includes(String(y))", arg=year)
        for target in ("overview-temperature", "overview-co2"):
            assert page.locator(f"#{target} .js-plotly-plot").evaluate("e => e.layout.shapes[0].x0") == year
        page.wait_for_function("y => document.querySelector('#overview-globe .js-plotly-plot').data.every(t=>t.customdata.every(r=>r[1]===y))", arg=year)
        page.locator('#overview-year [role="slider"]').press("End")
        page.wait_for_function("document.querySelector('#overview-year-label').textContent==='2024'")
        point.click(force=True)
        page.wait_for_function("y=>document.querySelector('#overview-year-label').textContent===String(y)", arg=year)
    name = ranking.evaluate("e => e.data[0].y[0]")
    index = pie.evaluate("e => e.data[0].labels.indexOf('Châu Âu')")
    for element, scope in [(bar, name), (pie.locator(".slice").nth(index), "Châu Âu")]:
        for expected in (scope, "Toàn cầu"):
            element.hover(force=True)
            element.click(force=True)
            page.wait_for_function("v => document.querySelector('#overview-summary h2').textContent === v", arg=expected)
            assert page.locator('#overview-year-label').inner_text() == "2010", "Chọn vùng không được đổi năm"
    page.locator('#overview-year [role="slider"]').press("End")
    page.wait_for_function("document.querySelector('#overview-year-label').textContent === '2024'")
    for chart, index, selected in [("overview-scenario-co2", 2, "decline"), ("overview-forecast", 3, "trend")]:
        plot = page.locator(f"#{chart} .js-plotly-plot")
        for repeat in range(2):
            plot.scroll_into_view_if_needed()
            x, y = plot.evaluate("""(e, index) => {
                const t=e._fullData[index], l=e._fullLayout, box=e.getBoundingClientRect(), i=20;
                return [box.x+l.xaxis._offset+l.xaxis.l2p(t.x[i]), box.y+l.yaxis._offset+l.yaxis.l2p(t.y[i])];
            }""", index)
            page.mouse.move(x, y)
            page.wait_for_timeout(150)
            page.mouse.click(x, y)
            label = "Giảm 5%/năm" if selected == "decline" else "Tiếp diễn"
            page.wait_for_function("v => document.querySelector('#overview-scenario input:checked').parentElement.textContent === v", arg=label)
            page.wait_for_function("v => document.querySelector('#overview-scenario-co2 .js-plotly-plot').data.find(t=>t.line.width===3).customdata[0][0] === v", arg=selected)
            if repeat == 0:
                page.locator("#overview-scenario label").filter(has_text="Giữ mức 2024").click()
                page.wait_for_function("document.querySelector('#overview-scenario-co2 .js-plotly-plot').data.find(t=>t.line.width===3).customdata[0][0]==='stable'")
    for width in (1440, 1024, 768, 360, 390, 1440):
        page.set_viewport_size({"width": width, "height": 1000})
        page.wait_for_function("""() => {
            const e=document.querySelector('#overview-globe'), p=e?.querySelector('.js-plotly-plot');
            return p?._fullLayout && Math.abs(e.clientWidth-p._fullLayout.width)<2;
        }""")
        page.wait_for_timeout(250)
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), width
        geometry = page.locator("#overview-globe").evaluate("""e => {
            const b=e.getBoundingClientRect(), g=e.querySelector('.frame path').getBoundingClientRect();
            return [g.x+g.width/2-b.x-b.width/2,g.width-g.height,g.x-b.x,b.right-g.right];
        }""")
        assert abs(geometry[0]) < 1 and abs(geometry[1]) < 1 and min(geometry[2:]) >= 0, (width, geometry)
        globe_frame = page.locator("#overview-globe .frame path").bounding_box()
        colorbar = page.locator("#overview-globe .colorbar").bounding_box()
        assert colorbar["x"] >= globe_frame["x"] + globe_frame["width"], (width, globe_frame, colorbar)
        timeline = page.locator(".overview-timeline")
        assert timeline.bounding_box()["height"] < 85
        heading = timeline.locator(".overview-year-heading").bounding_box()
        handle = timeline.locator(".rc-slider-handle").bounding_box()
        mark = timeline.locator(".rc-slider-mark-text").first.bounding_box()
        assert handle["y"] - heading["y"] - heading["height"] >= 4
        assert mark["y"] - handle["y"] - handle["height"] >= 4
        ring = pie.locator(".pielayer .trace").bounding_box()
        label = pie.locator(".annotation-text-g").bounding_box()
        legend = pie.locator(".legend").bounding_box()
        assert abs(label["x"] + label["width"]/2 - ring["x"] - ring["width"]/2) < 1
        assert abs(label["y"] + label["height"]/2 - ring["y"] - ring["height"]/2) < 1
        assert (label["width"]**2 + label["height"]**2)**.5 < ring["width"] * .62
        assert ring["x"] + ring["width"] + 8 <= legend["x"]
        assert legend["x"] + legend["width"] <= pie.bounding_box()["x"] + pie.bounding_box()["width"]
        if width > 1000:
            if width == 1440:
                assert globe_frame["height"] > 350
            for grid in page.locator(".overview-section .chart-grid").all():
                left, right = [card.bounding_box() for card in grid.locator(":scope > .card").all()]
                assert abs(left["width"]-right["width"]) < 1 and abs(left["y"]-right["y"]) < 1
                assert abs(left["height"]-right["height"]) < 1
        if width in (1440, 390):
            page.evaluate("window.scrollTo(0, 0)")
            page.mouse.move(0, 0)
            page.screenshot(path=OUTPUT / f"climate_overview_{width}.png", full_page=True)
    for collapsed in (True, False):
        page.locator("#collapse-sidebar").click()
        page.wait_for_function("v => document.querySelector('#app-shell').classList.contains('collapsed') === v", arg=collapsed)
        page.wait_for_function("""() => {
            const e=document.querySelector('#overview-globe'), p=e.querySelector('.js-plotly-plot');
            const b=e.getBoundingClientRect(), g=e.querySelector('.frame path').getBoundingClientRect();
            return Math.abs(p._fullLayout.width-e.clientWidth)<2 && Math.abs(g.x+g.width/2-b.x-b.width/2)<1;
        }""")
        page.wait_for_timeout(250)
        assert page.evaluate("""[...document.querySelectorAll('.js-plotly-plot')].every(
            p => !p.offsetParent || Math.abs(p._fullLayout.width-p.clientWidth)<2)""")

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
        if globe.evaluate("(e, code)=>e.layout.meta.selected===code", code):
            return
        x, y = globe.evaluate("""(e,coordinates) => {
            const [x,y]=e._fullLayout.geo._subplot.projection(coordinates), box=e.getBoundingClientRect();
            return [x+box.x,y+box.y];
        }""", coordinates)
        page.mouse.move(x, y)
        page.wait_for_timeout(150)
        page.mouse.click(x, y)
        page.wait_for_function("([id,code]) => document.querySelector('#'+id+' .js-plotly-plot').layout.meta.selected===code", arg=[map_id, code])
        name = globe.evaluate("(e,code) => {const t=e.data.find(t=>t.locations.includes(code));return t.customdata[t.locations.indexOf(code)][0];}", code)
        page.wait_for_function("name => document.querySelector('#country-filter').innerText.trim()===name", arg=name)
        summary = "overview-summary" if map_id == "overview-globe" else "country-panel"
        page.wait_for_function("([id,name]) => document.querySelector('#'+id+' h2').textContent===name", arg=[summary, name])

    selected = globe.evaluate("e => e.layout.meta.selected")
    before = camera()
    drag()
    rotated = camera()
    assert abs(rotated[0]-before[0]) > 1
    assert globe.evaluate("e => e.layout.meta.selected") == selected
    select_country([105, 35], "CHN")
    assert all(abs(a-b) < .1 for a, b in zip(camera(), rotated)), (map_id, rotated, camera())
    x, y = globe.evaluate("""e => {
        const [x,y]=e._fullLayout.geo._subplot.projection([105,35]), box=e.getBoundingClientRect();
        return [x+box.x,y+box.y];
    }""")
    page.mouse.click(x, y)
    page.wait_for_function("id => document.querySelector('#'+id+' .js-plotly-plot').layout.meta.selected==='all'", arg=map_id)
    page.wait_for_function("document.querySelector('#country-filter').innerText.trim()==='Tất cả quốc gia'")
    select_country([105, 35], "CHN")
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
    page.locator("#continent-filter").click()
    page.locator("#continent-filter").get_by_text("Châu Á", exact=True).click()
    page.wait_for_function("id => document.querySelector('#'+id+' .js-plotly-plot').layout.meta.selected==='all'", arg=map_id)
    before = camera()
    select_country([134, -25], "AUS")
    assert "Châu Đại Dương" in page.locator("#continent-filter").inner_text()
    select_country([105, 35], "CHN")
    assert "Châu Á" in page.locator("#continent-filter").inner_text()
    assert all(abs(a-b) < .1 for a, b in zip(camera(), before))
    page.locator("#continent-filter").click()
    page.locator("#continent-filter").get_by_text("Tất cả châu lục", exact=True).click()
    page.wait_for_function("id => document.querySelector('#'+id+' .js-plotly-plot').data.some(t=>t.locations.includes('ARG')&&t.showscale)", arg=map_id)
    page.locator(f"#{controls} label").filter(has_text="Bản đồ phẳng").click()
    page.wait_for_function("id => document.querySelector('#'+id+' .js-plotly-plot')._fullLayout.geo.projection.type==='natural earth'", arg=map_id)
    select_country([-64, -34], "ARG")
    page.locator(f"#{controls} label").filter(has_text="Địa cầu").click()
    page.wait_for_function("id => document.querySelector('#'+id+' .js-plotly-plot')._fullLayout.geo.projection.type==='orthographic'", arg=map_id)
    if map_id == "globe":
        saved = camera()
        page.locator("#metric-filter").click()
        page.locator("#metric-filter").get_by_text("Khí thải CO₂", exact=True).click()
        page.wait_for_function("document.querySelector('#globe .js-plotly-plot').data.some(t=>t.name==='CO₂')")
        page.locator("#year-range").click()
        page.locator("#year-range").get_by_text("1990–1999", exact=True).click()
        page.wait_for_function("document.querySelector('#country-panel .selection-year').textContent==='1999'")
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

        page.wait_for_function("document.querySelector('#overview-temperature .js-plotly-plot')?._fullData[0].x[0]===1961")
        page.locator("#year-range").click()
        page.locator("#year-range").get_by_text("1961–1969 (chưa đủ 10 năm)", exact=True).click()
        page.wait_for_function("document.querySelector('#page-subtitle')?.textContent==='Toàn cầu · 1961–1969'")
        page.wait_for_function("document.querySelector('#overview-temperature .js-plotly-plot')?._fullData[0].x.length===9")
        page.wait_for_function("document.querySelector('#overview-continents .js-plotly-plot')?.data[0]?.type==='pie'")
        page.locator('a[href="#co2"]').first.click()
        page.wait_for_function("document.querySelector('#quan-eda-gallery .js-plotly-plot')?._fullData[0].x[0]===1850")
        page.locator('a[href="#overview"]').first.click()
        page.wait_for_function("document.querySelector('#page-subtitle')?.textContent==='Toàn cầu · 1961–1969'")
        page.wait_for_function("document.querySelector('#overview-temperature .js-plotly-plot')?._fullData[0].x.length===9")
        page.locator("#year-range").click()
        page.locator("#year-range").get_by_text("Toàn bộ · 1961–2024", exact=True).click()
        page.wait_for_function("document.querySelector('#overview-temperature .js-plotly-plot')?._fullData[0].x.length===64")
        page.wait_for_function("document.querySelector('#overview-year-label')?.textContent==='2024'")
        page.wait_for_function("document.querySelector('#overview-globe .js-plotly-plot').data.every(t=>t.customdata.every(r=>r[1]===2024))")
        page.wait_for_function("document.querySelector('#overview-continents .js-plotly-plot')?.data[0]?.type==='pie'")
        page.locator('#overview-year [role="slider"]').press("End")
        page.wait_for_function("document.querySelector('#overview-year-label')?.textContent==='2024'")
        checked["independent_decades"] = {"overview": "1961–2024", "co2": "1850–2024", "restored": "1961–1969"}

        check_overview_links(page)
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
            page.wait_for_load_state("networkidle")
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
        page.wait_for_function("""() => {
            const card = document.querySelectorAll('#quan-eda-gallery .interactive .eda-artifact-card')[3];
            const plot = card?.querySelector('.js-plotly-plot');
            return card?.textContent.includes('Lượng CO₂ theo châu lục')
                && plot?._fullData.length > 0
                && plot._fullData.every(trace => trace.stackgroup === '1');
        }""")
        assert page.locator("#filter-bar").is_visible()
        page.wait_for_function("document.querySelector('#quan-eda-gallery .js-plotly-plot')._fullData[0].x[0]===1850")
        assert "Toàn cầu" in page.locator("#page-subtitle").inner_text()
        check_eda_country_click(page, quan_gallery)
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
        check_eda_country_click(page, duc_gallery)
        check_eda_layout(page, duc_gallery)
        if not interactive_card.locator(".eda-artifact-heading h3").inner_text().strip():
            raise AssertionError("Biểu đồ tương tác bị mất tiêu đề")
        if duc_gallery.locator("img").count() != 6:
            raise AssertionError("Trang Nhiệt độ chưa hiển thị đủ 6 biểu đồ tĩnh của Đức")
        duc_gallery.locator("summary").click()
        monthly_static = duc_gallery.locator(".static .eda-artifact-card").last
        monthly_static.scroll_into_view_if_needed()
        page.wait_for_function("document.querySelector('#duc-eda-gallery .static img[src$=\"06_nhiet_do_theo_thang.png\"]')?.naturalWidth > 0")
        assert "1880–2025" in monthly_static.inner_text()
        monthly_static.get_by_role("button", name="Mở rộng").click()
        page.locator('#eda-modal.open img[src$="06_nhiet_do_theo_thang.png"]').wait_for()
        page.locator("#close-eda-modal").click()
        duc_gallery.locator("summary").click()
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
        page.wait_for_function("document.querySelector('#page-subtitle').textContent==='Châu Âu · 1961–2024'")
        assert "Tất cả quốc gia" in country_filter.inner_text()
        assert "nan" not in page.locator(".insight-grid").inner_text().lower()

        page.locator('a[href="#scenario"]').first.click()
        page.locator("#scenario-temperature-chart").wait_for()
        page.wait_for_function("document.querySelector('#scenario-temperature-chart .js-plotly-plot')?._fullLayout.xaxis.range[0]===1880")
        assert page.locator("#header-data-range").inner_text() == "1880–2024"
        assert page.locator("#scenario-temperature-chart .js-plotly-plot").evaluate("p => p._fullLayout.yaxis.range[0] < 0")
        if page.locator("#page-content .js-plotly-plot").count() != 4:
            raise AssertionError("Trang kịch bản phải có đủ 4 biểu đồ mô hình")
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
