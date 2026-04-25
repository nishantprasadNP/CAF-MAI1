function classifyDrift(value) {
  if (value >= 0.2) return "risk-high";
  if (value >= 0.1) return "risk-moderate";
  return "risk-safe";
}

function MonitoringCard({ monitoring }) {
  const dataDrift = monitoring?.data_drift ?? 0;
  const biasDrift = monitoring?.bias_drift ?? 0;

  return (
    <div className="result-card">
      <h3>Monitoring (Module 11)</h3>

      <p className={classifyDrift(dataDrift)}>
        <strong>Data Drift:</strong> {dataDrift.toFixed(2)}
      </p>

      <p className={classifyDrift(biasDrift)}>
        <strong>Bias Drift:</strong> {biasDrift.toFixed(2)}
      </p>

      <p>
        <strong>Trend:</strong> {monitoring?.trend || "stable"}
      </p>

      <p>
        <strong>Alerts:</strong>{" "}
        {monitoring?.alerts?.length
          ? monitoring.alerts.join(", ")
          : "None"}
      </p>
    </div>
  );
}

export default MonitoringCard;