function riskClass(value) {
  const normalized = String(value || "").toLowerCase();
  if (normalized.includes("high")) return "risk-high";
  if (normalized.includes("moderate")) return "risk-moderate";
  return "risk-safe";
}

// 🔥 Feature name cleaner
function formatFeature(name) {
  if (!name) return "";

  return name
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase())
    .replace("Pclass", "Passenger Class")
    .replace("Sex", "Gender")
    .replace("Fare", "Ticket Fare")
    .replace("Cabin", "Cabin Info");
}

function DecisionCard({ decision }) {
  if (!decision) return null;

  const confidence =
    typeof decision?.confidence === "number"
      ? (decision.confidence * 100).toFixed(1) + "%"
      : "N/A";

  const biasRisk = decision?.bias_flag || "unknown";

  // ✅ Use AI explanation only (no duplication)
  const explanation =
    decision?.ai_explanation ||
    decision?.explanation ||
    "No explanation available";

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

      {/* ❌ REMOVED context_influence */}

      <details className="decision-why">
        <summary>Why this decision?</summary>

        <p style={{ lineHeight: "1.6" }}>{explanation}</p>

        {features.length > 0 && (
          <ul className="feature-list">
            {features.map((item, i) => (
              <li key={i}>
                <span>{formatFeature(item.feature)}</span>
                <strong>
                  {typeof item.impact === "number"
                    ? item.impact.toFixed(3)
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