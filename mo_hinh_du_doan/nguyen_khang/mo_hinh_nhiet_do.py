import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "data/du_lieu_da_xu_ly/nguyen_khang/khi_hau_toan_cau_nam.csv"
OUTPUT = ROOT / "data/ket_qua_mo_hinh/nguyen_khang"

NAM_CHIA = 2014
NAM_CUOI = 2050


def kich_ban(info, toc_do_nam, ma="custom", ten=None):
    if not np.isfinite(toc_do_nam) or toc_do_nam < -1:
        raise ValueError("Mức thay đổi CO₂ phải hữu hạn và không thấp hơn −100%/năm.")
    nam_goc = info["full_period"][1]
    nam = np.arange(nam_goc + 1, NAM_CUOI + 1)
    co2 = info["last_co2"] * (1 + toc_do_nam) ** (nam - nam_goc)
    tich_luy = info["last_cumulative_co2"] + np.cumsum(co2)
    x = tich_luy / 1000
    du_bao = info["intercept"] + info["coefficient"] * x
    sai_so = info["residual_std"] * np.sqrt(
        1 + 1 / info["sample_size"] + (x - info["x_mean"]) ** 2 / info["sxx"]
    )
    return pd.DataFrame({
        "scenario_id": ma, "scenario": ten or f"Tùy chỉnh {toc_do_nam * 100:+.1f}%/năm",
        "annual_change_pct": toc_do_nam * 100, "year": nam,
        "co2": co2, "cumulative_co2": tich_luy,
        "temperature_prediction": du_bao,
        "lower_90": du_bao - info["critical_90"] * sai_so,
        "upper_90": du_bao + info["critical_90"] * sai_so,
    })


def main():
    from scipy.stats import t
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

    df = pd.read_csv(INPUT).sort_values("year")
    cols = ["year", "temperature_anomaly", "co2", "cumulative_co2"]
    if not np.isfinite(df[cols]).all().all() or not df.year.diff().iloc[1:].eq(1).all():
        raise ValueError("Dữ liệu phải đầy đủ, mỗi năm đúng một quan sát.")
    data = df.assign(temperature_trend_5y=df.temperature_anomaly.rolling(5).mean()).dropna(subset=cols + ["temperature_trend_5y"])
    x, y = data[["cumulative_co2"]].to_numpy() / 1000, data.temperature_trend_5y
    train = data.year <= NAM_CHIA
    model = LinearRegression().fit(x[train], y[train])
    prediction = model.predict(x[~train])
    info = {
        "model": "Linear Regression",
        "formula": "temperature_trend_5y = intercept + coefficient × cumulative_co2_gt",
        "train_period": [int(data.year.min()), NAM_CHIA],
        "test_period": [int(data.year[~train].min()), int(data.year.max())],
        "full_period": [int(data.year.min()), int(data.year.max())],
        "r2_train": float(r2_score(y[train], model.predict(x[train]))),
        "r2_test": float(r2_score(y[~train], prediction)),
        "mae_test": float(mean_absolute_error(y[~train], prediction)),
        "rmse_test": float(np.sqrt(mean_squared_error(y[~train], prediction))),
    }
    model.fit(x, y)
    recent = df.set_index("year").co2.loc[2005:2024]
    rate = float((recent.iloc[-1] / recent.iloc[0]) ** (1 / (recent.index[-1] - recent.index[0])) - 1)
    info.update({
        "intercept": float(model.intercept_), "coefficient": float(model.coef_[0]),
        "sample_size": len(data), "critical_90": float(t.ppf(.95, len(data) - 2)),
        "residual_std": float(np.sqrt(((y - model.predict(x)) ** 2).sum() / (len(data) - 2))),
        "x_mean": float(x.mean()), "sxx": float(((x - x.mean()) ** 2).sum()),
        "last_co2": float(df.co2.iloc[-1]),
        "last_cumulative_co2": float(df.cumulative_co2.iloc[-1]),
        "recent_annual_rate": rate,
        "interval": "Dải OLS 90% xấp xỉ, giả định phần dư độc lập; chưa gồm bất định kịch bản",
    })
    backtest = data.loc[~train, ["year", "temperature_anomaly", "temperature_trend_5y"]]
    backtest = backtest.assign(temperature_prediction=prediction)
    scenarios = pd.concat([
        kich_ban(info, rate, "trend", "Tiếp diễn xu hướng"),
        kich_ban(info, 0, "stable", "Giữ mức 2024"),
        kich_ban(info, -.05, "decline", "Giảm 5%/năm"),
    ], ignore_index=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    backtest.to_csv(OUTPUT / "du_doan_kiem_tra.csv", index=False)
    scenarios.to_csv(OUTPUT / "kich_ban_2050.csv", index=False)
    (OUTPUT / "thong_tin_mo_hinh.json").write_text(
        json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK: R² test={info['r2_test']:.3f}, MAE test={info['mae_test']:.3f} °C")


if __name__ == "__main__":
    main()
