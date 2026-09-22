from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
GLOBAL_DATA = ROOT / "processed" / "nguyen_khang" / "khi_hau_toan_cau_nam.csv"
OUT = ROOT / "outputs" / "nguyen_khang"
TRAIN_END = 2014
TEST_START = 2015
FORECAST_END = 2050

def fit_linear(x: pd.Series, y: pd.Series) -> tuple[float, float]:
    x_values = x.to_numpy(dtype=float)
    y_values = y.to_numpy(dtype=float)
    design = np.column_stack([np.ones(len(x_values)), x_values])
    (intercept, slope), *_ = np.linalg.lstsq(design, y_values, rcond=None)
    return float(intercept), float(slope)

def predict(x: pd.Series | np.ndarray, intercept: float, slope: float) -> np.ndarray:
    return intercept + slope * np.asarray(x, dtype=float)

def evaluate(actual: pd.Series, predicted: np.ndarray) -> dict[str, float]:
    errors = actual.to_numpy(dtype=float) - predicted
    denominator = np.square(actual - actual.mean()).sum()
    return {
        "mae": round(float(np.abs(errors).mean()), 4),
        "rmse": round(float(np.sqrt(np.square(errors).mean())), 4),
        "r2": round(float(1 - np.square(errors).sum() / denominator), 4),
    }

def train_models(data: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    model_data = data.dropna(
        subset=["temperature_anomaly", "year", "cumulative_co2"]
    ).copy()
    train = model_data[model_data["year"] <= TRAIN_END]
    test = model_data[model_data["year"] >= TEST_START]
    comparison: dict[str, dict] = {}
    predictions = model_data[["year", "temperature_anomaly"]].copy()

    for name, feature in [
        ("year_linear", "year"),
        ("cumulative_co2_linear", "cumulative_co2"),
    ]:
        intercept, slope = fit_linear(train[feature], train["temperature_anomaly"])
        test_prediction = predict(test[feature], intercept, slope)
        comparison[name] = {
            "feature": feature,
            "train_period": [int(train.year.min()), int(train.year.max())],
            "test_period": [int(test.year.min()), int(test.year.max())],
            "intercept": intercept,
            "slope": slope,
            **evaluate(test["temperature_anomaly"], test_prediction),
        }
        predictions[f"prediction_{name}"] = predict(
            model_data[feature], intercept, slope
        )

    selected = min(comparison, key=lambda key: comparison[key]["rmse"])
    comparison["selected_model"] = selected
    comparison["selection_rule"] = "RMSE thấp nhất trên tập kiểm tra 2015–2024"
    return comparison, predictions

def build_scenarios(data: pd.DataFrame, model: dict) -> pd.DataFrame:
    last = data.dropna(subset=["co2", "cumulative_co2"]).iloc[-1]
    recent = data[data["year"].between(2005, int(last.year))].dropna(subset=["co2"])
    trend_intercept, trend_slope = fit_linear(recent["year"], recent["co2"])
    future_years = np.arange(int(last.year) + 1, FORECAST_END + 1)
    last_emission = float(last.co2)

    pathways = {
        "Xu hướng hiện tại": np.maximum(
            predict(future_years, trend_intercept, trend_slope), 0
        ),
        "Giữ ổn định": np.full(len(future_years), last_emission),
        "Giảm 3% mỗi năm": last_emission * np.power(0.97, future_years - int(last.year)),
    }
    rows = []
    for scenario, emissions in pathways.items():
        cumulative = float(last.cumulative_co2) + np.cumsum(emissions)
        temperatures = predict(cumulative, model["intercept"], model["slope"])
        for year, co2, total, temperature in zip(
            future_years, emissions, cumulative, temperatures
        ):
            rows.append({
                "scenario": scenario,
                "year": int(year),
                "co2": round(float(co2), 3),
                "cumulative_co2": round(float(total), 3),
                "temperature_prediction": round(float(temperature), 4),
            })
    return pd.DataFrame(rows)

def main() -> None:
    data = pd.read_csv(GLOBAL_DATA)
    comparison, historical_predictions = train_models(data)
    selected_name = comparison["selected_model"]
    selected_model = comparison[selected_name]
    scenarios = build_scenarios(data, selected_model)

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "so_sanh_mo_hinh.json").write_text(
        json.dumps(comparison, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    historical_predictions.to_csv(OUT / "du_doan_tap_kiem_tra.csv", index=False)
    scenarios.to_csv(OUT / "kich_ban_nhiet_do_2050.csv", index=False)
    print(
        f"OK: selected={selected_name}, "
        f"test_RMSE={selected_model['rmse']:.4f}, scenarios={len(scenarios)}"
    )

if __name__ == "__main__":
    main()
