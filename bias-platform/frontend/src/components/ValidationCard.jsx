function ValidationCard({ validation }) {
  return (
    <div className="result-card">
      <h3>Validation (Module 9)</h3>
      <p>
        <strong>Action:</strong> {validation.action}
      </p>
      <p className={validation.status.toLowerCase().includes("not") ? "risk-high" : "risk-safe"}>
        <strong>Status:</strong> {validation.status}
      </p>
      <p>
        <strong>Alternative:</strong> {validation.alternative}
      </p>
      <p>
        <strong>Reason:</strong> {validation.reason}
      </p>
      <p>
        <strong>Required vs Available:</strong> {validation.requiredResources} vs {validation.availableResources}
      </p>
    </div>
  );
}

export default ValidationCard;
