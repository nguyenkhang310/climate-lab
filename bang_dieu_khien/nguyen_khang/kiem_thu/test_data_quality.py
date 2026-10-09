import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import numpy as np
import pandas as pd
import nbformat
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error

from bang_dieu_khien.nguyen_khang.du_lieu import DATA, MODEL_INFO, SECTOR_DATA, loc_du_lieu, loc_du_lieu_nganh
from mo_hinh_du_doan.nguyen_khang import mo_hinh_nhiet_do as model
from phan_tich_co2.quan import lam_sach_du_lieu as quan
from phan_tich_co2.quan.tao_bieu_do_plotly import renewable_coverage_note, sector_coverage_note
from phan_tich_nhiet_do.duc import lam_sach_du_lieu as duc

ROOT = Path(__file__).resolve().parents[3]
PROCESSED = ROOT / "data/du_lieu_da_xu_ly"


class CalendarYearTests(unittest.TestCase):
    def test_year_requires_12_values_and_preserves_zero(self):
        countries = pd.DataFrame({"country": ["Example"] * 2, "iso_alpha": ["AAA"] * 2,
                                  "continent": ["Asia"] * 2, "year": [2000, 2001], "decade": [2000] * 2})
        monthly = pd.DataFrame({"iso_alpha": ["AAA"] * 24, "year": [2000] * 12 + [2001] * 12,
                                "month": list(range(1, 13)) * 2, "temperature_anomaly": [0.] * 23 + [np.nan],
                                "source_flag": ["E"] * 24})
        with TemporaryDirectory() as folder, patch.object(duc, "OUT", Path(folder)):
            result, stats = duc.clean_calendar_year(countries, monthly)
        self.assertEqual(result.loc[0, "temperature_anomaly"], 0.)
        self.assertEqual(result.loc[0, "months_available"], 12)
        self.assertTrue(pd.isna(result.loc[1, "temperature_anomaly"]))
        self.assertEqual(result.loc[1, "months_available"], 11)
        self.assertEqual(stats["incomplete_years"], 1)

    def test_duplicate_month_cannot_manufacture_a_complete_year(self):
        country = pd.DataFrame({"country": ["Example"], "iso_alpha": ["AAA"],
                                "continent": ["Asia"], "year": [2000], "decade": [2000]})
        monthly = pd.DataFrame({"iso_alpha": ["AAA"] * 12, "year": [2000] * 12,
                                "month": [1] * 12, "temperature_anomaly": [1.] * 12, "source_flag": ["E"] * 12})
        with self.assertRaises(ValueError):
            duc.clean_calendar_year(country, monthly)

    def test_saved_calendar_csv_and_join_match_all_months(self):
        monthly = pd.read_csv(PROCESSED / "duc/nhiet_do_theo_thang.csv")
        monthly = monthly[monthly.iso_alpha.ne("WLD")]
        expected = monthly.groupby(["iso_alpha", "year"]).temperature_anomaly.agg(["mean", "count"])
        calendar = pd.read_csv(PROCESSED / "duc/nhiet_do_quoc_gia_nam_lich.csv").set_index(["iso_alpha", "year"])
        pd.testing.assert_index_equal(calendar.index, expected.index)
        np.testing.assert_allclose(calendar.temperature_anomaly, expected["mean"].where(expected["count"].eq(12)),
                                   rtol=1e-12, atol=1e-12, equal_nan=True)
        np.testing.assert_array_equal(calendar.months_available, expected["count"])
        joined = DATA.set_index(["iso_alpha", "year"])
        np.testing.assert_allclose(joined.temperature_anomaly, calendar.temperature_anomaly.reindex(joined.index),
                                   rtol=1e-12, atol=1e-12, equal_nan=True)
        meteorological = pd.read_csv(PROCESSED / "duc/nhiet_do_quoc_gia.csv").set_index(["iso_alpha", "year"])
        self.assertEqual(meteorological.loc[("VNM", 2024), "temperature_anomaly"], 1.914)
        self.assertAlmostEqual(calendar.loc[("VNM", 2024), "temperature_anomaly"], 1.8213333333333335)

    def test_notebook_saved_a_complete_execution_without_errors(self):
        notebook = nbformat.read(ROOT / "phan_tich_nhiet_do/duc/01_lam_sach_va_eda.ipynb", as_version=4)
        cells = [cell for cell in notebook["cells"] if cell["cell_type"] == "code"]
        self.assertEqual([cell["execution_count"] for cell in cells], list(range(1, len(cells) + 1)))
        self.assertFalse(any(output["output_type"] == "error" for cell in cells for output in cell["outputs"]))
        self.assertTrue(any("PASS:" in output.get("text", "") for cell in cells for output in cell["outputs"]))


class QuanQualityTests(unittest.TestCase):
    def test_cleaning_reproduces_all_four_saved_csvs(self):
        regions = pd.read_csv(quan.CONTINENT)
        cmap = dict(zip(regions.Code, regions["World region according to OWID"]))
        national, world, _ = quan.clean_owid(cmap)
        sectors, _ = quan.clean_edgar(cmap)
        renewable, _ = quan.clean_renewable(cmap)
        for name, expected in [("co2_quoc_gia", national), ("co2_toan_cau", world),
                               ("co2_theo_nganh", sectors), ("nang_luong_tai_tao", renewable)]:
            with self.subTest(table=name):
                actual = pd.read_csv(PROCESSED / f"quan/{name}.csv")
                pd.testing.assert_frame_equal(actual, expected, check_dtype=False, check_exact=False,
                                              rtol=1e-12, atol=1e-12)

    def test_curacao_remap_preserves_source_emissions_and_restores_filter(self):
        raw = pd.read_excel(quan.EDGAR, sheet_name="GHG_by_sector_and_country")
        raw = raw[raw.Substance.eq("CO2") & raw["EDGAR Country Code"].eq("ANT")]
        expected = raw.melt(id_vars=["Sector"], value_vars=[col for col in raw if str(col).isdigit()],
                            var_name="year", value_name="co2").rename(columns={"Sector": "sector"})
        expected = expected.sort_values(["year", "sector"]).reset_index(drop=True)
        actual = SECTOR_DATA[SECTOR_DATA.iso_alpha.eq("CUW")].sort_values(["year", "sector"]).reset_index(drop=True)
        pd.testing.assert_frame_equal(actual[["year", "sector", "co2"]], expected[["year", "sector", "co2"]],
                                      check_dtype=False, check_exact=False, rtol=1e-12, atol=1e-12)
        self.assertTrue(actual.source_iso_alpha.eq("ANT").all())
        self.assertFalse(loc_du_lieu_nganh(loc_du_lieu("2020-2024", country="CUW")).empty)

    def test_combined_region_is_not_assigned_to_either_country(self):
        for code in ["SRB", "MNE"]:
            selected = loc_du_lieu_nganh(loc_du_lieu("1970-2024", country=code))
            self.assertFalse(selected.iso_alpha.eq("SCG").any())
        europe = loc_du_lieu_nganh(loc_du_lieu("1970-2024", continent="Europe"))
        self.assertTrue(europe.iso_alpha.eq("SCG").any())
        combined = SECTOR_DATA[SECTOR_DATA.iso_alpha.eq("SCG")]
        self.assertTrue(combined.entity_type.eq("combined_region").all())
        self.assertTrue(combined.continent.eq("Europe").all())

    def test_incomplete_sector_shares_keep_null_and_disclose_coverage(self):
        raw = pd.DataFrame({"Substance": ["CO2"] * 3, "Country": ["Example"] * 3,
                            "EDGAR Country Code": ["AAA"] * 3,
                            "Sector": ["Power Industry", "Transport", "Buildings"],
                            2000: [10., 30., np.nan]})
        with patch.object(quan.pd, "read_excel", return_value=raw):
            cleaned, report = quan.clean_edgar({"AAA": "Asia"})
        self.assertEqual(cleaned.co2.isna().sum(), 1)
        self.assertEqual(cleaned.sector_share_percent.isna().sum(), 1)
        self.assertTrue(cleaned.sectors_available.eq(2).all())
        self.assertTrue(cleaned.sectors_expected.eq(3).all())
        self.assertEqual(report["incomplete_country_years"], 1)
        self.assertIn("1/1", sector_coverage_note(cleaned))

    def test_renewable_note_reports_changing_country_coverage(self):
        frame = pd.DataFrame({"year": [2023, 2023, 2024, 2024], "renewable_percent": [10., 20., 11., np.nan]})
        note = renewable_coverage_note(frame)
        self.assertIn("2024: 1", note)
        self.assertIn("1–2", note)


class ModelTimeDependenceTests(unittest.TestCase):
    def test_block_bootstrap_is_reproducible_and_changes_independent_error_band(self):
        scenario = model.tao_kich_ban(MODEL_INFO, MODEL_INFO["recent_annual_rate"])
        x = scenario.cumulative_co2.to_numpy() / 1000
        first = model.tinh_khoang_du_doan(MODEL_INFO, x)
        second = model.tinh_khoang_du_doan(MODEL_INFO, x)
        np.testing.assert_array_equal(first, second)
        independent = model.tinh_khoang_du_doan({**MODEL_INFO, "bootstrap_block_length": 1}, x)
        self.assertGreater(first[1, -1] - first[0, -1], independent[1, -1] - independent[0, -1])
        np.testing.assert_allclose(scenario.temperature_prediction,
                                   MODEL_INFO["intercept"] + MODEL_INFO["coefficient"] * x)
        self.assertEqual(MODEL_INFO["interval_method"], "circular_block_residual_bootstrap")
        self.assertEqual(
            MODEL_INFO["bootstrap_block_length"],
            model.chon_do_dai_khoi(MODEL_INFO["bootstrap_residuals"]),
        )

    def test_backtest_intervals_use_training_residuals_only(self):
        data = pd.read_csv(model.INPUT)
        data["target"] = data.temperature_anomaly.rolling(5).mean()
        data = data.dropna(subset=["target"])
        train, test = data[data.year.le(2014)], data[data.year.gt(2014)]
        x = train[["cumulative_co2"]].to_numpy() / 1000
        fitted = LinearRegression().fit(x, train.target)
        info = model.tao_thong_so_khoang_du_doan(x, train.target, fitted)
        self.assertEqual(info["sample_size"], 131)
        self.assertLess(max(info["bootstrap_x"]), min(test.cumulative_co2 / 1000))
        bounds = model.tinh_khoang_du_doan(info, test.cumulative_co2.to_numpy() / 1000)
        saved = pd.read_csv(model.OUTPUT / "du_doan_kiem_tra.csv")
        np.testing.assert_allclose(saved[["lower_90", "upper_90"]].to_numpy().T, bounds)

    def test_rolling_validation_uses_only_previous_years(self):
        data = pd.read_csv(model.INPUT)
        data["target"] = data.temperature_anomaly.rolling(5).mean()
        data = data.dropna(subset=["target"])
        validation = pd.read_csv(model.OUTPUT / "danh_gia_cuon_chieu.csv")
        self.assertEqual(len(validation), 4)
        self.assertEqual(validation.test_start.tolist(), [1995, 2000, 2005, 2010])
        self.assertTrue(validation.test_end.le(model.NAM_CHIA).all())
        for row in validation.itertuples():
            train = data[data.year.le(row.train_end)]
            test = data[data.year.between(row.test_start, row.test_end)]
            self.assertLess(row.train_end, row.test_start)
            fitted = LinearRegression().fit(train[["cumulative_co2"]] / 1000, train.target)
            actual = mean_absolute_error(test.target, fitted.predict(test[["cumulative_co2"]] / 1000))
            self.assertAlmostEqual(row.mae, actual)
        self.assertAlmostEqual(MODEL_INFO["rolling_validation_mae"], np.average(validation.mae, weights=validation.test_size))

    def test_history_selection_cannot_see_holdout_temperatures(self):
        data = pd.read_csv(model.INPUT)
        data["temperature_trend_5y"] = data.temperature_anomaly.rolling(5).mean()
        data = data.dropna(subset=["temperature_trend_5y"])
        selected, comparison, _ = model.chon_giai_doan_huan_luyen(data)
        changed = data.copy()
        changed.loc[changed.year.gt(model.NAM_CHIA), "temperature_trend_5y"] = 999
        repeated, same, _ = model.chon_giai_doan_huan_luyen(changed)
        self.assertEqual(selected, repeated)
        pd.testing.assert_frame_equal(comparison, same)
        self.assertEqual(selected, MODEL_INFO["selected_history_start"])
        self.assertEqual(selected, int(comparison.loc[comparison.mae.idxmin(), "history_start"]))
        self.assertTrue(comparison.validation_end.eq(2014).all())
        self.assertTrue(comparison.validation_start.eq(1995).all())


if __name__ == "__main__":
    unittest.main()
