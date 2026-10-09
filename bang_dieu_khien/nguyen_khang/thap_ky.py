"""Tổng hợp thập kỷ từ dữ liệu năm, giữ nguyên ý nghĩa giá trị thiếu."""


def tuy_chon_thap_ky(start, end):
    options = [{"label": f"Toàn bộ · {start}–{end}", "value": f"{start}-{end}"}]
    for decade in range(start // 10 * 10, end + 1, 10):
        first, last = max(decade, start), min(decade + 9, end)
        label = f"{first}–{last}" + (" (chưa đủ 10 năm)" if last - first < 9 else "")
        options.append({"label": label, "value": f"{first}-{last}"})
    return options


def nhan_thap_ky(frame):
    periods = frame.groupby(frame.year // 10 * 10).year.agg(["min", "max"])
    return {int(decade): f"{int(row['min'])}–{int(row['max'])}"
            for decade, row in periods.iterrows()}


def trung_binh_quoc_gia_theo_thap_ky(frame, field):
    labels = nhan_thap_ky(frame)
    grouped = frame.assign(decade=frame.year // 10 * 10).groupby(
        ["decade", "iso_alpha", "country"], as_index=False,
    )
    result = grouped.agg(**{field: (field, "mean"), "years": (field, "count")})
    result["period"] = result.decade.map(labels)
    return result.dropna(subset=[field]).sort_values(["decade", "iso_alpha"])
