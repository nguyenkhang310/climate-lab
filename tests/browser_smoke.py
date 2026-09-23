from __future__ import annotations

import json

from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:8050"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PAGES = {
    "overview": "Tổng quan khí hậu",
    "earth": "Bản đồ khí hậu",
    "temperature": "Nhiệt độ",
    "co2": "Phát thải CO₂",
    "forecast": "Dự báo",
    "insights": "Nhận định",
    "data": "Dữ liệu",
    "settings": "Cài đặt",
}

def main() -> None:
    console_errors: list[str] = []
    page_errors: list[str] = []
    checked: dict[str, dict] = {}

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=CHROME,
            headless=True,
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
        page.locator("#page-title").wait_for(state="visible")

        country_filter = page.locator("#country-filter")
        country_filter.click()
        country_filter.locator("input").fill("Viet Nam")
        country_filter.locator("input").press("Enter")
        page.wait_for_function(
            "() => document.querySelector('#overview-map-selection')?.textContent.includes('Viet Nam')"
        )
        page.locator("#overview-map-view label").filter(has_text="Bản đồ ngang").click()
        page.wait_for_function(
            "() => [...document.querySelectorAll('#overview-map-view input')].some(input => input.checked && input.parentElement.textContent.includes('Bản đồ ngang'))"
        )
        checked["interactions"] = {
            "country": "Viet Nam",
            "map_view": "flat",
        }

        page.locator('a[href="#earth"]').first.click()
        page.get_by_text("Bản đồ khí hậu tương tác", exact=True).wait_for()
        page.locator("#earth-map-view label").filter(has_text="Bản đồ ngang").click()
        page.wait_for_function(
            "() => [...document.querySelectorAll('#earth-map-view input')].some(input => input.checked && input.parentElement.textContent.includes('Bản đồ ngang'))"
        )
        page.locator("#reset-globe").click()

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

        page.locator('a[href="#co2"]').first.click()
        quan_gallery = page.locator("#quan-eda-gallery")
        quan_gallery.wait_for()
        quan_gallery.get_by_text("Biểu đồ tĩnh", exact=True).wait_for()
        quan_gallery.get_by_text("Biểu đồ tương tác", exact=True).wait_for()
        if quan_gallery.locator("img").count() != 5:
            raise AssertionError("Trang CO₂ chưa hiển thị đủ 5 biểu đồ tĩnh của Quân")
        if quan_gallery.locator("iframe").count() != 6:
            raise AssertionError("Trang CO₂ chưa hiển thị đủ 6 biểu đồ tương tác của Quân")
        if page.locator("#page-content .js-plotly-plot").count() != 0:
            raise AssertionError("Trang CO₂ còn biểu đồ dashboard không thuộc phần Quân")

        page.locator('a[href="#temperature"]').first.click()
        duc_gallery = page.locator("#duc-eda-gallery")
        duc_gallery.wait_for()
        duc_gallery.get_by_text("Biểu đồ tĩnh", exact=True).wait_for()
        duc_gallery.get_by_text("Biểu đồ tương tác", exact=True).wait_for()
        section_titles = duc_gallery.locator(".eda-format-heading h3").all_inner_texts()
        if section_titles != ["Biểu đồ tương tác", "Biểu đồ tĩnh"]:
            raise AssertionError(f"Sai thứ tự nhóm biểu đồ: {section_titles}")
        interactive_card = duc_gallery.locator(".eda-artifact-grid.interactive .eda-artifact-card").first
        card_box = interactive_card.bounding_box()
        gallery_box = duc_gallery.bounding_box()
        frame_box = interactive_card.locator("iframe").bounding_box()
        if card_box["width"] < gallery_box["width"] * .9 or frame_box["height"] < 600:
            raise AssertionError("Biểu đồ tương tác vẫn bị thu nhỏ")
        if not interactive_card.locator(".eda-artifact-heading h3").inner_text().strip():
            raise AssertionError("Biểu đồ tương tác bị mất tiêu đề")
        if duc_gallery.locator("img").count() != 5:
            raise AssertionError("Trang Nhiệt độ chưa hiển thị đủ 5 biểu đồ tĩnh của Đức")
        if duc_gallery.locator("iframe").count() != 5:
            raise AssertionError("Trang Nhiệt độ chưa hiển thị đủ 5 biểu đồ tương tác của Đức")
        if page.locator("#page-content .js-plotly-plot").count() != 0:
            raise AssertionError("Trang Nhiệt độ còn biểu đồ dashboard không thuộc phần Đức")
        duc_gallery.locator(".eda-expand-button").first.click()
        page.locator("#eda-modal.open .eda-modal-frame").wait_for()
        page.locator("#close-eda-modal").click()
        page.wait_for_function(
            "() => !document.querySelector('#eda-modal').classList.contains('open')"
        )

        page.locator('a[href="#forecast"]').first.click()
        page.get_by_text("R² kiểm tra", exact=True).wait_for()
        page.get_by_text("Kết quả năm 2050", exact=True).wait_for()
        page.locator("#duc-forecast-gallery").wait_for()
        if page.locator("#duc-forecast-gallery img").count() != 1:
            raise AssertionError("Trang Dự báo thiếu biểu đồ hồi quy tĩnh tham khảo của Đức")
        if page.locator("#duc-forecast-gallery iframe").count() != 1:
            raise AssertionError("Trang Dự báo thiếu biểu đồ hồi quy tương tác tham khảo của Đức")
        page.screenshot(path="/tmp/climate_dashboard_desktop.png", full_page=True)

        page.set_viewport_size({"width": 390, "height": 844})
        page.goto(f"{BASE_URL}/#overview", wait_until="networkidle")
        page.locator("#page-title").wait_for(state="visible")
        page.wait_for_timeout(300)
        dimensions = page.evaluate(
            "() => ({width: innerWidth, scrollWidth: document.documentElement.scrollWidth})"
        )
        page.screenshot(path="/tmp/climate_dashboard_mobile.png", full_page=True)
        browser.close()

    if page_errors or console_errors:
        raise AssertionError({"page_errors": page_errors, "console_errors": console_errors})
    if dimensions["scrollWidth"] > dimensions["width"] + 2:
        raise AssertionError(f"Mobile bị tràn ngang: {dimensions}")

    result = {
        "pages": checked,
        "mobile": dimensions,
        "screenshots": [
            "/tmp/climate_dashboard_desktop.png",
            "/tmp/climate_dashboard_mobile.png",
        ],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
