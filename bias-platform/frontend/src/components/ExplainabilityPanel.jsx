function ExplainabilityPanel({ explainability }) {
  return (
    <div className="result-card wide">
      <h3>Explainability</h3>
      <p>
        <strong>Context Contribution:</strong> {explainability.contextContribution}
      </p>
      <p>
        <strong>Bias Contribution:</strong> {explainability.biasContribution}
      </p>
      <h4>Top Features</h4>
      <ul className="feature-list">
        {explainability.topFeatures.map((item) => (
          <li key={item.name}>
            <span>{item.name}</span>
            <strong>{item.score}%</strong>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default ExplainabilityPanel;
