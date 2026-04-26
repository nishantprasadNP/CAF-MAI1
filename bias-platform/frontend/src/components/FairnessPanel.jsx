function FairnessPanel({ data, debias }) {
  if (!data) return null;

  const summary = data.summary || {};

  const accuracy = data.accuracy ?? 0;
  const f1 = data.f1 ?? 0;

  const biasGap = summary.bias_gap ?? 0;
  const fairnessCount = data.num_fairness_metrics ?? 0;

  const before = debias?.before;
  const after = debias?.after;
  const improvement = debias?.improvement;

  return (
    <div className="result-card wide">
      <h3>Model + Fairness Summary</h3>

      <div className="summary-grid">
        <p>
          <strong>Accuracy:</strong> {(accuracy * 100).toFixed(1)}%
        </p>

        <p>
          <strong>F1:</strong> {(f1 * 100).toFixed(1)}%
        </p>

        <p>
          <strong>Bias Gap:</strong>{" "}
          <span style={{ color: biasGap > 0.2 ? "red" : "green" }}>
            {biasGap.toFixed(2)}
          </span>
        </p>

        <p>
          <strong>Fairness Metrics:</strong> {fairnessCount}
        </p>
      </div>

      <h4>Debiasing Impact</h4>

      <div className="summary-grid">
        <p>
          <strong>Before Fairness:</strong>{" "}
          {typeof before === "number" ? before.toFixed(2) : "No data"}
        </p>

        <p>
          <strong>After Fairness:</strong>{" "}
          {typeof after === "number" ? after.toFixed(2) : "No data"}
        </p>

        <p>
          <strong>Improvement:</strong>{" "}
          {debias?.changed === false
            ? "Not required (already fair)"
            : typeof improvement === "number"
            ? improvement.toFixed(2)
            : "No significant change detected"}
        </p>
      </div>
    </div>
  );
}

export default FairnessPanel;