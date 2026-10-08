"""Tổng hợp thập kỷ từ dữ liệu năm, giữ nguyên ý nghĩa giá trị thiếu."""


def decade_options(start, end):
    options = [{"label": f"Toàn bộ · {start}–{end}", "value": f"{start}-{end}"}]
    for decade in range(start // 10 * 10, end + 1, 10):
        first, last = max(decade, start), min(decade + 9, end)
        label = f"{first}–{last}" + (" (chưa đủ 10 năm)" if last - first < 9 else "")
        options.append({"label": label, "value": f"{first}-{last}"})
    return options


def decade_labels(frame):
    periods = frame.groupby(frame.year // 10 * 10).year.agg(["min", "max"])
    return {int(decade): f"{int(row['min'])}–{int(row['max'])}"
            for decade, row in periods.iterrows()}


def country_decade_means(frame, field):
    labels = decade_labels(frame)
    grouped = frame.assign(decade=frame.year // 10 * 10).groupby(
        ["decade", "iso_alpha", "country"], as_index=False,
    )
    result = grouped.agg(**{field: (field, "mean"), "years": (field, "count")})
    result["period"] = result.decade.map(labels)
    return result.dropna(subset=[field]).sort_values(["decade", "iso_alpha"])
