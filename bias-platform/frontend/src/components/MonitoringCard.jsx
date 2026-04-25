function classifyDrift(value) {
  if (value >= 0.2) return "risk-high";
  if (value >= 0.1) return "risk-moderate";
  return "risk-safe";
}

function MonitoringCard({ monitoring }) {
  const alertClass = monitoring.alerts === "None" ? "risk-safe" : "risk-moderate";
  return (
    <div className="result-card">
      <h3>Monitoring (Module 11)</h3>
      <p className={classifyDrift(monitoring.dataDrift)}>
        <strong>Data Drift:</strong> {monitoring.dataDrift.toFixed(2)} ({monitoring.dataDriftLabel})
      </p>
      <p className={classifyDrift(monitoring.biasDrift)}>
        <strong>Bias Drift:</strong> {monitoring.biasDrift.toFixed(2)} ({monitoring.biasDriftLabel})
      </p>
      <p>
        <strong>Bias Drift Trend:</strong> {monitoring.previousBiasDrift.toFixed(2)} {"->"}{" "}
        {monitoring.currentBiasDrift.toFixed(2)}
      </p>
      <p className={alertClass}>
        <strong>Alerts:</strong> {monitoring.alerts}
      </p>
    </div>
  );
}

export default MonitoringCard;
