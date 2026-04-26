import pandas as pd


def compute_subgroup_metrics(df, y_true, y_pred, bias_columns):
    if not bias_columns:
        return {}

    df = df.reset_index(drop=True)
    y_pred = pd.Series(y_pred).reset_index(drop=True)

    results = {}

    for col in bias_columns:
        if col not in df.columns:
            continue

        grouped = df.groupby(col)
        col_metrics = {}

        for val, g in grouped:
            idx = g.index

            preds = y_pred.iloc[idx]

            # 🔥 CRITICAL: positive prediction rate
            positive_rate = (preds == 1).mean()

            col_metrics[str(val)] = {
                "positive_rate": float(positive_rate),
                "count": int(len(preds)),
            }

        results[col] = col_metrics

    return results