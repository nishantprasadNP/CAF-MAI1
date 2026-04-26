def compute_bias_gap(subgroup_metrics):
    bias_gap = {}

    for col, groups in subgroup_metrics.items():
        rates = []

        for g in groups.values():
            val = g.get("positive_rate")
            if isinstance(val, (int, float)):
                rates.append(float(val))

        if not rates:
            continue

        # 🔹 BASIC GAP
        max_v = max(rates)
        min_v = min(rates)
        raw_gap = max_v - min_v

        # 🔹 ROBUST GAP (pairwise avg difference)
        if len(rates) > 1:
            diffs = [
                abs(rates[i] - rates[j])
                for i in range(len(rates))
                for j in range(i + 1, len(rates))
            ]
            robust_gap = sum(diffs) / len(diffs)
        else:
            robust_gap = raw_gap

        # 🔹 FINAL GAP (blend + clamp)
        gap = 0.7 * raw_gap + 0.3 * robust_gap

        # 🔥 CLAMP to avoid unrealistic 1.0 spikes
        gap = min(max(gap, 0.0), 0.95)

        bias_gap[col] = {
            "gap": round(gap, 4),
            "raw_gap": round(raw_gap, 4),
            "robust_gap": round(robust_gap, 4),
            "group_rates": {
                str(k): round(v.get("positive_rate", 0.0), 4)
                for k, v in groups.items()
            }
        }

    return bias_gap