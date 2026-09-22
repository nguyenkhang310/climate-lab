import json
import math
import unittest
from pathlib import Path

import pandas as pd
from plotly.utils import PlotlyJSONEncoder

import app
from climate_data import (
    DATA,
    FORECAST_DATA,
    GLOBAL_DATA,
    MODEL_METRICS,
    aggregate,
    filter_data,
)
from scripts.nguyen_khang.chuan_bi_du_lieu_dashboard import build_country_year

class ClimateDataTests(unittest.TestCase):
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

class ForecastTests(unittest.TestCase):
    def test_selected_model_has_lowest_test_rmse(self):
        selected = MODEL_METRICS["selected_model"]
        candidates = ["year_linear", "cumulative_co2_linear"]
        self.assertEqual(
            selected,
            min(candidates, key=lambda name: MODEL_METRICS[name]["rmse"]),
        )

    def test_three_complete_scenarios_to_2050(self):
        self.assertEqual(FORECAST_DATA.scenario.nunique(), 3)
        counts = FORECAST_DATA.groupby("scenario").year.nunique()
        self.assertTrue((counts == 26).all())
        self.assertEqual(int(FORECAST_DATA.year.min()), 2025)
        self.assertEqual(int(FORECAST_DATA.year.max()), 2050)
        for _, group in FORECAST_DATA.groupby("scenario"):
            self.assertTrue(group.sort_values("year").cumulative_co2.is_monotonic_increasing)

class DashboardSmokeTests(unittest.TestCase):
    def test_all_pages_build(self):
        pages = [
            "overview", "earth", "temperature", "co2", "comparison",
            "relationship", "forecast", "insights", "data", "settings",
        ]
        for page in pages:
            with self.subTest(page=page):
                result = app.render_page(
                    f"#{page}", "1970-2024", "all", "all",
                    "temperature", {}, "VNM",
                )
                self.assertEqual(len(result), 9)

    def test_member_eda_galleries_are_attached_to_expected_pages(self):
        expected = {
            "temperature": "duc-eda-gallery",
            "co2": "quan-eda-gallery",
            "forecast": "duc-forecast-gallery",
        }
        for page, gallery_id in expected.items():
            with self.subTest(page=page):
                content = app.render_page(
                    f"#{page}", "1970-2024", "all", "all",
                    "temperature", {}, "VNM",
                )[0]
                self.assertIn(gallery_id, self._component_ids(content))

    def test_member_pages_only_show_declared_member_artifacts(self):
        for page in ("temperature", "co2"):
            with self.subTest(page=page):
                content = app.render_page(
                    f"#{page}", "1970-2024", "all", "all",
                    "temperature", {}, "VNM",
                )[0]
                self.assertEqual(self._component_types(content).count("Graph"), 0)
                text = self._component_text(content)
                self.assertIn("Biểu đồ tĩnh", text)
                self.assertIn("Biểu đồ tương tác Plotly", text)

    @staticmethod
    def _component_ids(component):
        ids = set()
        if isinstance(component, (list, tuple)):
            for child in component:
                ids.update(DashboardSmokeTests._component_ids(child))
            return ids
        component_id = getattr(component, "id", None)
        if component_id:
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
    def test_all_declared_eda_files_exist_and_are_served(self):
        artifacts = (
            app.DUC_TEMPERATURE_ARTIFACTS
            + app.DUC_FORECAST_ARTIFACTS
            + app.QUAN_ARTIFACTS
        )
        client = app.server.test_client()
        for _, _, relative_path in artifacts:
            with self.subTest(path=relative_path):
                self.assertTrue((Path(app.EDA_ROOT) / relative_path).is_file())
                response = client.get(f"/eda-files/{relative_path}")
                self.assertEqual(response.status_code, 200)
                expected_mimetype = (
                    "text/html" if relative_path.endswith(".html") else "image/png"
                )
                self.assertEqual(response.mimetype, expected_mimetype)
                response.close()
        self.assertEqual(client.get("/eda-files/../app.py").status_code, 404)

    def test_quan_growth_has_no_infinite_values(self):
        frame = pd.read_csv(Path(app.ROOT) / "processed/quan/co2_quoc_gia.csv")
        finite = frame["co2_growth_pct"].dropna().map(math.isfinite)
        self.assertTrue(finite.all())
        self.assertEqual(int((frame["co2"] < 0).sum()), 0)


class EarthInteractionTests(unittest.TestCase):
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
            figure, "VNM", "globe.clickData", {"points": [{"location": "ABW"}]}
        )
        self.assertEqual(clicked["selected-country"]["data"], "ABW")

        switched = self._earth_callback(
            clicked["globe"]["figure"], "ABW", "earth-map-view.value",
            {"points": [{"location": "ABW"}]}, map_view="flat",
        )
        self.assertEqual(switched["selected-country"]["data"], "ABW")
        self.assertEqual(
            switched["globe"]["figure"]["layout"]["geo"]["projection"]["type"],
            "natural earth",
        )

        reset = self._earth_callback(
            switched["globe"]["figure"], "ABW", "reset-globe.n_clicks",
            {"points": [{"location": "ABW"}]}, map_view="flat", resets=1,
        )
        self.assertEqual(reset["selected-country"]["data"], "VNM")

    @staticmethod
    def _earth_callback(
        figure, selected, changed, click_data, map_view="globe", resets=0,
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
                {"id": "selected-country", "property": "data"},
            ],
            "inputs": [
                {"id": "globe", "property": "clickData", "value": click_data},
                {"id": "reset-globe", "property": "n_clicks", "value": resets},
                {"id": "earth-map-view", "property": "value", "value": map_view},
            ],
            "state": [
                {"id": "metric-filter", "property": "value", "value": "temperature"},
                {"id": "year-range", "property": "value", "value": "1970-2024"},
                {"id": "continent-filter", "property": "value", "value": "all"},
                {"id": "country-filter", "property": "value", "value": "all"},
                {"id": "selected-country", "property": "data", "value": selected},
                {"id": "globe", "property": "relayoutData", "value": {}},
                {"id": "globe", "property": "figure", "value": figure},
            ],
            "changedPropIds": [changed],
        }
        response = app.server.test_client().post("/_dash-update-component", json=payload)
        if response.status_code != 200:
            raise AssertionError(response.get_data(as_text=True))
        return response.get_json()["response"]

if __name__ == "__main__":
    unittest.main()
