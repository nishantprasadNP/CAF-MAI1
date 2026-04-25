function FairnessPanel({ summary, debias }) {
  return (
    <div className="result-card wide">
      <h3>Model + Fairness Summary</h3>
      <div className="summary-grid">
        <p>
          <strong>Accuracy:</strong> {summary.accuracy}
        </p>
        <p>
          <strong>F1:</strong> {summary.f1}
        </p>
        <p>
          <strong>Bias Gap:</strong> {summary.biasGap}
        </p>
        <p>
          <strong>Fairness Metrics:</strong> {summary.fairnessMetricsCount}
        </p>
      </div>

      <h4>Debiasing Impact</h4>
      <div className="summary-grid">
        <p>
          <strong>Before Fairness:</strong> {debias.before}
        </p>
        <p>
          <strong>After Fairness:</strong> {debias.after}
        </p>
        <p>
          <strong>Improvement:</strong> {debias.improvement}
        </p>
      </div>
    </div>
  );
}

export default FairnessPanel;
