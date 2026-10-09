import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "data/du_lieu_da_xu_ly/nguyen_khang/khi_hau_toan_cau_nam.csv"
OUTPUT = ROOT / "data/ket_qua_mo_hinh/nguyen_khang"

NAM_CHIA = 2014
NAM_CUOI = 2050
SO_LAN_BOOTSTRAP = 2000
HAT_GION_NGAU_NHIEN = 18
CAC_MOC_BAT_DAU = (1880, 1961, 1970)


def chon_do_dai_khoi(phan_du, toi_thieu=5, toi_da=15):
    """Chọn khối đủ dài để tự tương quan phần dư giảm về mức nhiễu."""
    phan_du = pd.Series(np.asarray(phan_du, dtype=float))
    nguong = 1.96 / np.sqrt(len(phan_du))
    do_dai_cuoi = min(toi_da, len(phan_du) - 1)
    for do_dai in range(toi_thieu, do_dai_cuoi + 1):
        if abs(phan_du.autocorr(do_dai)) <= nguong:
            return do_dai
    return do_dai_cuoi


def tao_thong_so_khoang_du_doan(x, y, mo_hinh):
    x = np.asarray(x, dtype=float).reshape(-1)
    phan_du = np.asarray(y, dtype=float) - mo_hinh.predict(x.reshape(-1, 1))
    return {
        "intercept": float(mo_hinh.intercept_), "coefficient": float(mo_hinh.coef_[0]),
        "sample_size": len(x), "x_mean": float(x.mean()),
        "sxx": float(np.square(x - x.mean()).sum()),
        "residual_lag1_correlation": float(pd.Series(phan_du).autocorr()),
        "bootstrap_x": x.tolist(), "bootstrap_residuals": phan_du.tolist(),
        "bootstrap_samples": SO_LAN_BOOTSTRAP, "bootstrap_seed": HAT_GION_NGAU_NHIEN,
        "bootstrap_block_length": chon_do_dai_khoi(phan_du),
        "interval_method": "circular_block_residual_bootstrap",
    }


def kiem_tra_phan_du(x, y, mo_hinh, cac_nam):
    """Tạo bảng phần dư và các kiểm tra hồi quy được dùng trong bài giảng."""
    from scipy.stats import chi2, shapiro

    x, y = np.asarray(x, dtype=float).reshape(-1), np.asarray(y, dtype=float)
    du_doan = mo_hinh.predict(x.reshape(-1, 1))
    phan_du = y - du_doan
    so_mau = len(x)
    centered_x = x - x.mean()
    leverage = 1 / so_mau + np.square(centered_x) / np.square(centered_x).sum()
    residual_mse = np.square(phan_du).sum() / (so_mau - 2)
    cooks = np.square(phan_du) / (2 * residual_mse) * leverage / np.square(1 - leverage)

    auxiliary = LinearRegression().fit(du_doan.reshape(-1, 1), np.square(phan_du))
    bp_statistic = so_mau * auxiliary.score(du_doan.reshape(-1, 1), np.square(phan_du))
    durbin_watson = np.square(np.diff(phan_du)).sum() / np.square(phan_du).sum()
    table = pd.DataFrame({
        "year": np.asarray(cac_nam, dtype=int), "cumulative_co2_gt": x,
        "temperature_actual": y, "temperature_fitted": du_doan,
        "residual": phan_du, "leverage": leverage,
        "cooks_distance": cooks, "influential": cooks > 4 / so_mau,
    })
    largest = table.loc[table.cooks_distance.idxmax()]
    return table, {
        "train_durbin_watson": float(durbin_watson),
        "train_breusch_pagan_p": float(chi2.sf(bp_statistic, 1)),
        "train_shapiro_p": float(shapiro(phan_du).pvalue),
        "train_influential_count": int(table.influential.sum()),
        "train_max_cooks_distance": float(largest.cooks_distance),
        "train_max_cooks_year": int(largest.year),
    }


def tinh_khoang_du_doan(thong_tin, x):
    x = np.asarray(x, dtype=float).reshape(-1)
    x_quan_sat = np.asarray(thong_tin["bootstrap_x"], dtype=float)
    phan_du = np.asarray(thong_tin["bootstrap_residuals"], dtype=float)
    phan_du = (phan_du - phan_du.mean()) * np.sqrt(len(phan_du) / (len(phan_du) - 2))
    do_dai_khoi = thong_tin["bootstrap_block_length"]
    bo_sinh_so = np.random.default_rng(thong_tin["bootstrap_seed"])

    def rut_mau_phan_du(do_dai):
        so_khoi = (do_dai + do_dai_khoi - 1) // do_dai_khoi
        diem_dau = bo_sinh_so.integers(0, len(phan_du),
                                      size=(thong_tin["bootstrap_samples"], so_khoi))
        chi_so = (diem_dau[..., None] + np.arange(do_dai_khoi)) % len(phan_du)
        return phan_du[chi_so].reshape(thong_tin["bootstrap_samples"], -1)[:, :do_dai]

    sai_so_mo_phong = rut_mau_phan_du(len(x_quan_sat))
    doi_he_so = (sai_so_mo_phong @ (x_quan_sat - thong_tin["x_mean"])) / thong_tin["sxx"]
    doi_he_so_chan = sai_so_mo_phong.mean(axis=1) - doi_he_so * thong_tin["x_mean"]
    cac_du_doan = (thong_tin["intercept"] + doi_he_so_chan[:, None]
                   + (thong_tin["coefficient"] + doi_he_so[:, None]) * x[None, :]
                   + rut_mau_phan_du(len(x)))
    return np.quantile(cac_du_doan, [0.05, 0.95], axis=0)


def tao_kich_ban(thong_tin, toc_do_nam, ma="custom", ten=None):
    if not np.isfinite(toc_do_nam) or toc_do_nam < -1:
        raise ValueError("Mức thay đổi CO₂ phải hữu hạn và không thấp hơn −100%/năm.")
    nam_goc = thong_tin["full_period"][1]
    nam = np.arange(nam_goc + 1, NAM_CUOI + 1)
    co2 = thong_tin["last_co2"] * (1 + toc_do_nam) ** (nam - nam_goc)
    tich_luy = thong_tin["last_cumulative_co2"] + np.cumsum(co2)
    x = tich_luy / 1000
    du_bao = thong_tin["intercept"] + thong_tin["coefficient"] * x
    lower, upper = tinh_khoang_du_doan(thong_tin, x)
    return pd.DataFrame({
        "scenario_id": ma, "scenario": ten or f"Tùy chỉnh {toc_do_nam * 100:+.1f}%/năm",
        "annual_change_pct": toc_do_nam * 100, "year": nam, "co2": co2,
        "cumulative_co2": tich_luy,
        "extrapolation_ratio": tich_luy / thong_tin["last_cumulative_co2"],
        "temperature_prediction": du_bao, "lower_90": lower, "upper_90": upper,
    })


def danh_gia_cuon_chieu(du_lieu):
    ket_qua = []
    # Dùng cùng bốn giai đoạn 1995–2014; không nhìn tập kiểm tra 2015–2024.
    for moc_chia in range(1994, NAM_CHIA, 5):
        huan_luyen = du_lieu[du_lieu.year.le(moc_chia)]
        kiem_tra = du_lieu[du_lieu.year.between(moc_chia + 1, moc_chia + 5)]
        if len(huan_luyen) < 20 or len(kiem_tra) != 5:
            raise ValueError("Mỗi lần kiểm tra cần ít nhất 20 năm học và đủ 5 năm đánh giá.")
        x = huan_luyen[["cumulative_co2"]].to_numpy() / 1000
        mo_hinh = LinearRegression().fit(x, huan_luyen.temperature_trend_5y)
        thuc_te = kiem_tra.temperature_trend_5y
        du_doan = mo_hinh.predict(kiem_tra[["cumulative_co2"]].to_numpy() / 1000)
        can_duoi, can_tren = tinh_khoang_du_doan(
            tao_thong_so_khoang_du_doan(x, huan_luyen.temperature_trend_5y, mo_hinh),
            kiem_tra.cumulative_co2.to_numpy() / 1000)
        mo_hinh_moc = LinearRegression().fit(huan_luyen[["year"]], huan_luyen.temperature_trend_5y)
        du_doan_moc = mo_hinh_moc.predict(kiem_tra[["year"]])
        ket_qua.append({
            "train_end": moc_chia, "test_start": int(kiem_tra.year.min()),
            "test_end": int(kiem_tra.year.max()), "test_size": len(kiem_tra),
            "mae": float(mean_absolute_error(thuc_te, du_doan)),
            "rmse": float(np.sqrt(mean_squared_error(thuc_te, du_doan))),
            "time_baseline_mae": float(mean_absolute_error(thuc_te, du_doan_moc)),
            "persistence_mae": float(np.abs(thuc_te - huan_luyen.temperature_trend_5y.iloc[-1]).mean()),
            "interval_coverage": float(thuc_te.between(can_duoi, can_tren).mean()),
        })
    return pd.DataFrame(ket_qua)


def chon_giai_doan_huan_luyen(du_lieu):
    cac_danh_gia, ket_qua = {}, []
    for nam_bat_dau in CAC_MOC_BAT_DAU:
        danh_gia = danh_gia_cuon_chieu(
            du_lieu[du_lieu.year.between(nam_bat_dau, NAM_CHIA)])
        cac_danh_gia[nam_bat_dau] = danh_gia
        ket_qua.append({
            "history_start": nam_bat_dau, "validation_start": 1995,
            "validation_end": NAM_CHIA, "mae": float(danh_gia.mae.mean()),
            "rmse": float(np.sqrt(np.square(danh_gia.rmse).mean())),
            "time_baseline_mae": float(danh_gia.time_baseline_mae.mean()),
            "persistence_mae": float(danh_gia.persistence_mae.mean()),
        })
    so_sanh = pd.DataFrame(ket_qua)
    duoc_chon = int(so_sanh.loc[so_sanh.mae.idxmin(), "history_start"])
    return duoc_chon, so_sanh, cac_danh_gia[duoc_chon]


def chay_mo_hinh():
    du_lieu_goc = pd.read_csv(INPUT).sort_values("year")
    cac_cot = ["year", "temperature_anomaly", "co2", "cumulative_co2"]
    if not np.isfinite(du_lieu_goc[cac_cot]).all().all() or not du_lieu_goc.year.diff().iloc[1:].eq(1).all():
        raise ValueError("Dữ liệu phải đầy đủ, mỗi năm đúng một quan sát.")
    du_lieu = du_lieu_goc.assign(
        temperature_trend_5y=du_lieu_goc.temperature_anomaly.rolling(5).mean()
    ).dropna(subset=["temperature_trend_5y"])
    nam_bat_dau, bang_so_sanh, danh_gia = chon_giai_doan_huan_luyen(du_lieu)
    du_lieu = du_lieu[du_lieu.year.ge(nam_bat_dau)]
    x = du_lieu[["cumulative_co2"]].to_numpy() / 1000
    y = du_lieu.temperature_trend_5y
    huan_luyen = du_lieu.year <= NAM_CHIA
    kiem_tra = ~huan_luyen

    # Đánh giá trên 2015–2024 trước khi học lại bằng toàn bộ dữ liệu.
    mo_hinh = LinearRegression().fit(x[huan_luyen], y[huan_luyen])
    du_doan = mo_hinh.predict(x[kiem_tra])
    thong_so_huan_luyen = tao_thong_so_khoang_du_doan(x[huan_luyen], y[huan_luyen], mo_hinh)
    can_duoi, can_tren = tinh_khoang_du_doan(thong_so_huan_luyen, x[kiem_tra])
    bang_phan_du, chi_so_phan_du = kiem_tra_phan_du(
        x[huan_luyen], y[huan_luyen], mo_hinh, du_lieu.loc[huan_luyen, "year"])
    nam_moc = int(bang_so_sanh.loc[bang_so_sanh.time_baseline_mae.idxmin(), "history_start"])
    du_lieu_moc = huan_luyen & du_lieu.year.ge(nam_moc)
    mo_hinh_moc = LinearRegression().fit(du_lieu.loc[du_lieu_moc, ["year"]], y[du_lieu_moc])
    du_doan_moc = mo_hinh_moc.predict(du_lieu.loc[kiem_tra, ["year"]])
    mse = mean_squared_error(y[kiem_tra], du_doan)
    thong_tin = {
        "model": "Linear Regression",
        "formula": "temperature_trend_5y = intercept + coefficient × cumulative_co2_gt",
        "train_period": [int(du_lieu.year.min()), NAM_CHIA],
        "test_period": [int(du_lieu.year[kiem_tra].min()), int(du_lieu.year.max())],
        "full_period": [int(du_lieu.year.min()), int(du_lieu.year.max())],
        "source_period": [int(du_lieu_goc.year.min()), int(du_lieu_goc.year.max())],
        "selected_history_start": nam_bat_dau, "selection_period": [1995, NAM_CHIA],
        "r2_train": float(r2_score(y[huan_luyen], mo_hinh.predict(x[huan_luyen]))),
        "r2_test": float(r2_score(y[kiem_tra], du_doan)),
        "mae_test": float(mean_absolute_error(y[kiem_tra], du_doan)),
        "mse_test": float(mse), "rmse_test": float(np.sqrt(mse)),
        "train_size": int(huan_luyen.sum()), "test_size": int(kiem_tra.sum()),
        "time_baseline_mae_test": float(mean_absolute_error(y[kiem_tra], du_doan_moc)),
        "time_baseline_start": nam_moc,
        "persistence_mae_test": float(np.abs(y[kiem_tra] - y[huan_luyen].iloc[-1]).mean()),
        "test_interval_coverage": float(y[kiem_tra].between(can_duoi, can_tren).mean()),
        "target_window_years": 5,
        "rolling_validation_mae": float(np.average(danh_gia.mae, weights=danh_gia.test_size)),
        "rolling_interval_coverage": float(np.average(
            danh_gia.interval_coverage, weights=danh_gia.test_size)),
        **chi_so_phan_du,
    }

    # Fit lại bằng 1884–2024 để tạo ba kịch bản tương lai.
    mo_hinh.fit(x, y)
    gan_day = du_lieu_goc.set_index("year").co2.tail(20)
    toc_do = float((gan_day.iloc[-1] / gan_day.iloc[0]) ** (1 / (gan_day.index[-1] - gan_day.index[0])) - 1)
    thong_tin.update({
        **tao_thong_so_khoang_du_doan(x, y, mo_hinh),
        "last_co2": float(du_lieu_goc.co2.iloc[-1]),
        "last_cumulative_co2": float(du_lieu_goc.cumulative_co2.iloc[-1]),
        "recent_annual_rate": toc_do,
    })
    bang_kiem_tra = du_lieu.loc[kiem_tra, [
        "year", "temperature_anomaly", "temperature_trend_5y"]].assign(
        temperature_prediction=du_doan, lower_90=can_duoi, upper_90=can_tren)
    cac_kich_ban = pd.concat([
        tao_kich_ban(thong_tin, toc_do, "trend", "Tiếp diễn xu hướng"),
        tao_kich_ban(thong_tin, 0, "stable", "Giữ mức 2024"),
        tao_kich_ban(thong_tin, -.05, "decline", "Giảm 5%/năm"),
    ], ignore_index=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    bang_kiem_tra.to_csv(OUTPUT / "du_doan_kiem_tra.csv", index=False)
    bang_phan_du.to_csv(OUTPUT / "phan_du_huan_luyen.csv", index=False)
    cac_kich_ban.to_csv(OUTPUT / "kich_ban_2050.csv", index=False)
    danh_gia.to_csv(OUTPUT / "danh_gia_cuon_chieu.csv", index=False)
    bang_so_sanh.to_csv(OUTPUT / "so_sanh_giai_doan_huan_luyen.csv", index=False)
    (OUTPUT / "thong_tin_mo_hinh.json").write_text(
        json.dumps(thong_tin, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK: R² test={thong_tin['r2_test']:.3f}, MAE test={thong_tin['mae_test']:.3f} °C")


if __name__ == "__main__":
    chay_mo_hinh()
