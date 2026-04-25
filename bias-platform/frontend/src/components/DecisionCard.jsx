function riskClass(value) {
  const normalized = String(value || "").toLowerCase();
  if (normalized.includes("high")) return "risk-high";
  if (normalized.includes("moderate")) return "risk-moderate";
  return "risk-safe";
}

function DecisionCard({ decision }) {
  return (
    <div className="result-card decision-card">
      <h3>Decision</h3>

      <p>
        <strong>Decision:</strong> {decision?.decision || "N/A"}
      </p>

      <p>
        <strong>Confidence:</strong>{" "}
        {typeof decision?.confidence === "number"
          ? (decision.confidence * 100).toFixed(1) + "%"
          : "N/A"}
      </p>

      <p className={riskClass(decision?.bias_flag)}>
        <strong>Bias Risk:</strong> {decision?.bias_flag || "Unknown"}
      </p>

      <p className={riskClass(decision?.context_influence)}>
        <strong>Context Influence:</strong>{" "}
        {decision?.context_influence || "Unknown"}
      </p>

      <details className="decision-why">
        <summary>Why this decision?</summary>
        <p>{decision?.explanation || "No explanation available"}</p>

        {decision?.top_features?.length ? (
          <ul className="feature-list">
            {decision.top_features.map((item, i) => (
              <li key={i}>
                <span>{item.feature || item.name}</span>
                <strong>{item.impact || item.score}</strong>
              </li>
            ))}
          </ul>
        ) : null}
      </details>
    </div>
  );
}

export default DecisionCard;