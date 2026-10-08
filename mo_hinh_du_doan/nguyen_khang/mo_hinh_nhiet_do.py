import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "data/du_lieu_da_xu_ly/nguyen_khang/khi_hau_toan_cau_nam.csv"
OUTPUT = ROOT / "data/ket_qua_mo_hinh/nguyen_khang"

NAM_CHIA = 2014
NAM_CUOI = 2050
BOOTSTRAP_SAMPLES = 2000
BOOTSTRAP_SEED = 18
HISTORY_STARTS = (1880, 1961, 1970)


def choose_block_length(residuals, minimum=5, maximum=15):
    """Chọn khối đủ dài để tự tương quan phần dư giảm về mức nhiễu."""
    residuals = pd.Series(np.asarray(residuals, dtype=float))
    threshold = 1.96 / np.sqrt(len(residuals))
    last_lag = min(maximum, len(residuals) - 1)
    for lag in range(minimum, last_lag + 1):
        if abs(residuals.autocorr(lag)) <= threshold:
            return lag
    return last_lag


def interval_parameters(x, y, fitted):
    x = np.asarray(x, dtype=float).reshape(-1)
    residuals = np.asarray(y, dtype=float) - fitted.predict(x.reshape(-1, 1))
    return {
        "intercept": float(fitted.intercept_),
        "coefficient": float(fitted.coef_[0]),
        "sample_size": len(x),
        "x_mean": float(x.mean()),
        "sxx": float(np.square(x - x.mean()).sum()),
        "residual_lag1_correlation": float(pd.Series(residuals).autocorr()),
        "bootstrap_x": x.tolist(),
        "bootstrap_residuals": residuals.tolist(),
        "bootstrap_samples": BOOTSTRAP_SAMPLES,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "bootstrap_block_length": choose_block_length(residuals),
        "interval_method": "circular_block_residual_bootstrap",
    }


def residual_diagnostics(x, y, fitted, years):
    """Tạo bảng phần dư và các kiểm tra hồi quy được dùng trong bài giảng."""
    from scipy.stats import chi2, shapiro
    from sklearn.linear_model import LinearRegression

    x = np.asarray(x, dtype=float).reshape(-1)
    y = np.asarray(y, dtype=float)
    predicted = fitted.predict(x.reshape(-1, 1))
    residuals = y - predicted
    n = len(x)
    centered_x = x - x.mean()
    leverage = 1 / n + np.square(centered_x) / np.square(centered_x).sum()
    residual_mse = np.square(residuals).sum() / (n - 2)
    cooks = np.square(residuals) / (2 * residual_mse) * leverage / np.square(1 - leverage)

    auxiliary = LinearRegression().fit(predicted.reshape(-1, 1), np.square(residuals))
    bp_statistic = n * auxiliary.score(predicted.reshape(-1, 1), np.square(residuals))
    durbin_watson = np.square(np.diff(residuals)).sum() / np.square(residuals).sum()
    table = pd.DataFrame({
        "year": np.asarray(years, dtype=int),
        "cumulative_co2_gt": x,
        "temperature_actual": y,
        "temperature_fitted": predicted,
        "residual": residuals,
        "leverage": leverage,
        "cooks_distance": cooks,
        "influential": cooks > 4 / n,
    })
    largest = table.loc[table.cooks_distance.idxmax()]
    metrics = {
        "train_durbin_watson": float(durbin_watson),
        "train_breusch_pagan_p": float(chi2.sf(bp_statistic, 1)),
        "train_shapiro_p": float(shapiro(residuals).pvalue),
        "train_influential_count": int(table.influential.sum()),
        "train_max_cooks_distance": float(largest.cooks_distance),
        "train_max_cooks_year": int(largest.year),
    }
    return table, metrics


def prediction_interval(info, x):
    x = np.asarray(x, dtype=float).reshape(-1)
    observed_x = np.asarray(info["bootstrap_x"], dtype=float)
    residuals = np.asarray(info["bootstrap_residuals"], dtype=float)
    residuals = (residuals - residuals.mean()) * np.sqrt(len(residuals) / (len(residuals) - 2))
    block = info["bootstrap_block_length"]
    rng = np.random.default_rng(info["bootstrap_seed"])

    def draw(length):
        blocks = (length + block - 1) // block
        starts = rng.integers(0, len(residuals), size=(info["bootstrap_samples"], blocks))
        indices = (starts[..., None] + np.arange(block)) % len(residuals)
        return residuals[indices].reshape(info["bootstrap_samples"], -1)[:, :length]

    simulated_errors = draw(len(observed_x))
    slope_change = (simulated_errors @ (observed_x - info["x_mean"])) / info["sxx"]
    intercept_change = simulated_errors.mean(axis=1) - slope_change * info["x_mean"]
    predictions = (
        info["intercept"] + intercept_change[:, None]
        + (info["coefficient"] + slope_change[:, None]) * x[None, :]
        + draw(len(x))
    )
    return np.quantile(predictions, [0.05, 0.95], axis=0)


def kich_ban(info, toc_do_nam, ma="custom", ten=None):
    if not np.isfinite(toc_do_nam) or toc_do_nam < -1:
        raise ValueError("Mức thay đổi CO₂ phải hữu hạn và không thấp hơn −100%/năm.")
    nam_goc = info["full_period"][1]
    nam = np.arange(nam_goc + 1, NAM_CUOI + 1)
    co2 = info["last_co2"] * (1 + toc_do_nam) ** (nam - nam_goc)
    tich_luy = info["last_cumulative_co2"] + np.cumsum(co2)
    x = tich_luy / 1000
    du_bao = info["intercept"] + info["coefficient"] * x
    lower, upper = prediction_interval(info, x)
    return pd.DataFrame({
        "scenario_id": ma, "scenario": ten or f"Tùy chỉnh {toc_do_nam * 100:+.1f}%/năm",
        "annual_change_pct": toc_do_nam * 100, "year": nam,
        "co2": co2, "cumulative_co2": tich_luy,
        "extrapolation_ratio": tich_luy / info["last_cumulative_co2"],
        "temperature_prediction": du_bao,
        "lower_90": lower, "upper_90": upper,
    })


def rolling_validation(data):
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import mean_absolute_error, mean_squared_error

    rows = []
    # Cùng bốn giai đoạn 1995–2014 để so sánh các độ dài lịch sử công bằng.
    # Không dùng 2015–2024 để chọn giai đoạn huấn luyện.
    for cut in range(1994, NAM_CHIA, 5):
        train = data[data.year.le(cut)]
        test = data[data.year.between(cut + 1, cut + 5)]
        if len(train) < 20 or len(test) != 5:
            raise ValueError("Mỗi lần kiểm tra cần ít nhất 20 năm học và đủ 5 năm đánh giá.")
        x = train[["cumulative_co2"]].to_numpy() / 1000
        fitted = LinearRegression().fit(x, train.temperature_trend_5y)
        actual = test.temperature_trend_5y
        predicted = fitted.predict(test[["cumulative_co2"]].to_numpy() / 1000)
        parameters = interval_parameters(x, train.temperature_trend_5y, fitted)
        lower, upper = prediction_interval(parameters, test.cumulative_co2.to_numpy() / 1000)
        baseline = LinearRegression().fit(train[["year"]], train.temperature_trend_5y)
        baseline_prediction = baseline.predict(test[["year"]])
        rows.append({
            "train_end": cut,
            "test_start": int(test.year.min()),
            "test_end": int(test.year.max()),
            "test_size": len(test),
            "mae": float(mean_absolute_error(actual, predicted)),
            "rmse": float(np.sqrt(mean_squared_error(actual, predicted))),
            "time_baseline_mae": float(mean_absolute_error(actual, baseline_prediction)),
            "persistence_mae": float(np.abs(actual - train.temperature_trend_5y.iloc[-1]).mean()),
            "interval_coverage": float(actual.between(lower, upper).mean()),
        })
    return pd.DataFrame(rows)


def select_history(data):
    results, rows = {}, []
    for start in HISTORY_STARTS:
        validation = rolling_validation(data[data.year.between(start, NAM_CHIA)])
        results[start] = validation
        rows.append({
            "history_start": start,
            "validation_start": 1995,
            "validation_end": NAM_CHIA,
            "mae": float(validation.mae.mean()),
            "rmse": float(np.sqrt(np.square(validation.rmse).mean())),
            "time_baseline_mae": float(validation.time_baseline_mae.mean()),
            "persistence_mae": float(validation.persistence_mae.mean()),
        })
    comparison = pd.DataFrame(rows)
    selected = int(comparison.loc[comparison.mae.idxmin(), "history_start"])
    return selected, comparison, results[selected]


def main():
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

    df = pd.read_csv(INPUT).sort_values("year")
    cols = ["year", "temperature_anomaly", "co2", "cumulative_co2"]
    if not np.isfinite(df[cols]).all().all() or not df.year.diff().iloc[1:].eq(1).all():
        raise ValueError("Dữ liệu phải đầy đủ, mỗi năm đúng một quan sát.")
    data = df.assign(temperature_trend_5y=df.temperature_anomaly.rolling(5).mean())
    data = data.dropna(subset=["temperature_trend_5y"])
    selected_start, comparison, validation = select_history(data)
    data = data[data.year.ge(selected_start)]
    x, y = data[["cumulative_co2"]].to_numpy() / 1000, data.temperature_trend_5y
    train = data.year <= NAM_CHIA
    test = ~train

    # Đánh giá trên 2015–2024 trước khi học lại bằng toàn bộ dữ liệu.
    model = LinearRegression().fit(x[train], y[train])
    prediction = model.predict(x[test])
    train_parameters = interval_parameters(x[train], y[train], model)
    lower_test, upper_test = prediction_interval(train_parameters, x[test])
    residuals, diagnostics = residual_diagnostics(
        x[train], y[train], model, data.loc[train, "year"]
    )
    baseline_start = int(comparison.loc[comparison.time_baseline_mae.idxmin(), "history_start"])
    baseline_train = train & data.year.ge(baseline_start)
    time_model = LinearRegression().fit(data.loc[baseline_train, ["year"]], y[baseline_train])
    time_prediction = time_model.predict(data.loc[test, ["year"]])
    test_mse = mean_squared_error(y[test], prediction)
    validation_weights = validation.test_size
    info = {
        "model": "Linear Regression",
        "formula": "temperature_trend_5y = intercept + coefficient × cumulative_co2_gt",
        "train_period": [int(data.year.min()), NAM_CHIA],
        "test_period": [int(data.year[test].min()), int(data.year.max())],
        "full_period": [int(data.year.min()), int(data.year.max())],
        "source_period": [int(df.year.min()), int(df.year.max())],
        "selected_history_start": selected_start,
        "selection_period": [1995, NAM_CHIA],
        "r2_train": float(r2_score(y[train], model.predict(x[train]))),
        "r2_test": float(r2_score(y[test], prediction)),
        "mae_test": float(mean_absolute_error(y[test], prediction)),
        "mse_test": float(test_mse),
        "rmse_test": float(np.sqrt(test_mse)),
        "train_size": int(train.sum()),
        "test_size": int(test.sum()),
        "time_baseline_mae_test": float(mean_absolute_error(y[test], time_prediction)),
        "time_baseline_start": baseline_start,
        "persistence_mae_test": float(np.abs(y[test] - y[train].iloc[-1]).mean()),
        "test_interval_coverage": float(y[test].between(lower_test, upper_test).mean()),
        "target_window_years": 5,
        "rolling_validation_mae": float(np.average(validation.mae, weights=validation_weights)),
        "rolling_interval_coverage": float(np.average(
            validation.interval_coverage, weights=validation_weights
        )),
        **diagnostics,
    }

    # Fit lại bằng 1884–2024 để tạo ba kịch bản tương lai.
    model.fit(x, y)
    recent = df.set_index("year").co2.tail(20)
    years = recent.index[-1] - recent.index[0]
    rate = float((recent.iloc[-1] / recent.iloc[0]) ** (1 / years) - 1)
    info.update({
        **interval_parameters(x, y, model),
        "last_co2": float(df.co2.iloc[-1]),
        "last_cumulative_co2": float(df.cumulative_co2.iloc[-1]),
        "recent_annual_rate": rate,
    })
    backtest = data.loc[test, ["year", "temperature_anomaly", "temperature_trend_5y"]]
    backtest = backtest.assign(
        temperature_prediction=prediction,
        lower_90=lower_test,
        upper_90=upper_test,
    )
    scenarios = pd.concat([
        kich_ban(info, rate, "trend", "Tiếp diễn xu hướng"),
        kich_ban(info, 0, "stable", "Giữ mức 2024"),
        kich_ban(info, -.05, "decline", "Giảm 5%/năm"),
    ], ignore_index=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    backtest.to_csv(OUTPUT / "du_doan_kiem_tra.csv", index=False)
    residuals.to_csv(OUTPUT / "phan_du_huan_luyen.csv", index=False)
    scenarios.to_csv(OUTPUT / "kich_ban_2050.csv", index=False)
    validation.to_csv(OUTPUT / "danh_gia_cuon_chieu.csv", index=False)
    comparison.to_csv(OUTPUT / "so_sanh_giai_doan_huan_luyen.csv", index=False)
    (OUTPUT / "thong_tin_mo_hinh.json").write_text(
        json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK: R² test={info['r2_test']:.3f}, MAE test={info['mae_test']:.3f} °C")


if __name__ == "__main__":
    main()
