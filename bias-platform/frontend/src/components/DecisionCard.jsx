function riskClass(value) {
  const normalized = String(value || "").toLowerCase();
  if (normalized.includes("high")) return "risk-high";
  if (normalized.includes("moderate")) return "risk-moderate";
  return "risk-safe";
}

function DecisionCard({ decision }) {
  if (!decision) return null;

  const confidence =
    typeof decision?.confidence === "number"
      ? (decision.confidence * 100).toFixed(1) + "%"
      : "N/A";

  const biasRisk = decision?.bias_flag || "unknown";
  const contextInfluence = decision?.context_influence || "unknown";

  const explanation =
    decision?.explanation || "No explanation available";

  const aiExplanation =
    decision?.ai_explanation || null;

  const features = Array.isArray(decision?.top_features)
    ? decision.top_features
    : [];

  return (
    <div className="result-card decision-card">
      <h3>Decision</h3>

      <p>
        <strong>Decision:</strong> {decision?.decision || "N/A"}
      </p>

      <p>
        <strong>Confidence:</strong> {confidence}
      </p>

      <p className={riskClass(biasRisk)}>
        <strong>Bias Risk:</strong> {biasRisk}
      </p>

      <p className={riskClass(contextInfluence)}>
        <strong>Context Influence:</strong> {contextInfluence}
      </p>

      <details className="decision-why">
        <summary>Why this decision?</summary>

        {/* Primary explanation */}
        <p>{explanation}</p>

        {/* 🔥 AI Explanation (Gemini) */}
        {aiExplanation && (
          <p style={{ marginTop: "8px", color: "#4b5563" }}>
            {aiExplanation}
          </p>
        )}

        {/* Top features */}
        {features.length > 0 && (
          <ul className="feature-list">
            {features.map((item, i) => (
              <li key={i}>
                <span>{item.feature || item.name || "unknown"}</span>
                <strong>
                  {typeof item.impact === "number"
                    ? item.impact
                    : item.score ?? "N/A"}
                </strong>
              </li>
            ))}
          </ul>
        )}
      </details>
    </div>
  );
}

export default DecisionCard;