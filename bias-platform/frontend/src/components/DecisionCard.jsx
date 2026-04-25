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
        <strong>Decision:</strong> {decision.finalDecision || "N/A"}
      </p>
      <p>
        <strong>Confidence:</strong> {decision.confidence}
      </p>
      <p className={riskClass(decision.biasRisk)}>
        <strong>Bias Risk:</strong> {decision.biasRisk}
      </p>
      <p className={riskClass(decision.contextInfluence)}>
        <strong>Context Influence:</strong> {decision.contextInfluence}
      </p>
      <details className="decision-why">
        <summary>Why this decision?</summary>
        <p>{decision.explanation}</p>
        {decision.featureImpacts?.length ? (
          <ul className="feature-list">
            {decision.featureImpacts.map((item) => (
              <li key={item.feature}>
                <span>{item.feature}</span>
                <strong>{item.impact}</strong>
              </li>
            ))}
          </ul>
        ) : null}
        {decision.contributions ? (
          <p className="muted">
            Feature: {decision.contributions.feature ?? "N/A"} | Context: {decision.contributions.context ?? "N/A"} |
            Bias: {decision.contributions.bias ?? "N/A"}
          </p>
        ) : null}
      </details>
    </div>
  );
}

export default DecisionCard;
