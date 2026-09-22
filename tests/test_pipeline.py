import unittest

import app
from climate_data import (
    DATA,
    FORECAST_DATA,
    GLOBAL_DATA,
    MODEL_METRICS,
    aggregate,
    filter_data,
)

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

if __name__ == "__main__":
    unittest.main()
