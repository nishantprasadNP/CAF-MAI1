from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score


def compute_intersectional_metrics(df, y_true, y_pred, bias_columns):
    if not bias_columns:
        return {}

    df = df.reset_index(drop=True)
    y_true = y_true.reset_index(drop=True)
    y_pred = y_pred.reset_index(drop=True)

    grouped = df.groupby(bias_columns)
    results = {}

    for key, g in grouped:
        idx = g.index
        yt = y_true.iloc[idx]
        yp = y_pred.iloc[idx]

        name = "|".join(map(str, key)) if isinstance(key, tuple) else str(key)

        results[name] = {
            "accuracy": accuracy_score(yt, yp),
            "precision": precision_score(yt, yp, zero_division=0),
            "recall": recall_score(yt, yp, zero_division=0),
            "f1": f1_score(yt, yp, zero_division=0),
        }

    return results