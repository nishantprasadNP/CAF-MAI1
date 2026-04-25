function ExplainabilityPanel({ explainability }) {
  const features = explainability?.top_features || [];

  return (
    <div className="result-card wide">
      <h3>Explainability</h3>

      <p>
        <strong>Context Contribution:</strong>{" "}
        {explainability?.contextContribution ?? "N/A"}
      </p>

      <p>
        <strong>Bias Contribution:</strong>{" "}
        {explainability?.biasContribution ?? "N/A"}
      </p>

      <h4>Top Features</h4>

      <ul className="feature-list">
        {features.length ? (
          features.map((item, i) => (
            <li key={i}>
              <span>{item.feature || item.name}</span>
              <strong>{item.impact || item.score}</strong>
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