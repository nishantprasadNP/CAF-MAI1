function FairnessPanel({ data, debias }) {
  // 🔥 SAFE EXTRACTION
  const accuracy = data?.accuracy;
  const f1 = data?.f1;
  const biasGap = data?.bias_gap;
  const fairnessMetrics = data?.fairness_metrics || {};

  const fairnessCount = Object.keys(fairnessMetrics).length;

  // 🔥 FORMATTERS
  const formatPercent = (val) =>
    typeof val === "number" ? `${(val * 100).toFixed(1)}%` : "N/A";

  return (
    <div className="result-card wide">
      <h3>Model + Fairness Summary</h3>

      <div className="summary-grid">
        <p>
          <strong>Accuracy:</strong> {formatPercent(accuracy)}
        </p>

        <p>
          <strong>F1:</strong> {formatPercent(f1)}
        </p>

        <p>
          <strong>Bias Gap:</strong>{" "}
          {typeof biasGap === "number" ? biasGap.toFixed(2) : "N/A"}
        </p>

        <p>
          <strong>Fairness Metrics:</strong> {fairnessCount}
        </p>
      </div>

      <h4>Debiasing Impact</h4>

      <div className="summary-grid">
        <p>
          <strong>Before Fairness:</strong>{" "}
          {debias?.before || "No significant change detected"}
        </p>

        <p>
          <strong>After Fairness:</strong>{" "}
          {debias?.after || "No significant change detected"}
        </p>

        <p>
          <strong>Improvement:</strong>{" "}
          {debias?.improvement || "No significant change detected"}
        </p>
      </div>
    </div>
  );
}

export default FairnessPanel;