import json
import math
import sqlite3
import unittest
from contextlib import closing
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pandas as pd
import numpy as np
from plotly.utils import PlotlyJSONEncoder

from bang_dieu_khien.nguyen_khang import ung_dung as app
from bang_dieu_khien.nguyen_khang.du_lieu import (
    BACKTEST_DATA,
    DATA,
    GLOBAL_DATA,
    GLOBAL_CO2,
    GLOBAL_TEMPERATURE,
    MODEL_INFO,
    RESIDUAL_DATA,
    SCENARIO_DATA,
    SECTOR_DATA,
    tong_hop_du_lieu,
    loc_du_lieu,
    loc_du_lieu_thang,
    loc_du_lieu_nganh,
    tong_co2_theo_nganh,
    chuoi_nhiet_do,
)
from mo_hinh_du_doan.nguyen_khang.ghep_du_lieu import build_country_year, build_global_year
from mo_hinh_du_doan.nguyen_khang.mo_hinh_nhiet_do import tao_kich_ban

def current_filters(continent, years, country, route="#overview", **clicks):
    return app.cap_nhat_bo_loc(route, years, continent, country, "temperature",
                              saved={"page": route}, **clicks)

class ClimateDataTests(unittest.TestCase):
    def test_territories_have_continents_from_reference(self):
        expected = {"ATF": "Africa", "SJM": "Europe", "BLM": "North America",
                    "MAF": "North America", "GUM": "Oceania", "MNP": "Oceania"}
        self.assertFalse(DATA.continent.isna().any())
        for code, continent in expected.items():
            self.assertEqual(DATA.loc[DATA.iso_alpha.eq(code), "continent"].unique().tolist(), [continent])
            result = current_filters(continent, "1970-2024", code)
            options, selected = result[4:6]
            self.assertEqual(selected, code)
            self.assertIn(code, [option["value"] for option in options])

    def test_source_values_survive_join_and_every_filter(self):
        tables = {
            "duc/nhiet_do_quoc_gia_nam_lich.csv": ["temperature_anomaly"],
            "quan/co2_quoc_gia.csv": ["co2", "co2_per_capita", "population"],
            "quan/nang_luong_tai_tao.csv": ["renewable_percent"],
        }
        indexed = DATA.set_index(["iso_alpha", "year"])
        for path, fields in tables.items():
            source = pd.read_csv(app.ROOT / "data/du_lieu_da_xu_ly" / path).set_index(["iso_alpha", "year"])
            np.testing.assert_allclose(indexed[fields], source[fields].reindex(indexed.index), equal_nan=True)
        scopes = [("all", code) for code in DATA.iso_alpha.unique()]
        scopes += [(name, "all") for name in ["all"] + app.CONTINENTS]
        for years in ["1970-2024", "1970-1979", "1980-1989", "1990-1999",
                      "2000-2009", "2010-2019", "2020-2024"]:
            start, end = map(int, years.split("-"))
            for continent, country in scopes:
                mask = DATA.year.between(start, end)
                if continent != "all":
                    mask &= DATA.continent.eq(continent)
                if country != "all":
                    mask &= DATA.iso_alpha.eq(country)
                pd.testing.assert_frame_equal(loc_du_lieu(years, continent, country), DATA[mask])

    def test_dashboard_key_and_period(self):
        self.assertEqual(int(DATA.year.min()), 1850)
        self.assertEqual(int(DATA.year.max()), 2024)
        self.assertEqual(int(DATA.duplicated(["iso_alpha", "year"]).sum()), 0)
        self.assertGreaterEqual(DATA.iso_alpha.nunique(), 200)

    def test_global_aggregation_uses_official_world_series(self):
        frame = loc_du_lieu("1970-2024")
        result = tong_hop_du_lieu(frame, use_global=True).set_index("year")
        official = GLOBAL_DATA.set_index("year")
        self.assertAlmostEqual(result.loc[2023, "co2"], official.loc[2023, "co2"])
        self.assertAlmostEqual(
            result.loc[2023, "temperature_anomaly"],
            official.loc[2023, "temperature_anomaly"],
        )

    def test_country_filter_keeps_real_annual_series(self):
        vietnam = loc_du_lieu("1970-2024", country="VNM")
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
        with closing(sqlite3.connect(database)) as connection:
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

    def test_rebuilding_sqlite_preserves_all_tables_and_views(self):
        from mo_hinh_du_doan.nguyen_khang import tao_co_so_du_lieu as database

        saved = database.DB
        with TemporaryDirectory() as folder, patch.object(database, "DB", Path(folder) / "climate_lab.db"):
            database.main()
            with closing(sqlite3.connect(saved)) as old, closing(sqlite3.connect(database.DB)) as new:
                self.assertFalse(new.execute("PRAGMA foreign_key_check").fetchall())
                tables = old.execute("SELECT name FROM sqlite_master WHERE type IN ('table', 'view')").fetchall()
                for (name,) in tables:
                    expected = pd.read_sql(f'SELECT * FROM "{name}"', old)
                    actual = pd.read_sql(f'SELECT * FROM "{name}"', new)
                    columns = expected.columns.tolist()
                    pd.testing.assert_frame_equal(
                        actual.sort_values(columns).reset_index(drop=True),
                        expected.sort_values(columns).reset_index(drop=True))

    def test_country_summary_keeps_source_values_including_missing_values(self):
        fields = ["temperature_anomaly", "co2", "co2_per_capita", "population"]
        for code, frame in DATA.groupby("iso_alpha"):
            with self.subTest(country=code):
                actual = tong_hop_du_lieu(frame).set_index("year")[fields]
                expected = frame.set_index("year")[fields]
                pd.testing.assert_frame_equal(actual, expected)

    def test_regional_per_capita_uses_paired_population_and_co2(self):
        frame = DATA[DATA.year == 2024].copy()
        frame.loc[frame.iso_alpha == "CHN", "co2"] = np.nan
        paired = frame.dropna(subset=["co2", "population"])
        paired = paired[paired.population > 0]
        expected = paired.co2.sum() * 1_000_000 / paired.population.sum()
        self.assertAlmostEqual(tong_hop_du_lieu(frame).co2_per_capita.iloc[0], expected)


class ScenarioModelTests(unittest.TestCase):
    def test_training_reproduces_all_saved_results(self):
        from mo_hinh_du_doan.nguyen_khang import mo_hinh_nhiet_do as model

        with TemporaryDirectory() as folder, patch.object(model, "OUTPUT", Path(folder)):
            model.chay_mo_hinh()
            actual_info = json.loads((Path(folder) / "thong_tin_mo_hinh.json").read_text(encoding="utf-8"))
            self.assertEqual(actual_info.keys(), MODEL_INFO.keys())
            for key, expected in MODEL_INFO.items():
                with self.subTest(field=key):
                    if isinstance(expected, float) or key in {"bootstrap_x", "bootstrap_residuals"}:
                        np.testing.assert_allclose(actual_info[key], expected, rtol=1e-12, atol=1e-12)
                    else:
                        self.assertEqual(actual_info[key], expected)
            for name, expected in [
                ("du_doan_kiem_tra", BACKTEST_DATA), ("kich_ban_2050", SCENARIO_DATA),
                ("phan_du_huan_luyen", RESIDUAL_DATA),
                ("danh_gia_cuon_chieu", pd.read_csv(app.ROOT / "data/ket_qua_mo_hinh/nguyen_khang/danh_gia_cuon_chieu.csv")),
            ]:
                pd.testing.assert_frame_equal(pd.read_csv(Path(folder) / f"{name}.csv"), expected)

    def test_custom_rates_and_prediction_intervals(self):
        for rate in (-1, -.1, 0, .05):
            frame = tao_kich_ban(MODEL_INFO, rate)
            self.assertTrue(np.isfinite(frame.select_dtypes("number")).all().all())
            self.assertTrue((frame.lower_90 <= frame.temperature_prediction).all())
            self.assertTrue((frame.upper_90 >= frame.temperature_prediction).all())
        for rate in (np.nan, np.inf, -1.01):
            with self.assertRaises(ValueError):
                tao_kich_ban(MODEL_INFO, rate)

    def test_global_model_input_matches_sources(self):
        pd.testing.assert_frame_equal(build_global_year(), GLOBAL_DATA, check_dtype=False)
        self.assertEqual(GLOBAL_DATA.year.tolist(), list(range(1880, 2025)))
        nasa = pd.read_csv(app.ROOT / "data/du_lieu_da_xu_ly/duc/nhiet_do_toan_cau.csv").set_index("year")
        co2 = pd.read_csv(app.ROOT / "data/du_lieu_da_xu_ly/quan/co2_toan_cau.csv").set_index("year")
        np.testing.assert_allclose(GLOBAL_DATA.temperature_anomaly, nasa.loc[GLOBAL_DATA.year, "temperature_anomaly"])
        np.testing.assert_allclose(GLOBAL_DATA.cumulative_co2, co2.loc[GLOBAL_DATA.year, "cumulative_co2"])
        self.assertEqual(MODEL_INFO["source_period"], [1880, 2024])
        self.assertEqual(MODEL_INFO["train_period"], [1884, 2014])
        self.assertEqual(MODEL_INFO["sample_size"], 141)
        self.assertTrue(GLOBAL_DATA.year.diff().iloc[1:].eq(1).all())
        self.assertTrue(np.isfinite(GLOBAL_DATA[["co2", "cumulative_co2", "temperature_anomaly"]]).all().all())

    def test_model_history_includes_1880_and_negative_temperatures(self):
        figure = app.tao_bieu_do_du_bao_nhiet_do(GLOBAL_DATA, SCENARIO_DATA, "trend")
        np.testing.assert_array_equal(figure.data[2].x, np.arange(1880, 2025))
        np.testing.assert_allclose(figure.data[2].y, GLOBAL_DATA.temperature_anomaly.rolling(5).mean(), equal_nan=True)
        self.assertEqual(figure.layout.xaxis.range[0], 1880)
        self.assertLess(np.nanmin(figure.data[2].y), 0)

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
            actual = tao_kich_ban(MODEL_INFO, expected.annual_change_pct.iloc[0] / 100)
            columns = ["year", "co2", "cumulative_co2", "extrapolation_ratio",
                       "temperature_prediction", "lower_90", "upper_90"]
            np.testing.assert_allclose(actual[columns], expected[columns], rtol=1e-12)
            np.testing.assert_allclose(actual.cumulative_co2, MODEL_INFO["last_cumulative_co2"] + actual.co2.cumsum())

    def test_selected_year_changes_chart_marker_and_kpis(self):
        result = app.cap_nhat_trang_du_doan("decline", -5, 2030)
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
        self.assertEqual(MODEL_INFO["test_size"], 10)
        self.assertAlmostEqual(MODEL_INFO["mse_test"], MODEL_INFO["rmse_test"] ** 2)
        self.assertTrue((SCENARIO_DATA.extrapolation_ratio > 1).all())

    def test_residual_diagnostics_are_complete(self):
        self.assertEqual(RESIDUAL_DATA.year.tolist(), list(range(1884, 2015)))
        self.assertEqual(int(RESIDUAL_DATA.influential.sum()), MODEL_INFO["train_influential_count"])
        self.assertAlmostEqual(RESIDUAL_DATA.residual.mean(), 0, places=12)
        self.assertGreater(MODEL_INFO["bootstrap_block_length"], 5)
        self.assertLess(MODEL_INFO["train_durbin_watson"], .5)
        self.assertLess(MODEL_INFO["train_breusch_pagan_p"], .05)

    def test_emission_choices_change_the_2050_result(self):
        year_2050 = SCENARIO_DATA[SCENARIO_DATA.year == 2050].set_index("scenario_id")
        self.assertLess(
            year_2050.loc["decline", "temperature_prediction"],
            year_2050.loc["trend", "temperature_prediction"],
        )
        custom = tao_kich_ban(MODEL_INFO, -.10)
        self.assertTrue(custom.cumulative_co2.is_monotonic_increasing)
        self.assertGreater(custom.lower_90.min(), -1)

    def test_custom_scenario_callback_is_serializable(self):
        result = app.cap_nhat_trang_du_doan("custom", -7.5, 2050)
        self.assertEqual(len(result), 9)
        self.assertEqual(len(result[-1]), 104)
        json.dumps(result, cls=PlotlyJSONEncoder)

class DashboardSmokeTests(unittest.TestCase):
    def test_overview_year_stays_inside_selected_country_data(self):
        frame = loc_du_lieu("1970-2024")
        current = app.tao_ban_do_the_gioi(frame[frame.year.eq(1970)]).to_plotly_json()
        with patch.object(app, "ctx") as context:
            context.triggered_id = "country-filter"
            for code, first in [("BLM", 2011), ("GUM", 1990), ("MNP", 1992)]:
                self.assertEqual(app.lay_cac_nam_ban_do(frame, code)[0], first)
                result = app.cap_nhat_tong_quan("1970-2024", "all", code, "temperature", "globe", 1970, 0, "#overview", current)
                self.assertEqual(result[7], first)
                self.assertEqual(result[10], first)
                self.assertEqual(result[11], str(first))
                self.assertEqual(result[0][0].children[1].children, str(first))
                for trace in result[5].data:
                    self.assertTrue(all(row[1] == first for row in trace.customdata))

    def test_overview_period_change_moves_map_to_latest_year(self):
        old_frame = loc_du_lieu("1961-1969")
        current = app.tao_ban_do_the_gioi(old_frame[old_frame.year.eq(1969)]).to_plotly_json()
        with patch.object(app, "ctx") as context:
            context.triggered_id = "year-range"
            result = app.cap_nhat_tong_quan(
                "1961-2024", "all", "all", "temperature", "globe",
                1969, 0, "#overview", current,
            )
        self.assertEqual(result[10], 2024)
        self.assertEqual(result[11], "2024")
        for trace in result[5].data:
            self.assertTrue(all(row[1] == 2024 for row in trace.customdata))

    def test_csv_download_matches_filter_including_missing_values(self):
        for years in ["1970-2024", "1970-1979", "1980-1989", "1990-1999",
                      "2000-2009", "2010-2019", "2020-2024"]:
            for continent, country in [("all", "all"), ("Europe", "all"), ("Asia", "VNM"),
                                       ("North America", "BLM"), ("all", "ATA")]:
                result = app.xuat_du_lieu(1, None, years, continent, country)
                actual = pd.read_csv(StringIO(result["content"]))
                expected = loc_du_lieu(years, continent, country).reset_index(drop=True)
                pd.testing.assert_frame_equal(actual, expected, check_dtype=False)

    def test_wsgi_entrypoint(self):
        from app import app as wsgi_app

        self.assertIs(wsgi_app, app.server)
        self.assertEqual(wsgi_app.test_client().get("/").status_code, 200)

    def test_filter_change_during_navigation_builds_current_country(self):
        with patch.object(app, "ctx") as context:
            context.triggered_id = "country-filter"
            for route in ("overview", "earth"):
                result = app.hien_thi_trang(f"#{route}", "1970-2024", "all", "VNM", "temperature")
                self.assertIn("Vietnam", self._component_text(result[0]))
                ready = app.hien_thi_trang(f"#{route}", "1970-2024", "all", "VNM", "temperature",
                                        "overview-globe" if route == "overview" else None,
                                        "globe" if route == "earth" else None)
                self.assertIs(ready[0], app.no_update)

    def test_world_sector_chart_includes_all_edgar_codes(self):
        for year in (1970, 2023, 2024):
            frame = DATA[DATA.year == year]
            expected = SECTOR_DATA[SECTOR_DATA.year == year].co2.sum()
            self.assertAlmostEqual(tong_co2_theo_nganh(frame, use_global=True).sum(), expected)

    def test_overview_donut_uses_global_continent_totals(self):
        frame = loc_du_lieu()
        overview = app.tao_so_sanh_tong_quan(frame, "all", 2024)
        overview_plot = overview.children[1].children[1].figure
        expected = DATA[DATA.year.eq(2024)].groupby("continent").co2.sum(min_count=1)
        actual = dict(zip(overview_plot.data[0].labels, overview_plot.data[0].values))
        expected = {app.CONTINENT_NAMES.get(name, name): value for name, value in expected.items() if value > 0}
        self.assertEqual(set(actual), set(expected))
        for name, value in expected.items():
            self.assertAlmostEqual(actual[name], value)
        self.assertAlmostEqual(overview_plot.data[0].hole, .52)
        self.assertEqual(overview_plot.layout.height, 350)
        self.assertTrue(overview_plot.layout.showlegend)
        self.assertIn("TỔNG CO₂", overview_plot.layout.annotations[0].text)

    def test_trend_charts_do_not_hide_missing_years(self):
        frame = loc_du_lieu("2020-2024", country="VNM")
        frame.loc[frame.year == 2022, ["temperature_anomaly", "co2"]] = np.nan
        for create in (app.tao_bieu_do_nhiet_do, app.tao_bieu_do_co2):
            trace = create(frame).data[0]
            self.assertEqual(list(trace.x), list(range(2020, 2025)))
            self.assertTrue(pd.isna(trace.y[2]))

    def test_all_observed_data_pages_share_filters_and_csv(self):
        for page, _, _ in app.MENU:
            result = app.hien_thi_trang(f"#{page}", "1990-2023", "all", "VNM", "temperature")
            self.assertEqual(result[4], page == "scenario")
            self.assertEqual("hidden-filter" in result[8], page == "scenario")
            if page != "scenario":
                self.assertEqual(result[2], "Vietnam · 1990–2023")

    def test_sector_shares_follow_selected_country_and_year(self):
        frame = loc_du_lieu("2000-2023", country="VNM")
        totals = tong_co2_theo_nganh(frame)
        source = SECTOR_DATA[(SECTOR_DATA.iso_alpha == "VNM") & (SECTOR_DATA.year == 2023)]
        self.assertAlmostEqual(totals.sum(), source.co2.sum())
        figure = app.tao_bieu_do_nganh(totals)
        self.assertAlmostEqual(sum(figure.data[0].x), 100)
        self.assertEqual(figure.data[0].y[-1], totals.index[0])

    def test_insights_handle_missing_and_single_year_data(self):
        for country in ("VNM", "ESH", "ATA"):
            frame = loc_du_lieu("2024-2024", country=country)
            content = app.tao_trang_nhan_dinh(frame, tong_hop_du_lieu(frame), country)
            text = self._component_text(content)
            self.assertIn("Chưa đủ dữ liệu nhiệt độ", text)
            self.assertIn("Chưa đủ dữ liệu CO₂", text)
            self.assertNotIn("nan", text.lower())
            json.dumps(content, cls=PlotlyJSONEncoder)

    def test_insights_use_complete_calendar_windows_and_actual_co2_years(self):
        frame = loc_du_lieu("1970-2024", country="VNM")
        series = tong_hop_du_lieu(frame)
        content = app.tao_trang_nhan_dinh(frame, series, "Vietnam")
        first = series[series.year.between(1970, 1974)].temperature_anomaly.mean()
        last = series[series.year.between(2020, 2024)].temperature_anomaly.mean()
        self.assertEqual(content[1].children[0].children[0].children[1].children, f"{last-first:+.2f} °C")
        series.loc[series.year.eq(1970), "temperature_anomaly"] = np.nan
        series.loc[series.year.eq(2024), "co2"] = np.nan
        text = self._component_text(app.tao_trang_nhan_dinh(frame, series, "Vietnam"))
        self.assertIn("Chưa đủ dữ liệu nhiệt độ", text)
        self.assertIn("2023:", text)

    def test_co2_continent_area_and_industry_treemap_use_filtered_data(self):
        frame = loc_du_lieu("2015-2024", "Asia", "VNM")
        content = app.hien_thi_trang("#co2", "2015-2024", "Asia", "VNM", "co2")[0].children
        cards = content.children[0].children[1].children
        area = cards[3].children[1].figure
        tree = cards[4].children[1].figure
        expected_area = frame.groupby("year").co2.sum(min_count=1).dropna()
        self.assertEqual(len(area.data), 1)
        self.assertEqual(area.data[0].name, "Châu Á")
        np.testing.assert_array_equal(area.data[0].x, expected_area.index)
        np.testing.assert_allclose(np.asarray(area.data[0].y, dtype=float), expected_area.values)
        sectors = loc_du_lieu_nganh(frame)
        totals = sectors.groupby(["sector", "year"]).co2.sum(min_count=1).groupby("sector").mean()
        self.assertAlmostEqual(sum(tree.data[0].values), totals.sum())
        self.assertAlmostEqual(sum(row[0] for row in tree.data[0].customdata), 100)

    def test_all_pages_build(self):
        self.assertEqual(set(app.PAGE_INFO), {page for page, _, _ in app.MENU})
        for page, _, _ in app.MENU:
            with self.subTest(page=page):
                result = app.hien_thi_trang(
                    f"#{page}", "1970-2024", "all", "all",
                    "temperature",
                )
                self.assertEqual(len(result), 9)

    def test_scenario_page_has_controls_charts_and_download(self):
        content = app.hien_thi_trang(
            "#scenario", "1970-2024", "all", "all",
            "temperature",
        )[0]
        ids = self._component_ids(content)
        self.assertTrue({
            "scenario-choice", "scenario-rate", "scenario-year",
            "scenario-temperature-chart", "scenario-co2-chart",
            "scenario-backtest-chart", "scenario-residual-chart",
            "download-scenarios-button",
        }.issubset(ids))

    def test_member_eda_galleries_are_attached_to_expected_pages(self):
        expected = {
            "temperature": "duc-eda-gallery",
            "co2": "quan-eda-gallery",
        }
        for page, gallery_id in expected.items():
            with self.subTest(page=page):
                content = app.hien_thi_trang(
                    f"#{page}", "1970-2024", "all", "all",
                    "temperature",
                )[0]
                self.assertIn(gallery_id, self._component_ids(content))

    def test_member_pages_only_show_declared_member_artifacts(self):
        for page in ("temperature", "co2"):
            with self.subTest(page=page):
                content = app.hien_thi_trang(
                    f"#{page}", "1970-2024", "all", "all",
                    "temperature",
                )[0]
                self.assertEqual(self._component_types(content).count("Graph"), 6)
                self.assertEqual(self._component_types(content).count("Img"), 6 if page == "temperature" else 5)
                self.assertNotIn("Iframe", self._component_types(content))
                text = self._component_text(content)
                self.assertIn("Biểu đồ tĩnh", text)
                self.assertIn("Biểu đồ tương tác", text)
                self.assertLess(text.index("Biểu đồ tương tác"), text.index("Biểu đồ tĩnh"))

        gallery = app.hien_thi_trang("#temperature", "1970-2024", "all", "all", "temperature")[0].children
        interactive_section = gallery.children[0]
        self.assertIn("interactive", interactive_section.className)
        self.assertIn("interactive", interactive_section.children[1].className)

    def test_member_charts_use_filtered_source_values(self):
        for continent, country in [("all", "all"), ("Asia", "all"), ("Asia", "VNM")]:
            for page, field in [("temperature", "temperature_anomaly"), ("co2", "co2")]:
                frame = loc_du_lieu("2015-2024", continent, country, temperature=page == "temperature")
                series = (chuoi_nhiet_do(frame, "2015-2024", use_global=continent == country == "all")
                          if page == "temperature" else tong_hop_du_lieu(frame, use_global=continent == country == "all"))
                content = app.hien_thi_trang(f"#{page}", "2015-2024", continent, country, "temperature")[0].children
                cards = content.children[0].children[1].children
                figure = cards[0].children[1].figure
                np.testing.assert_array_equal(figure.data[0].x, series.year)
                np.testing.assert_allclose(figure.data[0].y, series[field], equal_nan=True)
                map_trace = cards[2].children[1].figure.data[0]
                expected = frame[frame.year.between(2015, 2019)].dropna(subset=[field if page == "temperature" else "co2_per_capita"])
                self.assertEqual(set(map_trace.locations), set(expected.iso_alpha))

    def test_country_options_follow_continent_and_keep_valid_selection(self):
        options, value = current_filters("Asia", "2020-2024", "USA")[4:6]
        self.assertEqual(value, "all")
        self.assertNotIn("USA", {option["value"] for option in options})
        self.assertEqual(current_filters("Asia", "2020-2024", "VNM")[5], "VNM")

    def test_member_pages_handle_missing_and_single_year_data(self):
        for page in ("temperature", "co2"):
            for country in ("VNM", "ESH", "ATA"):
                content = app.hien_thi_trang(f"#{page}", "2024-2024", "all", country, "temperature")[0]
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
    def test_decade_filter_covers_data_once_and_marks_partial_decade(self):
        dropdown = app.tao_bo_loc().children[0].children[1]
        options = dropdown.options
        periods = [item["value"] for item in options[1:]]
        self.assertEqual(periods[0], "1961-1969")
        self.assertEqual(periods[-1], "2020-2024")
        self.assertEqual(len(periods), 7)
        self.assertIn("chưa đủ 10 năm", options[-1]["label"])
        pieces = [loc_du_lieu(period) for period in periods]
        pd.testing.assert_frame_equal(pd.concat(pieces).sort_index(), DATA[DATA.year.ge(1961)])
        self.assertEqual([piece.year.nunique() for piece in pieces], [9] + [10] * 5 + [5])

    def test_decade_mean_uses_available_years_and_keeps_zero(self):
        from bang_dieu_khien.nguyen_khang.thap_ky import trung_binh_quoc_gia_theo_thap_ky

        frame = pd.DataFrame({
            "iso_alpha": ["VNM"] * 5 + ["ATA"] * 5,
            "country": ["Vietnam"] * 5 + ["Antarctica"] * 5,
            "year": list(range(2020, 2025)) * 2,
            "co2_per_capita": [0, 2, np.nan, 4, np.nan] + [np.nan] * 5,
        })
        result = trung_binh_quoc_gia_theo_thap_ky(frame, "co2_per_capita")
        self.assertEqual(result.iso_alpha.tolist(), ["VNM"])
        self.assertEqual(result.period.tolist(), ["2020–2024"])
        self.assertEqual(result.years.tolist(), [3])
        self.assertEqual(result.co2_per_capita.tolist(), [2.0])

    def test_scatter_averages_only_years_with_both_indicators(self):
        frame = loc_du_lieu("2020-2024", country="VNM")
        frame["co2_per_capita"] = [10, np.nan, 30, 50, np.nan]
        frame["renewable_percent"] = [np.nan, 90, 70, 50, np.nan]
        figures = app.co2_figures(tong_hop_du_lieu(frame), frame, loc_du_lieu_nganh(frame))
        trace = figures["06_scatter_co2pc_renewable"].data[0]
        self.assertEqual(list(trace.x), [60])
        self.assertEqual(list(trace.y), [40])
        self.assertEqual(trace.customdata[0][0], 2)

    def test_all_twelve_charts_match_each_filtered_table(self):
        scopes = [("all", "all"), ("Asia", "all"), ("Europe", "all"),
                  ("all", "VNM"), ("all", "ESH"), ("all", "ATA")]
        for years in ["1961-1969", "1970-2024", "1970-1979", "1980-1989", "1990-1999", "2000-2009",
                      "2010-2019", "2020-2025", "2024-2024", "1971-1979"]:
            for continent, country in scopes:
                with self.subTest(years=years, continent=continent, country=country):
                    frame = loc_du_lieu(years, continent, country, temperature=True)
                    series = chuoi_nhiet_do(frame, years, continent == country == "all")
                    monthly = loc_du_lieu_thang(frame, continent == country == "all", years)
                    temperature = list(app.temperature_figures(series, frame, monthly).values())
                    periods = {decade: f"{group.year.min()}–{group.year.max()}"
                               for decade, group in frame.groupby(frame.year // 10 * 10)}
                    valid = frame.dropna(subset=["temperature_anomaly"]).assign(decade=lambda d: (d.year // 10 * 10).map(periods))
                    np.testing.assert_allclose(temperature[0].data[0].y, series.temperature_anomaly, equal_nan=True)
                    np.testing.assert_allclose(temperature[0].data[1].y, series.temperature_anomaly.rolling(5).mean(), equal_nan=True)
                    decades = series.groupby(series.year // 10 * 10).temperature_anomaly.mean()
                    np.testing.assert_allclose(temperature[1].data[0].y, decades, equal_nan=True)
                    self.assert_map_decades(temperature[2], frame, "temperature_anomaly")
                    pivot = valid.pivot_table(index="continent", columns="decade", values="temperature_anomaly")
                    if not pivot.empty:
                        np.testing.assert_allclose(temperature[3].data[0].z, pivot, equal_nan=True)
                    for trace in temperature[4].data:
                        np.testing.assert_allclose(trace.y, valid[valid.decade.eq(trace.name)].temperature_anomaly)
                    expected = monthly.groupby(["year", "month"]).temperature_anomaly.mean().groupby("month")
                    np.testing.assert_array_equal(temperature[5].data[0].x, range(1, 13))
                    np.testing.assert_allclose(temperature[5].data[0].y, expected.mean().reindex(range(1, 13)), equal_nan=True)
                    np.testing.assert_allclose(temperature[5].data[0].customdata, expected.count().reindex(range(1, 13)), equal_nan=True)
                    frame = loc_du_lieu(years, continent, country)
                    series = tong_hop_du_lieu(frame, continent == country == "all", co2_only=True)
                    sectors = loc_du_lieu_nganh(frame, continent == country == "all")
                    co2 = list(app.co2_figures(series, frame, sectors).values())
                    np.testing.assert_allclose(co2[0].data[0].y, series.co2, equal_nan=True)
                    top = frame.groupby("country", as_index=False).co2.mean().dropna(subset=["co2"]).nlargest(15, "co2")
                    actual = {name: value for trace in co2[1].data for name, value in zip(trace.y, trace.x)}
                    self.assertEqual(actual, top.set_index("country").co2.to_dict())
                    self.assert_map_decades(co2[2], frame, "co2_per_capita")
                    continent_totals = (
                        frame.groupby(["continent", "year"], observed=True).co2
                        .sum(min_count=1).dropna()
                    )
                    for trace in co2[3].data:
                        expected_values = continent_totals.loc[trace.name].reindex(trace.x)
                        np.testing.assert_allclose(trace.y, expected_values, equal_nan=True)
                    totals = sectors.groupby(["sector", "year"]).co2.sum(min_count=1)
                    tree = totals.groupby("sector").mean()
                    tree = tree[tree > 0]
                    if not tree.empty:
                        trace = co2[4].data[0]
                        np.testing.assert_allclose(trace.values, tree.reindex(trace.labels))
                        np.testing.assert_allclose(np.asarray(trace.customdata, dtype=float)[:, 0], tree.reindex(trace.labels) / tree.sum() * 100)
                    paired = frame.dropna(subset=["co2_per_capita", "renewable_percent"])
                    paired = paired.groupby("country", as_index=False)[["co2_per_capita", "renewable_percent"]].mean()
                    actual = {name: (x, y) for trace in co2[5].data for name, x, y in zip(trace.hovertext, trace.x, trace.y)}
                    expected = {row.country: (row.renewable_percent, row.co2_per_capita) for row in paired.itertuples()}
                    self.assertEqual(actual, expected)

    def assert_map_decades(self, figure, data, field):
        expected = {}
        counts = {}
        for _, group in data.groupby(data.year // 10 * 10):
            label = f"{group.year.min()}–{group.year.max()}"
            values = group.groupby("iso_alpha")[field].mean().dropna()
            if not values.empty:
                expected[label] = values.to_dict()
                counts[label] = group.groupby("iso_alpha")[field].count().to_dict()
        labels = list(expected)
        self.assertEqual([frame.name for frame in figure.frames], labels if len(labels) > 1 else [])
        if not labels:
            self.assertFalse(figure.data)
            return
        snapshots = [(labels[0], figure.data[0])] + [(frame.name, frame.data[0]) for frame in figure.frames]
        for label, trace in snapshots:
            self.assertEqual(dict(zip(trace.locations, trace.z)), expected[label])
            for iso, custom in zip(trace.locations, trace.customdata):
                self.assertEqual(custom[0], label)
                self.assertEqual(custom[1], counts[label][iso])
        if figure.frames:
            self.assertEqual([step.args[0][0] for step in figure.layout.sliders[0].steps], labels)
            self.assertTrue(all(step.args[1]["frame"]["redraw"] for step in figure.layout.sliders[0].steps))
            self.assertEqual(figure.layout.sliders[0].x, .05)
            self.assertEqual(figure.layout.sliders[0].len, 1)
            buttons = figure.layout.updatemenus[0].buttons
            self.assertEqual([button.label for button in buttons], ["▶ Phát", "■ Dừng"])
            self.assertTrue(all(button.method == "animate" for button in buttons))

    def test_member_maps_follow_decade_and_country_filters(self):
        for route, field in [("temperature", "temperature_anomaly"), ("co2", "co2_per_capita")]:
            for continent, country in [("all", "all"), ("Asia", "VNM"), ("all", "ATA")]:
                with self.subTest(route=route, country=country):
                    page = app.hien_thi_trang(f"#{route}", "1990-2023", continent, country, "temperature")[0]
                    cards = page.children.children[0].children[1].children
                    figure = cards[2].children[1].figure
                    frame = loc_du_lieu("1990-2023", continent, country, temperature=route == "temperature")
                    self.assert_map_decades(figure, frame, field)
                    self.assertIn(f"{app.ten_pham_vi(continent, country)} · Dữ liệu 1990–2023", figure.layout.meta["scope"])
                    if country != "ATA":
                        series = (chuoi_nhiet_do(frame, "1990-2023", use_global=continent == country == "all")
                                  if route == "temperature" else tong_hop_du_lieu(frame, continent == country == "all"))
                        expected = series.temperature_anomaly if route == "temperature" else series.co2
                        np.testing.assert_allclose(cards[0].children[1].figure.data[0].y, expected, equal_nan=True)

    def test_continent_colors_do_not_change_with_filters(self):
        from phan_tich_co2.quan.tao_bieu_do_plotly import CONTINENT_COLORS

        frame = loc_du_lieu("2015-2024", country="VNM")
        sectors = loc_du_lieu_nganh(frame)
        for countries in (frame, loc_du_lieu("2015-2024")):
            figure = app.co2_figures(tong_hop_du_lieu(countries), countries, sectors)["04_stacked_area_chau_luc"]
            for trace in figure.data:
                self.assertEqual(trace.line.color, CONTINENT_COLORS[trace.name])

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
        frame = loc_du_lieu("2020-2021", country="VNM")
        monthly = pd.DataFrame({"year": [2020, 2020, 2021, 2020], "month": [1, 1, 1, 2],
                                "temperature_anomaly": [0, 2, 4, np.nan]})
        figure = app.temperature_figures(tong_hop_du_lieu(frame), frame, monthly)["06_nhiet_do_theo_thang"]
        self.assertEqual(figure.data[0].y[0], 2.5)
        self.assertEqual(figure.data[0].customdata[0], 2)
        self.assertTrue(np.isnan(figure.data[0].y[1:]).all())
        self.assertFalse(figure.data[0].connectgaps)
        page = app.hien_thi_trang("#temperature", "2024-2024", "all", "VNM", "temperature")[0]
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
            ("duc/tinh/06_nhiet_do_theo_thang.png", "Img"),
            ("duc/tuong_tac/03_ban_do_nhiet_do.html", "Graph"),
            ("quan/tuong_tac/03_choropleth_co2pc.html", "Graph"),
        ]
        for path, component_type in cases:
            with self.subTest(path=path):
                opened = self._modal_callback(path)
                self.assertEqual(opened["eda-modal"]["className"], "eda-modal open")
                modal_children = opened["eda-modal-content"]["children"]
                self.assertEqual(modal_children[1]["type"], component_type)
                if component_type == "Img":
                    self.assertEqual(modal_children[1]["props"]["src"], f"/eda-files/{path}")
                elif Path(path).name.startswith("03"):
                    figure = modal_children[1]["props"]["figure"]
                    self.assertEqual([frame["name"] for frame in figure["frames"]],
                                     ["2015–2019", "2020–2024"])
                    self.assertIn("Vietnam · Dữ liệu 2015–2024", figure["layout"]["meta"]["scope"])
                    self.assertIn("Vietnam", modal_children[0]["props"]["children"][1]["props"]["children"])
                else:
                    expected = loc_du_lieu("2015-2024", country="VNM", temperature=True).temperature_anomaly.to_numpy()
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
        route = "#temperature" if path.startswith("duc/") else "#co2"
        page = app.hien_thi_trang(route, "2015-2024", "all", "VNM", "temperature")[0]
        cards = page.children.children[0].children[1].children
        figure = cards[int(Path(path).name[:2]) - 1].children[1].figure
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
                {"id": "url", "property": "hash", "value": route},
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


class DucTemperatureTests(unittest.TestCase):
    def test_monthly_chart_matches_raw_nasa_for_every_period(self):
        raw = pd.read_csv(app.ROOT / "data/du_lieu_goc/duc/nasa_nhiet_do_toan_cau_1880_2026.csv",
                          header=1, na_values="***")
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        options = current_filters("all", "1961-2025", "all", "#temperature")[0]
        for years in ["1880-2025", "2025-2025"] + [item["value"] for item in options]:
            with self.subTest(period=years):
                gallery = app.hien_thi_trang("#temperature", years, "all", "all", "temperature")[0].children
                cards = gallery.children[0].children[1].children
                selected = raw[raw.Year.between(*map(int, years.split("-")))][months]
                trace = cards[5].children[1].figure.data[0]
                np.testing.assert_allclose(trace.y, selected.mean(), atol=1e-12)
                np.testing.assert_array_equal(trace.customdata, selected.count())
                for card in cards:
                    self.assertIn(f"Dữ liệu {years.replace('-', '–')}", DashboardSmokeTests._component_text(card))
                for index in (0, 5):
                    self.assertIn("So với trung bình 1951–1980", DashboardSmokeTests._component_text(cards[index]))
                static = gallery.children[1].children[1].children[-1]
                self.assertTrue(static.children[1].src.endswith("tinh/06_nhiet_do_theo_thang.png"))
                self.assertIn("1880–2025", DashboardSmokeTests._component_text(static))

    def test_all_filters_are_saved_separately_for_each_page(self):
        first = app.cap_nhat_bo_loc("#overview", "1961-2024", "all", "all", "temperature")
        overview = app.cap_nhat_bo_loc("#overview", "1990-1999", "Asia", "VNM", "co2", saved=first[3])
        temperature = app.cap_nhat_bo_loc("#temperature", overview[1], "Asia", "VNM", "co2", saved=overview[3])
        self.assertEqual(temperature[1], "1961-2025")
        self.assertEqual(temperature[5:], ("all", "all", "temperature"))
        co2 = app.cap_nhat_bo_loc("#co2", temperature[1], "all", "all", "temperature", saved=temperature[3])
        self.assertEqual(co2[1], "1850-2024")
        restored = app.cap_nhat_bo_loc("#overview", co2[1], "all", "all", "temperature", saved=co2[3])
        self.assertEqual(restored[1], "1990-1999")
        self.assertEqual(restored[5:], ("VNM", "Asia", "co2"))

    def test_1880_overview_uses_paired_global_values_and_preserves_country_gaps(self):
        page = app.hien_thi_trang("#overview", "1880-1889", "all", "all", "temperature")[0]
        summary, temperature, co2, _ = app.tao_chi_tiet_tong_quan(loc_du_lieu("1880-1889"), "all", 1880, "Toàn cầu")
        expected = GLOBAL_DATA[GLOBAL_DATA.year.between(1880, 1889)]
        np.testing.assert_allclose(temperature.data[0].y, expected.temperature_anomaly)
        np.testing.assert_allclose(co2.data[0].y, expected.co2)
        self.assertIn("1880", DashboardSmokeTests._component_text(summary))
        self.assertNotIn("Chưa có dữ liệu trong phạm vi này", DashboardSmokeTests._component_text(page))
        self.assertTrue(loc_du_lieu("1880-1960").temperature_anomaly.isna().all())
        _, missing, _, _ = app.tao_chi_tiet_tong_quan(loc_du_lieu("1880-1889", country="VNM"), "VNM", 1880, "Vietnam")
        self.assertEqual(missing.layout.annotations[0].text, "Nhiệt độ quốc gia chỉ có từ 1961")
        export = app.xuat_du_lieu(1, None, "1880-1889", "all", "all", "#overview")
        pd.testing.assert_frame_equal(pd.read_csv(StringIO(export["content"])), expected.reset_index(drop=True), check_dtype=False)

    def test_duc_cleaning_reproduces_all_three_csv_files(self):
        from phan_tich_nhiet_do.duc import lam_sach_du_lieu as duc

        saved = duc.OUT
        with TemporaryDirectory() as folder, patch.object(duc, "OUT", Path(folder)):
            duc.clean_nasa()
            duc.clean_faostat()
            duc.clean_monthly()
            for name in ("nhiet_do_toan_cau", "nhiet_do_quoc_gia", "nhiet_do_theo_thang"):
                with self.subTest(table=name):
                    pd.testing.assert_frame_equal(pd.read_csv(Path(folder) / f"{name}.csv"),
                                                  pd.read_csv(saved / f"{name}.csv"))

    def test_temperature_filter_starts_at_national_source_and_retains_global_history(self):
        result = app.cap_nhat_bo_loc("#temperature", "1961-2024", "all", "all", "temperature")
        options, value, header = result[:3]
        self.assertEqual((value, header), ("1961-2025", "1961–2025"))
        self.assertEqual(options[1]["value"], "1961-1969")
        self.assertEqual(options[-1]["value"], "2020-2025")
        self.assertIn("chưa đủ 10 năm", options[-1]["label"])
        self.assertEqual(int(GLOBAL_TEMPERATURE.year.min()), 1880)
        self.assertEqual(current_filters("all", "1990-1999", "all", "#temperature")[1], "1990-1999")

    def test_co2_1850_chart_and_export_match_original_world_series(self):
        result = current_filters("all", "1850-1859", "all", "#co2")
        self.assertEqual(result[1], "1850-1859")
        page = app.hien_thi_trang("#co2", result[1], "all", "all", "temperature")[0]
        cards = page.children.children[0].children[1].children
        expected = GLOBAL_CO2[GLOBAL_CO2.year.between(1850, 1859)]
        np.testing.assert_array_equal(cards[0].children[1].figure.data[0].x, expected.year)
        np.testing.assert_allclose(cards[0].children[1].figure.data[0].y, expected.co2)
        national = loc_du_lieu(result[1])
        expected_area = (
            national.groupby(["continent", "year"], observed=True).co2
            .sum(min_count=1).dropna()
        )
        english_name = {v: k for k, v in app.CONTINENT_NAMES.items()}
        for trace in cards[3].children[1].figure.data:
            continent = english_name.get(trace.name, trace.name)
            values = expected_area.loc[continent].reindex(trace.x)
            np.testing.assert_allclose(trace.y, values, equal_nan=True)
        for index in (4, 5):
            self.assertFalse(cards[index].children[1].figure.data)
        export = app.xuat_du_lieu(1, None, result[1], "all", "all", "#co2")
        pd.testing.assert_frame_equal(pd.read_csv(StringIO(export["content"])), expected.reset_index(drop=True))

    def test_nasa_1880s_render_without_country_data(self):
        page = app.hien_thi_trang("#temperature", "1880-1889", "all", "all", "temperature")[0]
        cards = page.children.children[0].children[1].children
        self.assertEqual(len(cards), 6)
        expected = GLOBAL_TEMPERATURE[GLOBAL_TEMPERATURE.year.between(1880, 1889)]
        np.testing.assert_array_equal(cards[0].children[1].figure.data[0].x, expected.year)
        np.testing.assert_allclose(cards[0].children[1].figure.data[0].y, expected.temperature_anomaly)
        self.assertEqual(list(cards[1].children[1].figure.data[0].x), ["1880–1889"])
        self.assertAlmostEqual(cards[1].children[1].figure.data[0].y[0], expected.temperature_anomaly.mean())
        self.assertFalse(cards[2].children[1].figure.data)
        self.assertIn("chỉ có từ 1961", DashboardSmokeTests._component_text(cards[2]))
        np.testing.assert_array_equal(cards[5].children[1].figure.data[0].customdata, np.full(12, 10))

    def test_country_temperature_keeps_1961_and_2025_source_values(self):
        source = pd.read_csv(app.ROOT / "data/du_lieu_da_xu_ly/duc/nhiet_do_quoc_gia.csv")
        for years in ("1960-1969", "2020-2025"):
            with self.subTest(period=years):
                frame = loc_du_lieu(years, country="VNM", temperature=True)
                expected = source[source.iso_alpha.eq("VNM") & source.year.between(*map(int, years.split("-")))]
                pd.testing.assert_frame_equal(frame, expected)
                page = app.hien_thi_trang("#temperature", years, "all", "VNM", "temperature")[0]
                cards = page.children.children[0].children[1].children
                np.testing.assert_allclose(cards[0].children[1].figure.data[0].y, expected.temperature_anomaly)
                self.assertEqual(cards[2].children[1].figure.data[0].customdata[0][1], len(expected))

    def test_invalid_early_temperature_period_resets_to_available_source(self):
        result = current_filters("all", "1880-1889", "VNM", "#temperature")
        options, selected = result[4:6]
        self.assertEqual(selected, "VNM")
        self.assertIn("VNM", {option["value"] for option in options})
        self.assertEqual(result[1], "1961-2025")

    def test_temperature_csv_uses_same_duc_source_as_charts(self):
        for years, country in (("1880-1889", "all"), ("1960-1969", "VNM"), ("2020-2025", "VNM")):
            with self.subTest(period=years, country=country):
                result = app.xuat_du_lieu(1, None, years, "all", country, "#temperature")
                actual = pd.read_csv(StringIO(result["content"]))
                frame = loc_du_lieu(years, country=country, temperature=True)
                expected = chuoi_nhiet_do(frame, years, use_global=True) if country == "all" else frame
                pd.testing.assert_frame_equal(actual, expected.reset_index(drop=True), check_dtype=False)


class EarthInteractionTests(unittest.TestCase):
    def test_map_click_can_switch_continent_and_country_together(self):
        for trigger in ("overview-globe", "globe"):
            with self.subTest(map=trigger), patch.object(app, "ctx") as context:
                context.triggered_id = trigger
                click = {"points": [{"location": "AUS", "customdata": ["Australia", 2024]}]}
                result = current_filters(
                    "Asia", "1880-2024", "VNM", "#overview",
                    overview_click=click, earth_click=click)
                options, country, continent = result[4:7]
                self.assertEqual((country, continent), ("AUS", "Oceania"))
                self.assertIn("AUS", {option["value"] for option in options})
                self.assertNotIn("VNM", {option["value"] for option in options})

    def test_globe_outside_continent_is_clickable_without_showing_filtered_values(self):
        snapshot = app.lay_du_lieu_ban_do(loc_du_lieu("1970-2024", "Asia"), 2024)
        self.assertEqual(set(snapshot.iso_alpha), set(DATA.loc[DATA.year.eq(2024), "iso_alpha"]))
        self.assertTrue(snapshot.loc[snapshot.outside_scope, ["co2", "temperature_anomaly"]].isna().all().all())
        figure = app.tao_ban_do_the_gioi(snapshot, "VNM")
        trace = next(trace for trace in figure.data if "AUS" in trace.locations)
        self.assertFalse(trace.showscale)
        self.assertEqual(trace.text[list(trace.locations).index("AUS")], "Ngoài châu lục đang chọn")

    def test_eda_map_click_selects_country_and_ignores_other_charts(self):
        for route, path in (("#temperature", "duc/tuong_tac/03_ban_do_nhiet_do.html"),
                            ("#co2", "quan/tuong_tac/03_choropleth_co2pc.html")):
            graph_id = {"type": "eda-chart", "path": path}
            click = {"points": [{"location": "VNM"}]}
            with self.subTest(page=route), patch.object(app, "ctx") as context:
                context.triggered_id = graph_id
                result = current_filters("all", "2020-2024", "all", route,
                                                    eda_clicks=[click], eda_ids=[graph_id])
                self.assertEqual(result[5:7], ("VNM", "all"))
                context.triggered_id = {"type": "eda-chart", "path": "duc/tuong_tac/01_xu_huong_nhiet_do_toan_cau.html"}
                self.assertEqual(current_filters("all", "2020-2024", "all", route,
                                 eda_clicks=[click], eda_ids=[graph_id]), (app.no_update,) * 8)

    def test_empty_or_stale_map_click_does_not_reset_filters(self):
        with patch.object(app, "ctx") as context:
            context.triggered_id = "overview-globe"
            self.assertEqual(current_filters("Asia", "1961-1969", "VNM"), (app.no_update,) * 8)
            context.triggered_id = "url"
            result = current_filters("Asia", "1961-1969", "VNM", "#temperature",
                                                overview_click={"points": [{"location": "AUS"}]})
            self.assertEqual(result[5:7], ("VNM", "Asia"))

    def test_earth_layout_is_focused_and_handles_missing_values(self):
        frame = loc_du_lieu("1970-2024")
        for country in ("all", "VNM", "ESH", "ATA"):
            content = app.tao_trang_ban_do(frame, country, "co2", app.ten_pham_vi("all", country))
            self.assertEqual(DashboardSmokeTests._component_types(content).count("Graph"), 3)
            text = DashboardSmokeTests._component_text(content)
            self.assertIn("triệu tấn", text)
            self.assertNotIn("nan", text.lower())
            self.assertNotIn("Tỷ trọng", text)

    def test_map_color_range_does_not_hide_extreme_values(self):
        for metric in ("temperature", "co2"):
            figure = app.tao_ban_do_the_gioi(DATA[DATA.year == 2024], metric=metric)
            trace = next(t for t in figure.data if t.showscale)
            self.assertLessEqual(trace.zmin, min(trace.z))
            self.assertGreaterEqual(trace.zmax, max(trace.z))
            self.assertEqual(len(trace.customdata[0]), 2)

    def test_temperature_colors_stay_consistent_between_years(self):
        palettes = []
        for year in (1970, 2000, 2024):
            figure = app.tao_ban_do_the_gioi(DATA[DATA.year == year])
            trace = next(t for t in figure.data if t.showscale)
            self.assertEqual((trace.zmin, trace.zmax), (-6, 6))
            self.assertIn((8 / 12, "#E65C36"), trace.colorscale)
            palettes.append(trace.colorscale)
        self.assertEqual(palettes[0], palettes[1])
        self.assertEqual(palettes[1], palettes[2])

    def test_year_changes_after_polar_rotation_keep_world_bounds(self):
        for lat in (95, 214.963, -215):
            rotation = {"lon": -255, "lat": lat, "roll": 0}
            initial = app.tao_ban_do_the_gioi(DATA[DATA.year == 2024], rotation=rotation)
            changed = app.cap_nhat_ban_do(DATA[DATA.year == 1970], "VNM", "temperature",
                                     "globe", 0, initial.to_plotly_json())
            geo = changed.layout.geo
            self.assertEqual(geo.projection.rotation.to_plotly_json(), rotation)
            self.assertEqual(geo.center.to_plotly_json(), {"lon": -255, "lat": lat})
            self.assertEqual(tuple(geo.lonaxis.range), (-180, 180))
            self.assertEqual(tuple(geo.lataxis.range), (-90, 90))

    def test_metric_and_year_changes_keep_selected_country_and_camera(self):
        figure = app.tao_ban_do_the_gioi(DATA[DATA.year == 2024], "ARG", rotation={"lon": -64, "lat": -34})
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
        figure = app.tao_ban_do_the_gioi(DATA[DATA.year == 2024])
        self.assertEqual(figure.layout.paper_bgcolor, "white")
        self.assertEqual(figure.layout.geo.oceancolor, "#163E5C")
        self.assertFalse(figure.layout.margin.autoexpand)
        self.assertEqual(app.khung_bieu_do(figure, globe=True).config["topojsonURL"], "/assets/")

    def test_globe_keeps_every_cleaned_country_clickable(self):
        snapshot = DATA[DATA.year == DATA.year.max()]
        for metric in ("temperature", "co2"):
            with self.subTest(metric=metric):
                figure = app.tao_ban_do_the_gioi(snapshot, "VNM", metric)
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
            app.lay_quoc_gia_duoc_chon({"points": [{"location": "VNM"}]}, available),
            "VNM",
        )
        self.assertEqual(
            app.lay_quoc_gia_duoc_chon({"points": [{"customdata": ["USA", 2024]}]}, available),
            "USA",
        )
        self.assertIsNone(
            app.lay_quoc_gia_duoc_chon({"points": [{"location": "FRA"}]}, available)
        )

    def test_click_view_switch_and_reset_callbacks(self):
        frame = loc_du_lieu("1970-2024")
        figure = app.tao_ban_do_the_gioi(
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
        initial = app.tao_ban_do_the_gioi(snapshot, "VNM").to_plotly_json()
        initial["layout"]["geo"]["projection"]["rotation"] = {"lon": 60, "lat": 30}
        selected = app.cap_nhat_ban_do(snapshot, "CHN", "temperature", "globe", 0, initial)
        self.assertEqual(selected.layout.geo.projection.rotation.lon, 60)
        self.assertEqual(selected.layout.geo.projection.rotation.lat, 30)
        self.assertEqual(selected.layout.geo.uirevision, initial["layout"]["geo"]["uirevision"])
        trace = next(t for t in selected.data if "CHN" in t.locations)
        index = list(trace.locations).index("CHN")
        self.assertEqual(trace.marker.line.color[index], "#FFD54A")
        self.assertEqual(trace.marker.line.width[index], 3)
        normal = next(i for i, code in enumerate(trace.locations) if code != "CHN")
        self.assertEqual(trace.marker.line.color[normal], "#8EA4B2")
        self.assertEqual(trace.marker.line.width[normal], .75)
        self.assertTrue(selected.layout.geo.showcountries)
        self.assertEqual(selected.layout.geo.countrycolor, "#8EA4B2")
        self.assertEqual(selected.layout.geo.countrywidth, .75)

    def test_flat_pan_does_not_leak_into_globe(self):
        snapshot = DATA[DATA.year == 2024]
        initial = app.tao_ban_do_the_gioi(snapshot, rotation={"lon": 72, "lat": 26}).to_plotly_json()
        flat = app.cap_nhat_ban_do(snapshot, "CHN", "temperature", "flat", 0, initial).to_plotly_json()
        self.assertEqual(flat["layout"]["geo"]["lonaxis"]["range"], [-180, 180])
        flat["layout"]["geo"]["center"] = {"lon": -45, "lat": 50}
        flat["layout"]["geo"]["projection"].update(rotation={"lon": -45}, scale=2)
        globe = app.cap_nhat_ban_do(snapshot, "CHN", "temperature", "globe", 0, flat)
        self.assertEqual(globe.layout.geo.projection.rotation.lon, 72)
        self.assertEqual(globe.layout.geo.projection.rotation.lat, 26)
        self.assertEqual(globe.layout.geo.projection.scale, 1)
        self.assertEqual(tuple(globe.layout.geo.lonaxis.range), (-180, 180))
        self.assertEqual(tuple(globe.layout.geo.lataxis.range), (-90, 90))
        self.assertEqual(globe.layout.geo.center.to_plotly_json(), {"lon": 72, "lat": 26})
        again = app.cap_nhat_ban_do(snapshot, "CHN", "temperature", "flat", 0, globe.to_plotly_json())
        self.assertEqual(again.layout.meta["globe_rotation"]["lon"], 72)
        reset = app.cap_nhat_ban_do(snapshot, "CHN", "temperature", "globe", 1, globe.to_plotly_json(), reset=True)
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
