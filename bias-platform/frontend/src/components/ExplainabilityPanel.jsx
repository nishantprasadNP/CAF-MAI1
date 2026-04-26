function formatFeature(name) {
  if (!name) return "";
  return name
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function ExplainabilityPanel({ explainability }) {
  const features = explainability?.top_features || [];

  return (
    <div className="result-card wide">
      <h3>Explainability</h3>

      {}

      <p>
        <strong>Bias Contribution:</strong>{" "}
        {explainability?.biasContribution ?? "N/A"}
      </p>

      <h4>Top Features</h4>

      <ul className="feature-list">
        {features.length ? (
          features.map((item, i) => (
            <li key={i}>
              <span>{formatFeature(item.feature)}</span>
              <strong>
                {typeof item.impact === "number"
                  ? item.impact.toFixed(3)
                  : item.score ?? "N/A"}
              </strong>
            </li>
          ))
        ) : (
          <li>No feature data</li>
        )}
      </ul>
    </div>
  );
}

export default ExplainabilityPanel;