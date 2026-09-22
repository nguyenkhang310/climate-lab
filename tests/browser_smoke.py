from __future__ import annotations

import json

from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:8050"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PAGES = {
    "overview": "Tổng quan khí hậu",
    "earth": "Bản đồ khí hậu",
    "temperature": "Nhiệt độ",
    "co2": "Khí thải CO₂",
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
        page.get_by_text("Bộ dữ liệu khí hậu đã làm sạch", exact=True).wait_for()
        with page.expect_download() as download_info:
            page.locator("#export-data").click()
        download = download_info.value
        export_path = download.path()
        export_header = open(export_path, encoding="utf-8").readline().strip()
        if "temperature_anomaly" not in export_header or "co2" not in export_header:
            raise AssertionError(f"CSV xuất thiếu cột: {export_header}")
        checked["export"] = {"filename": download.suggested_filename}

        page.locator('a[href="#co2"]').first.click()
        page.get_by_text("Cơ cấu phát thải theo ngành", exact=True).wait_for()
        page.get_by_text("Năng lượng tái tạo và CO₂/người", exact=True).wait_for()

        page.locator('a[href="#forecast"]').first.click()
        page.get_by_text("R² kiểm tra", exact=True).wait_for()
        page.get_by_text("Kết quả tại năm 2050", exact=True).wait_for()
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
