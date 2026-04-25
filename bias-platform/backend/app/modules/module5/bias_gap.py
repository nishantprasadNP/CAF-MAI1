def compute_bias_gap(subgroup_metrics):
    bias_gap = {}
    metric_names = ("accuracy", "precision", "recall", "f1")

    for bias_column, subgroup_data in subgroup_metrics.items():
        column_gaps = {}

        for metric in metric_names:
            values = [
                subgroup_metrics_dict.get(metric)
                for subgroup_metrics_dict in subgroup_data.values()
                if isinstance(subgroup_metrics_dict.get(metric), (int, float))
            ]

            if values:
                column_gaps[f"{metric}_gap"] = max(values) - min(values)

        if column_gaps:
            bias_gap[bias_column] = column_gaps

    return bias_gap