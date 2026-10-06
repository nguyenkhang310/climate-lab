import json
import math
import sqlite3
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import numpy as np
from plotly.utils import PlotlyJSONEncoder

from bang_dieu_khien.nguyen_khang import ung_dung as app
from bang_dieu_khien.nguyen_khang.du_lieu import (
    BACKTEST_DATA,
    DATA,
    GLOBAL_DATA,
    MODEL_INFO,
    SCENARIO_DATA,
    SECTOR_DATA,
    aggregate,
    filter_data,
    filtered_months,
    filtered_sectors,
    sector_totals,
)
from mo_hinh_du_doan.nguyen_khang.ghep_du_lieu import build_country_year, build_global_year
from mo_hinh_du_doan.nguyen_khang.mo_hinh_nhiet_do import kich_ban

class ClimateDataTests(unittest.TestCase):
    def test_source_values_survive_join_and_every_filter(self):
        tables = {
            "duc/nhiet_do_quoc_gia.csv": ["temperature_anomaly"],
            "quan/co2_quoc_gia.csv": ["co2", "co2_per_capita", "population"],
            "quan/nang_luong_tai_tao.csv": ["renewable_percent"],
        }
        indexed = DATA.set_index(["iso_alpha", "year"])
        for path, fields in tables.items():
            source = pd.read_csv(app.ROOT / "data/du_lieu_da_xu_ly" / path).set_index(["iso_alpha", "year"])
            np.testing.assert_allclose(indexed[fields], source[fields].reindex(indexed.index), equal_nan=True)
        scopes = [("all", code) for code in DATA.iso_alpha.unique()]
        scopes += [(name, "all") for name in ["all"] + app.CONTINENTS]
        for years in ["1970-2024", "1990-2023", "2000-2024", "2015-2024"]:
            start, end = map(int, years.split("-"))
            for continent, country in scopes:
                mask = DATA.year.between(start, end)
                if continent != "all":
                    mask &= DATA.continent.eq(continent)
                if country != "all":
                    mask &= DATA.iso_alpha.eq(country)
                pd.testing.assert_frame_equal(filter_data(years, continent, country), DATA[mask])

    def test_dashboard_key_and_period(self):
        self.assertEqual(int(DATA.year.min()), 1970)
        self.assertEqual(int(DATA.year.max()), 2024)
        self.assertEqual(int(DATA.duplicated(["iso_alpha", "year"]).sum()), 0)
        self.assertGreaterEqual(DATA.iso_alpha.nunique(), 200)

    def test_global_aggregation_uses_official_world_series(self):
        frame = filter_data("1970-2024")
        result = aggregate(frame, use_global=True).set_index("year")
        official = GLOBAL_DATA.set_index("year")
        self.assertAlmostEqual(result.loc[2023, "co2"], official.loc[2023, "co2"])
        self.assertAlmostEqual(
            result.loc[2023, "temperature_anomaly"],
            official.loc[2023, "temperature_anomaly"],
        )

    def test_country_filter_keeps_real_annual_series(self):
        vietnam = filter_data("1970-2024", country="VNM")
        self.assertEqual(vietnam.iso_alpha.unique().tolist(), ["VNM"])
        self.assertEqual(vietnam.year.nunique(), 55)
        self.assertGreater(vietnam.co2.notna().sum(), 40)

    def test_dashboard_matches_current_member_cleaned_data(self):
        rebuilt, report = build_country_year()
        pd.testing.assert_frame_equal(
            DATA.reset_index(drop=True),
            rebuilt,
            check_dtype=False,
            check_exact=False,
            atol=1e-12,
        )
        self.assertEqual(report["countries_or_territories"], 244)

    def test_sqlite_join_matches_dashboard_data(self):
        database = Path("data/du_lieu_da_xu_ly/nguyen_khang/climate_lab.db")
        with sqlite3.connect(database) as connection:
            actual = pd.read_sql(
                "SELECT * FROM dashboard_quoc_gia_nam ORDER BY iso_alpha, year",
                connection,
            )
            self.assertFalse(connection.execute("PRAGMA foreign_key_check").fetchall())
            document = (app.ROOT / "tai_lieu/dung_chung/SO_DO_DU_LIEU.md").read_text(encoding="utf-8")
            query = document.split("```sql\n", 1)[1].split("```", 1)[0]
            documented = pd.read_sql(query, connection).sort_values(["iso_alpha", "year"]).reset_index(drop=True)
            pd.testing.assert_frame_equal(documented, actual)
        expected = DATA.sort_values(["iso_alpha", "year"]).reset_index(drop=True)
        pd.testing.assert_frame_equal(
            actual.convert_dtypes(), expected.convert_dtypes(), check_dtype=False
        )

    def test_country_summary_keeps_source_values_including_missing_values(self):
        fields = ["temperature_anomaly", "co2", "co2_per_capita", "population"]
        for code, frame in DATA.groupby("iso_alpha"):
            with self.subTest(country=code):
                actual = aggregate(frame).set_index("year")[fields]
                expected = frame.set_index("year")[fields]
                pd.testing.assert_frame_equal(actual, expected)

    def test_regional_per_capita_uses_paired_population_and_co2(self):
        frame = DATA[DATA.year == 2024].copy()
        frame.loc[frame.iso_alpha == "CHN", "co2"] = np.nan
        paired = frame.dropna(subset=["co2", "population"])
        paired = paired[paired.population > 0]
        expected = paired.co2.sum() * 1_000_000 / paired.population.sum()
        self.assertAlmostEqual(aggregate(frame).co2_per_capita.iloc[0], expected)


class ScenarioModelTests(unittest.TestCase):
    def test_custom_rates_and_prediction_intervals(self):
        for rate in (-1, -.1, 0, .05):
            frame = kich_ban(MODEL_INFO, rate)
            self.assertTrue(np.isfinite(frame.select_dtypes("number")).all().all())
            self.assertTrue((frame.lower_90 <= frame.temperature_prediction).all())
            self.assertTrue((frame.upper_90 >= frame.temperature_prediction).all())
        for rate in (np.nan, np.inf, -1.01):
            with self.assertRaises(ValueError):
                kich_ban(MODEL_INFO, rate)

    def test_global_model_input_matches_sources(self):
        pd.testing.assert_frame_equal(build_global_year(), GLOBAL_DATA, check_dtype=False)
        self.assertTrue(GLOBAL_DATA.year.diff().iloc[1:].eq(1).all())
        self.assertTrue(np.isfinite(GLOBAL_DATA[["co2", "cumulative_co2", "temperature_anomaly"]]).all().all())

    def test_backtest_was_fit_only_on_training_years(self):
        from sklearn.linear_model import LinearRegression
        from sklearn.metrics import r2_score, mean_absolute_error

        data = GLOBAL_DATA.assign(target=GLOBAL_DATA.temperature_anomaly.rolling(5).mean()).dropna(subset=["target"])
        train, test = data[data.year <= 2014], data[data.year > 2014]
        model = LinearRegression().fit(train[["cumulative_co2"]] / 1000, train.target)
        predicted = model.predict(test[["cumulative_co2"]] / 1000)
        np.testing.assert_allclose(predicted, BACKTEST_DATA.temperature_prediction)
        self.assertAlmostEqual(r2_score(test.target, predicted), MODEL_INFO["r2_test"])
        self.assertAlmostEqual(mean_absolute_error(test.target, predicted), MODEL_INFO["mae_test"])

    def test_custom_and_exported_scenarios_use_identical_math(self):
        for _, expected in SCENARIO_DATA.groupby("scenario_id"):
            actual = kich_ban(MODEL_INFO, expected.annual_change_pct.iloc[0] / 100)
            columns = ["year", "co2", "cumulative_co2", "temperature_prediction", "lower_90", "upper_90"]
            np.testing.assert_allclose(actual[columns], expected[columns], rtol=1e-12)
            np.testing.assert_allclose(actual.cumulative_co2, MODEL_INFO["last_cumulative_co2"] + actual.co2.cumsum())

    def test_selected_year_changes_chart_marker_and_kpis(self):
        result = app.update_scenario_page("decline", -5, 2030)
        self.assertTrue(result[3].startswith("2030"))
        self.assertIn("Thấp hơn", result[5])
        self.assertEqual(result[0].data[-1].x[0], 2030)
        self.assertTrue(any(shape.x0 == 2030 for shape in result[1].layout.shapes))

    def test_backtest_and_scenarios_are_complete(self):
        self.assertEqual(BACKTEST_DATA.year.tolist(), list(range(2015, 2025)))
        self.assertEqual(SCENARIO_DATA.scenario_id.nunique(), 3)
        self.assertTrue((SCENARIO_DATA.groupby("scenario_id").year.nunique() == 26).all())
        self.assertEqual(int(SCENARIO_DATA.year.min()), 2025)
        self.assertEqual(int(SCENARIO_DATA.year.max()), 2050)
        self.assertLess(MODEL_INFO["mae_test"], .1)

    def test_emission_choices_change_the_2050_result(self):
        year_2050 = SCENARIO_DATA[SCENARIO_DATA.year == 2050].set_index("scenario_id")
        self.assertLess(
            year_2050.loc["decline", "temperature_prediction"],
            year_2050.loc["trend", "temperature_prediction"],
        )
        custom = kich_ban(MODEL_INFO, -.10)
        self.assertTrue(custom.cumulative_co2.is_monotonic_increasing)
        self.assertGreater(custom.lower_90.min(), -1)

    def test_custom_scenario_callback_is_serializable(self):
        result = app.update_scenario_page("custom", -7.5, 2050)
        self.assertEqual(len(result), 9)
        self.assertEqual(len(result[-1]), 104)
        json.dumps(result, cls=PlotlyJSONEncoder)

class DashboardSmokeTests(unittest.TestCase):
    def test_wsgi_entrypoint(self):
        from app import app as wsgi_app

        self.assertIs(wsgi_app, app.server)
        self.assertEqual(wsgi_app.test_client().get("/").status_code, 200)

    def test_filter_change_during_navigation_builds_current_country(self):
        with patch.object(app, "ctx") as context:
            context.triggered_id = "country-filter"
            for route in ("overview", "earth"):
                result = app.render_page(f"#{route}", "1970-2024", "all", "VNM", "temperature")
                self.assertIn("Vietnam", self._component_text(result[0]))
                ready = app.render_page(f"#{route}", "1970-2024", "all", "VNM", "temperature",
                                        "overview-globe" if route == "overview" else None,
                                        "globe" if route == "earth" else None)
                self.assertIs(ready[0], app.no_update)

    def test_world_sector_chart_includes_all_edgar_codes(self):
        for year in (1970, 2023, 2024):
            frame = DATA[DATA.year == year]
            expected = SECTOR_DATA[SECTOR_DATA.year == year].co2.sum()
            self.assertAlmostEqual(sector_totals(frame, use_global=True).sum(), expected)

    def test_overview_and_insights_share_global_sector_percentages(self):
        frame = filter_data()
        overview = app.overview_comparison(frame, "all", 2024, "Toàn cầu")
        insights = app.create_insights_page(frame, aggregate(frame, use_global=True), "Toàn cầu")
        overview_plot = overview.children[1].children[1].figure
        insight_plot = insights[1].children[2].children[1].figure
        np.testing.assert_allclose(overview_plot.data[0].x, insight_plot.data[0].x)

    def test_trend_charts_do_not_hide_missing_years(self):
        frame = filter_data("2020-2024", country="VNM")
        frame.loc[frame.year == 2022, ["temperature_anomaly", "co2"]] = np.nan
        for create in (app.create_temperature_chart, app.create_co2_chart):
            trace = create(frame).data[0]
            self.assertEqual(list(trace.x), list(range(2020, 2025)))
            self.assertTrue(pd.isna(trace.y[2]))

    def test_all_observed_data_pages_share_filters_and_csv(self):
        for page, _, _ in app.MENU:
            result = app.render_page(f"#{page}", "1990-2023", "all", "VNM", "temperature")
            self.assertEqual(result[4], page == "scenario")
            self.assertEqual("hidden-filter" in result[8], page == "scenario")
            if page != "scenario":
                self.assertEqual(result[2], "Vietnam · 1990–2023")

    def test_sector_shares_follow_selected_country_and_year(self):
        frame = filter_data("2000-2023", country="VNM")
        totals = sector_totals(frame)
        source = SECTOR_DATA[(SECTOR_DATA.iso_alpha == "VNM") & (SECTOR_DATA.year == 2023)]
        self.assertAlmostEqual(totals.sum(), source.co2.sum())
        figure = app.create_sector_chart(totals)
        self.assertAlmostEqual(sum(figure.data[0].x), 100)
        self.assertEqual(figure.data[0].y[-1], totals.index[0])

    def test_insights_handle_missing_and_single_year_data(self):
        for country in ("VNM", "ESH", "ATA"):
            frame = filter_data("2024-2024", country=country)
            content = app.create_insights_page(frame, aggregate(frame), country)
            text = self._component_text(content)
            self.assertIn("Chưa đủ dữ liệu nhiệt độ", text)
            self.assertIn("Chưa đủ dữ liệu CO₂", text)
            self.assertNotIn("nan", text.lower())
            json.dumps(content, cls=PlotlyJSONEncoder)

    def test_insights_use_complete_calendar_windows_and_actual_co2_years(self):
        frame = filter_data("1970-2024", country="VNM")
        series = aggregate(frame)
        content = app.create_insights_page(frame, series, "Vietnam")
        first = series[series.year.between(1970, 1974)].temperature_anomaly.mean()
        last = series[series.year.between(2020, 2024)].temperature_anomaly.mean()
        self.assertEqual(content[1].children[0].children[0].children[1].children, f"{last-first:+.2f} °C")
        series.loc[series.year.eq(1970), "temperature_anomaly"] = np.nan
        series.loc[series.year.eq(2024), "co2"] = np.nan
        text = self._component_text(app.create_insights_page(frame, series, "Vietnam"))
        self.assertIn("Chưa đủ dữ liệu nhiệt độ", text)
        self.assertIn("2023:", text)

    def test_co2_industry_area_and_treemap_use_same_filtered_totals(self):
        frame = filter_data("2015-2024", "Asia", "VNM")
        content = app.render_page("#co2", "2015-2024", "Asia", "VNM", "co2")[0].children
        cards = content.children[0].children[1].children
        area = cards[3].children[1].figure
        tree = cards[4].children[1].figure
        totals = sector_totals(frame)
        self.assertAlmostEqual(sum(trace.y[-1] for trace in area.data), totals.sum())
        self.assertAlmostEqual(sum(tree.data[0].values), totals.sum())
        self.assertAlmostEqual(sum(row[0] for row in tree.data[0].customdata), 100)

    def test_all_pages_build(self):
        self.assertEqual(set(app.PAGE_INFO), {page for page, _, _ in app.MENU})
        for page, _, _ in app.MENU:
            with self.subTest(page=page):
                result = app.render_page(
                    f"#{page}", "1970-2024", "all", "all",
                    "temperature",
                )
                self.assertEqual(len(result), 9)

    def test_scenario_page_has_controls_charts_and_download(self):
        content = app.render_page(
            "#scenario", "1970-2024", "all", "all",
            "temperature",
        )[0]
        ids = self._component_ids(content)
        self.assertTrue({
            "scenario-choice", "scenario-rate", "scenario-year",
            "scenario-temperature-chart", "scenario-co2-chart",
            "scenario-backtest-chart",
            "download-scenarios-button",
        }.issubset(ids))

    def test_member_eda_galleries_are_attached_to_expected_pages(self):
        expected = {
            "temperature": "duc-eda-gallery",
            "co2": "quan-eda-gallery",
        }
        for page, gallery_id in expected.items():
            with self.subTest(page=page):
                content = app.render_page(
                    f"#{page}", "1970-2024", "all", "all",
                    "temperature",
                )[0]
                self.assertIn(gallery_id, self._component_ids(content))

    def test_member_pages_only_show_declared_member_artifacts(self):
        for page in ("temperature", "co2"):
            with self.subTest(page=page):
                content = app.render_page(
                    f"#{page}", "1970-2024", "all", "all",
                    "temperature",
                )[0]
                self.assertEqual(self._component_types(content).count("Graph"), 6)
                self.assertNotIn("Iframe", self._component_types(content))
                text = self._component_text(content)
                self.assertIn("Biểu đồ tĩnh", text)
                self.assertIn("Biểu đồ tương tác", text)
                self.assertLess(text.index("Biểu đồ tương tác"), text.index("Biểu đồ tĩnh"))

        gallery = app.render_page("#temperature", "1970-2024", "all", "all", "temperature")[0].children
        interactive_section = gallery.children[0]
        self.assertIn("interactive", interactive_section.className)
        self.assertIn("interactive", interactive_section.children[1].className)

    def test_member_charts_use_filtered_source_values(self):
        for continent, country in [("all", "all"), ("Asia", "all"), ("Asia", "VNM")]:
            frame = filter_data("2015-2024", continent, country)
            series = aggregate(frame, use_global=continent == country == "all")
            for page, field in [("temperature", "temperature_anomaly"), ("co2", "co2")]:
                content = app.render_page(f"#{page}", "2015-2024", continent, country, "temperature")[0].children
                cards = content.children[0].children[1].children
                figure = cards[0].children[1].figure
                np.testing.assert_array_equal(figure.data[0].x, series.year)
                np.testing.assert_allclose(figure.data[0].y, series[field], equal_nan=True)
                map_trace = cards[2].children[1].figure.data[0]
                expected = frame[frame.year.eq(2024)].dropna(subset=[field if page == "temperature" else "co2_per_capita"])
                self.assertEqual(set(map_trace.locations), set(expected.iso_alpha))

    def test_country_options_follow_continent_and_keep_valid_selection(self):
        options, value = app.update_country_options("Asia", "2015-2024", "USA")
        self.assertEqual(value, "all")
        self.assertNotIn("USA", {option["value"] for option in options})
        self.assertEqual(app.update_country_options("Asia", "2015-2024", "VNM")[1], "VNM")

    def test_member_pages_handle_missing_and_single_year_data(self):
        for page in ("temperature", "co2"):
            for country in ("VNM", "ESH", "ATA"):
                content = app.render_page(f"#{page}", "2024-2024", "all", country, "temperature")[0]
                json.dumps(content, cls=PlotlyJSONEncoder)
                self.assertNotIn("nan", self._component_text(content).lower())

    @staticmethod
    def _component_ids(component):
        ids = set()
        if isinstance(component, (list, tuple)):
            for child in component:
                ids.update(DashboardSmokeTests._component_ids(child))
            return ids
        component_id = getattr(component, "id", None)
        if isinstance(component_id, str):
            ids.add(component_id)
        children = getattr(component, "children", None)
        if children is not None:
            ids.update(DashboardSmokeTests._component_ids(children))
        return ids

    @staticmethod
    def _component_types(component):
        if isinstance(component, (list, tuple)):
            return sum(
                (DashboardSmokeTests._component_types(child) for child in component),
                [],
            )
        types = [component.__class__.__name__]
        children = getattr(component, "children", None)
        if children is not None:
            types += DashboardSmokeTests._component_types(children)
        return types

    @staticmethod
    def _component_text(component):
        if isinstance(component, str):
            return component
        if isinstance(component, (list, tuple)):
            return " ".join(DashboardSmokeTests._component_text(child) for child in component)
        return DashboardSmokeTests._component_text(getattr(component, "children", []))


class MemberEdaTests(unittest.TestCase):
    def test_all_twelve_charts_match_each_filtered_table(self):
        scopes = [("all", "all"), ("Asia", "all"), ("Europe", "all"),
                  ("all", "VNM"), ("all", "ESH"), ("all", "ATA")]
        for years in ["1970-2024", "1990-2023", "2000-2024", "2015-2024", "2024-2024"]:
            for continent, country in scopes:
                with self.subTest(years=years, continent=continent, country=country):
                    frame = filter_data(years, continent, country)
                    series = aggregate(frame, continent == country == "all")
                    monthly = filtered_months(frame, continent == country == "all")
                    temperature = list(app.temperature_figures(series, frame, monthly).values())
                    sectors = filtered_sectors(frame, continent == country == "all")
                    co2 = list(app.co2_figures(series, frame, sectors).values())
                    valid = frame.dropna(subset=["temperature_anomaly"]).assign(decade=lambda d: (d.year // 10 * 10).astype(str))
                    latest = frame[frame.year.eq(series.year.max())]
                    np.testing.assert_allclose(temperature[0].data[0].y, series.temperature_anomaly, equal_nan=True)
                    np.testing.assert_allclose(temperature[0].data[1].y, series.temperature_anomaly.rolling(5).mean(), equal_nan=True)
                    decades = series.groupby(series.year // 10 * 10).temperature_anomaly.mean()
                    np.testing.assert_allclose(temperature[1].data[0].y, decades, equal_nan=True)
                    temp_latest = latest.dropna(subset=["temperature_anomaly"])
                    self.assertEqual(dict(zip(temperature[2].data[0].locations, temperature[2].data[0].z)),
                                     temp_latest.set_index("iso_alpha").temperature_anomaly.to_dict())
                    pivot = valid.pivot_table(index="continent", columns="decade", values="temperature_anomaly")
                    if not pivot.empty:
                        np.testing.assert_allclose(temperature[3].data[0].z, pivot, equal_nan=True)
                    for trace in temperature[4].data:
                        np.testing.assert_allclose(trace.y, valid[valid.decade.eq(trace.name)].temperature_anomaly)
                    expected = monthly.groupby(["year", "month"]).temperature_anomaly.mean().groupby("month")
                    np.testing.assert_array_equal(temperature[5].data[0].x, range(1, 13))
                    np.testing.assert_allclose(temperature[5].data[0].y, expected.mean().reindex(range(1, 13)), equal_nan=True)
                    np.testing.assert_allclose(temperature[5].data[0].customdata, expected.count().reindex(range(1, 13)), equal_nan=True)
                    np.testing.assert_allclose(co2[0].data[0].y, series.co2, equal_nan=True)
                    top = latest.dropna(subset=["co2"]).nlargest(15, "co2")
                    actual = {name: value for trace in co2[1].data for name, value in zip(trace.y, trace.x)}
                    self.assertEqual(actual, top.set_index("country").co2.to_dict())
                    pc = latest.dropna(subset=["co2_per_capita"])
                    self.assertEqual(dict(zip(co2[2].data[0].locations, co2[2].data[0].z)), pc.set_index("iso_alpha").co2_per_capita.to_dict())
                    totals = sectors.groupby(["sector", "year"]).co2.sum(min_count=1)
                    for trace in co2[3].data:
                        np.testing.assert_allclose(trace.y, totals.loc[trace.name].reindex(trace.x), equal_nan=True)
                    tree = sectors[sectors.year.eq(series.year.max())].groupby("sector").co2.sum(min_count=1)
                    tree = tree[tree > 0]
                    if not tree.empty:
                        trace = co2[4].data[0]
                        np.testing.assert_allclose(trace.values, tree.reindex(trace.labels))
                        np.testing.assert_allclose(np.asarray(trace.customdata, dtype=float)[:, 0], tree.reindex(trace.labels) / tree.sum() * 100)
                    paired = latest.dropna(subset=["co2_per_capita", "renewable_percent"])
                    actual = {name: (x, y) for trace in co2[5].data for name, x, y in zip(trace.hovertext, trace.x, trace.y)}
                    expected = {row.country: (row.renewable_percent, row.co2_per_capita) for row in paired.itertuples()}
                    self.assertEqual(actual, expected)

    def test_sector_colors_do_not_change_with_filters(self):
        from phan_tich_co2.quan.tao_bieu_do_plotly import SECTOR_COLORS

        frame = filter_data("2015-2024", country="VNM")
        sectors = filtered_sectors(frame)
        selected = sectors[sectors.sector.eq("Giao thông")]
        for data in (sectors, selected):
            figure = app.co2_figures(aggregate(frame), frame, data)["04_stacked_area_nganh"]
            for trace in figure.data:
                self.assertEqual(trace.line.color, SECTOR_COLORS[trace.name])

    def test_new_duc_plotly_files_are_listed(self):
        interactive = [
            path for _, _, path in app.DUC_TEMPERATURE_ARTIFACTS
            if path.endswith(".html")
        ]
        self.assertEqual(len(interactive), 6)
        self.assertEqual(
            [Path(path).name[:2] for path in interactive],
            ["01", "02", "03", "04", "05", "06"],
        )

    def test_monthly_temperature_keeps_missing_values_and_equal_year_weights(self):
        frame = filter_data("2020-2021", country="VNM")
        monthly = pd.DataFrame({"year": [2020, 2020, 2021, 2020], "month": [1, 1, 1, 2],
                                "temperature_anomaly": [0, 2, 4, np.nan]})
        figure = app.temperature_figures(aggregate(frame), frame, monthly)["06_nhiet_do_theo_thang"]
        self.assertEqual(figure.data[0].y[0], 2.5)
        self.assertEqual(figure.data[0].customdata[0], 2)
        self.assertTrue(np.isnan(figure.data[0].y[1:]).all())
        self.assertFalse(figure.data[0].connectgaps)
        page = app.render_page("#temperature", "2024-2024", "all", "VNM", "temperature")[0]
        figure = page.children.children[0].children[1].children[-1].children[1].figure
        self.assertEqual(len(figure.data[0].y), 12)
        self.assertTrue(np.isfinite(figure.data[0].y).all())
        np.testing.assert_array_equal(figure.data[0].customdata, np.ones(12))

    def test_all_declared_eda_files_exist_and_are_served(self):
        artifacts = (
            app.DUC_TEMPERATURE_ARTIFACTS
            + app.QUAN_ARTIFACTS
        )
        client = app.server.test_client()
        for _, _, relative_path in artifacts:
            with self.subTest(path=relative_path):
                member, filename = relative_path.split("/", 1)
                self.assertTrue((app.EDA_ROOT[member] / filename).is_file())
                response = client.get(f"/eda-files/{relative_path}")
                self.assertEqual(response.status_code, 200)
                expected_mimetype = (
                    "text/html" if relative_path.endswith(".html") else "image/png"
                )
                self.assertEqual(response.mimetype, expected_mimetype)
                response.close()
        self.assertEqual(client.get("/eda-files/../app.py").status_code, 404)

    def test_quan_growth_has_no_infinite_values(self):
        frame = pd.read_csv(app.ROOT / "data/du_lieu_da_xu_ly/quan/co2_quoc_gia.csv")
        finite = frame["co2_growth_pct"].dropna().map(math.isfinite)
        self.assertTrue(finite.all())
        self.assertEqual(int((frame["co2"] < 0).sum()), 0)
        consecutive = frame.groupby("iso_alpha").year.diff().eq(1)
        self.assertTrue(frame.loc[~consecutive, "co2_growth_pct"].isna().all())

    def test_expand_and_close_eda_modal(self):
        cases = [
            ("duc/tuong_tac/01_xu_huong_nhiet_do_toan_cau.html", "Graph"),
            ("duc/tinh/01_xu_huong_nhiet_do_toan_cau.png", "Img"),
        ]
        for path, component_type in cases:
            with self.subTest(path=path):
                opened = self._modal_callback(path)
                self.assertEqual(opened["eda-modal"]["className"], "eda-modal open")
                modal_children = opened["eda-modal-content"]["children"]
                self.assertEqual(modal_children[1]["type"], component_type)
                if component_type == "Img":
                    self.assertEqual(modal_children[1]["props"]["src"], f"/eda-files/{path}")
                else:
                    expected = filter_data("2015-2024", country="VNM").temperature_anomaly.to_numpy()
                    actual = modal_children[1]["props"]["figure"]["data"][0]["y"]
                    if isinstance(actual, dict):
                        actual = np.frombuffer(app.base64.b64decode(actual["bdata"]), dtype=actual["dtype"])
                    np.testing.assert_allclose(actual, expected)

        closed = self._modal_callback(cases[0][0], close=True)
        self.assertEqual(closed["eda-modal"]["className"], "eda-modal")
        self.assertIsNone(closed["eda-modal-content"]["children"])

    @staticmethod
    def _modal_callback(path, close=False):
        output = next(key for key in app.app.callback_map if "eda-modal.className" in key)
        callback = app.app.callback_map[output]
        pattern = callback["inputs"][0]["id"]
        frame = filter_data("2015-2024", country="VNM")
        figure = app.temperature_figures(aggregate(frame), frame, filtered_months(frame))["01_xu_huong_nhiet_do_toan_cau"]
        trigger = "close-eda-modal.n_clicks" if close else (
            json.dumps({"path": path, "type": "expand-eda"}, separators=(",", ":"), sort_keys=True)
            + ".n_clicks"
        )
        payload = {
            "output": output,
            "outputs": [
                {"id": "eda-modal", "property": "className"},
                {"id": "eda-modal-content", "property": "children"},
            ],
            "inputs": [
                {"id": pattern, "property": "n_clicks", "value": [1]},
                {"id": "close-eda-modal", "property": "n_clicks", "value": int(close)},
                {"id": "url", "property": "hash", "value": "#temperature"},
                {"id": "year-range", "property": "value", "value": "2015-2024"},
                {"id": "continent-filter", "property": "value", "value": "all"},
                {"id": "country-filter", "property": "value", "value": "VNM"},
            ],
            "state": [
                {**callback["state"][0], "value": [json.loads(figure.to_json())]},
                {**callback["state"][1], "value": [{"type": "eda-chart", "path": path}]},
                {**callback["state"][2], "value": "Vietnam · 2015–2024"},
            ],
            "changedPropIds": [trigger],
        }
        response = app.server.test_client().post("/_dash-update-component", json=payload)
        if response.status_code != 200:
            raise AssertionError(response.get_data(as_text=True))
        return response.get_json()["response"]


class EarthInteractionTests(unittest.TestCase):
    def test_earth_layout_is_focused_and_handles_missing_values(self):
        frame = filter_data("1970-2024")
        for country in ("all", "VNM", "ESH", "ATA"):
            content = app.create_earth(frame, country, "co2", app.scope_name("all", country))
            self.assertEqual(DashboardSmokeTests._component_types(content).count("Graph"), 3)
            text = DashboardSmokeTests._component_text(content)
            self.assertIn("triệu tấn", text)
            self.assertNotIn("nan", text.lower())
            self.assertNotIn("Tỷ trọng", text)

    def test_map_color_range_does_not_hide_extreme_values(self):
        for metric in ("temperature", "co2"):
            figure = app.create_globe(DATA[DATA.year == 2024], metric=metric)
            trace = next(t for t in figure.data if t.showscale)
            self.assertLessEqual(trace.zmin, min(trace.z))
            self.assertGreaterEqual(trace.zmax, max(trace.z))
            self.assertEqual(len(trace.customdata[0]), 2)

    def test_temperature_colors_stay_consistent_between_years(self):
        palettes = []
        for year in (1970, 2000, 2024):
            figure = app.create_globe(DATA[DATA.year == year])
            trace = next(t for t in figure.data if t.showscale)
            self.assertEqual((trace.zmin, trace.zmax), (-6, 6))
            self.assertIn((8 / 12, "#E65C36"), trace.colorscale)
            palettes.append(trace.colorscale)
        self.assertEqual(palettes[0], palettes[1])
        self.assertEqual(palettes[1], palettes[2])

    def test_year_changes_after_polar_rotation_keep_world_bounds(self):
        for lat in (95, 214.963, -215):
            rotation = {"lon": -255, "lat": lat, "roll": 0}
            initial = app.create_globe(DATA[DATA.year == 2024], rotation=rotation)
            changed = app.update_map(DATA[DATA.year == 1970], "VNM", "temperature",
                                     "globe", 0, initial.to_plotly_json())
            geo = changed.layout.geo
            self.assertEqual(geo.projection.rotation.to_plotly_json(), rotation)
            self.assertEqual(geo.center.to_plotly_json(), {"lon": -255, "lat": lat})
            self.assertEqual(tuple(geo.lonaxis.range), (-180, 180))
            self.assertEqual(tuple(geo.lataxis.range), (-90, 90))

    def test_metric_and_year_changes_keep_selected_country_and_camera(self):
        figure = app.create_globe(DATA[DATA.year == 2024], "ARG", rotation={"lon": -64, "lat": -34})
        figure = json.loads(figure.to_json())
        for changed in ("metric-filter.value", "year-range.value"):
            result = self._earth_callback(figure, "ARG", changed, metric="co2", years="1990-2023")
            layout = result["globe"]["figure"]["layout"]
            self.assertEqual(layout["meta"]["selected"], "ARG")
            self.assertEqual(layout["geo"]["projection"]["rotation"], {"lon": -64, "lat": -34})
            if changed == "metric-filter.value":
                self.assertNotIn("country-panel", result)
                self.assertNotIn("earth-lower", result)

    def test_map_has_local_geometry_white_card_and_blue_ocean(self):
        with app.server.test_client().get("/assets/world_110m.json") as response:
            self.assertEqual(response.status_code, 200)
            self.assertIn("countries", response.get_json()["objects"])
        figure = app.create_globe(DATA[DATA.year == 2024])
        self.assertEqual(figure.layout.paper_bgcolor, "white")
        self.assertEqual(figure.layout.geo.oceancolor, "#163E5C")
        self.assertEqual(app.graph(figure, globe=True).config["topojsonURL"], "/assets/")

    def test_globe_keeps_every_cleaned_country_clickable(self):
        snapshot = DATA[DATA.year == DATA.year.max()]
        for metric in ("temperature", "co2"):
            with self.subTest(metric=metric):
                figure = app.create_globe(snapshot, "VNM", metric)
                field = "co2" if metric == "co2" else "temperature_anomaly"
                locations = {
                    iso
                    for trace in figure.data if trace.type == "choropleth"
                    for iso in trace.locations
                }
                self.assertEqual(locations, set(snapshot.iso_alpha))
                self.assertEqual(figure.layout.meta["selected"], "VNM")

                data_trace = next(trace for trace in figure.data if trace.name != "Chưa có dữ liệu")
                mapped = dict(zip(data_trace.locations, data_trace.z))
                expected = snapshot.dropna(subset=[field]).set_index("iso_alpha")[field]
                self.assertEqual(set(mapped), set(expected.index))
                for iso, value in expected.items():
                    self.assertAlmostEqual(float(mapped[iso]), float(value))

                missing_trace = next(trace for trace in figure.data if trace.name == "Chưa có dữ liệu")
                expected_missing = set(snapshot.loc[snapshot[field].isna(), "iso_alpha"])
                self.assertEqual(set(missing_trace.locations), expected_missing)

    def test_country_click_accepts_map_location_and_custom_data(self):
        available = {"VNM", "USA"}
        self.assertEqual(
            app.country_from_click({"points": [{"location": "VNM"}]}, available),
            "VNM",
        )
        self.assertEqual(
            app.country_from_click({"points": [{"customdata": ["USA", 2024]}]}, available),
            "USA",
        )
        self.assertIsNone(
            app.country_from_click({"points": [{"location": "FRA"}]}, available)
        )

    def test_click_view_switch_and_reset_callbacks(self):
        frame = filter_data("1970-2024")
        figure = app.create_globe(
            frame[frame.year == frame.year.max()], "VNM", "temperature"
        ).to_plotly_json()
        figure = json.loads(json.dumps(figure, cls=PlotlyJSONEncoder))

        clicked = self._earth_callback(
            figure, "ABW", "country-filter.value"
        )
        self.assertEqual(clicked["globe"]["figure"]["layout"]["meta"]["selected"], "ABW")

        switched = self._earth_callback(
            clicked["globe"]["figure"], "ABW", "earth-map-view.value",
            map_view="flat",
        )
        self.assertNotIn("country-panel", switched)
        self.assertNotIn("earth-lower", switched)
        self.assertEqual(switched["globe"]["figure"]["layout"]["meta"]["selected"], "ABW")
        self.assertEqual(
            switched["globe"]["figure"]["layout"]["geo"]["projection"]["type"],
            "natural earth",
        )

        reset = self._earth_callback(
            switched["globe"]["figure"], "ABW", "reset-globe.n_clicks",
            map_view="flat", resets=1,
        )
        self.assertEqual(reset["globe"]["figure"]["layout"]["meta"]["selected"], "ABW")

    def test_selection_does_not_reset_rotation_or_revision(self):
        snapshot = DATA[DATA.year == 2024]
        initial = app.create_globe(snapshot, "VNM").to_plotly_json()
        initial["layout"]["geo"]["projection"]["rotation"] = {"lon": 60, "lat": 30}
        selected = app.update_map(snapshot, "CHN", "temperature", "globe", 0, initial)
        self.assertEqual(selected.layout.geo.projection.rotation.lon, 60)
        self.assertEqual(selected.layout.geo.projection.rotation.lat, 30)
        self.assertEqual(selected.layout.geo.uirevision, initial["layout"]["geo"]["uirevision"])
        trace = next(t for t in selected.data if "CHN" in t.locations)
        index = list(trace.locations).index("CHN")
        self.assertEqual(trace.marker.line.color[index], "#FFD54A")
        self.assertEqual(trace.marker.line.width[index], 3)

    def test_flat_pan_does_not_leak_into_globe(self):
        snapshot = DATA[DATA.year == 2024]
        initial = app.create_globe(snapshot, rotation={"lon": 72, "lat": 26}).to_plotly_json()
        flat = app.update_map(snapshot, "CHN", "temperature", "flat", 0, initial).to_plotly_json()
        self.assertEqual(flat["layout"]["geo"]["lonaxis"]["range"], [-180, 180])
        flat["layout"]["geo"]["center"] = {"lon": -45, "lat": 50}
        flat["layout"]["geo"]["projection"].update(rotation={"lon": -45}, scale=2)
        globe = app.update_map(snapshot, "CHN", "temperature", "globe", 0, flat)
        self.assertEqual(globe.layout.geo.projection.rotation.lon, 72)
        self.assertEqual(globe.layout.geo.projection.rotation.lat, 26)
        self.assertEqual(globe.layout.geo.projection.scale, 1)
        self.assertEqual(tuple(globe.layout.geo.lonaxis.range), (-180, 180))
        self.assertEqual(tuple(globe.layout.geo.lataxis.range), (-90, 90))
        self.assertEqual(globe.layout.geo.center.to_plotly_json(), {"lon": 72, "lat": 26})
        again = app.update_map(snapshot, "CHN", "temperature", "flat", 0, globe.to_plotly_json())
        self.assertEqual(again.layout.meta["globe_rotation"]["lon"], 72)
        reset = app.update_map(snapshot, "CHN", "temperature", "globe", 1, globe.to_plotly_json(), reset=True)
        self.assertEqual(reset.layout.geo.projection.rotation.lon, 105)
        self.assertEqual(reset.layout.meta["selected"], "CHN")

    @staticmethod
    def _earth_callback(
        figure, selected, changed, map_view="globe", resets=0, metric="temperature", years="1970-2024",
    ):
        output = next(
            key for key in app.app.callback_map if "country-panel.children" in key
        )
        payload = {
            "output": output,
            "outputs": [
                {"id": "country-panel", "property": "children"},
                {"id": "earth-lower", "property": "children"},
                {"id": "globe", "property": "figure"},
            ],
            "inputs": [
                {"id": "country-filter", "property": "value", "value": selected},
                {"id": "metric-filter", "property": "value", "value": metric},
                {"id": "year-range", "property": "value", "value": years},
                {"id": "continent-filter", "property": "value", "value": "all"},
                {"id": "reset-globe", "property": "n_clicks", "value": resets},
                {"id": "earth-map-view", "property": "value", "value": map_view},
            ],
            "state": [
                {"id": "globe", "property": "figure", "value": figure},
                {"id": "url", "property": "hash", "value": "#earth"},
            ],
            "changedPropIds": [changed],
        }
        response = app.server.test_client().post("/_dash-update-component", json=payload)
        if response.status_code != 200:
            raise AssertionError(response.get_data(as_text=True))
        return response.get_json()["response"]

if __name__ == "__main__":
    unittest.main()
