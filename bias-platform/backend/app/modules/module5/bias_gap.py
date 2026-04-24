def compute_bias_gap(subgroup_metrics):
    bias_gap = {}
    metric_names = ("accuracy", "precision", "recall", "f1")

    for bias_column, subgroup_data in subgroup_metrics.items():
        column_gaps = {}

        for metric in metric_names:
            values = []

            for subgroup_metrics_dict in subgroup_data.values():
                metric_value = subgroup_metrics_dict.get(metric)
                if metric_value is None:
                    continue
                values.append(metric_value)

            if values:
                column_gaps[f"{metric}_gap"] = max(values) - min(values)

        bias_gap[bias_column] = column_gaps

    return bias_gap
