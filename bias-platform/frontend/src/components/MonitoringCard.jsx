function classifyDrift(value) {
  if (value >= 0.2) return "badge error";
  if (value >= 0.1) return "badge warning";
  return "badge good";
}

function MonitoringCard({ monitoring }) {
  const dataDrift = Number(monitoring?.data_drift ?? 0);
  const biasDrift = Number(monitoring?.bias_drift ?? 0);

  return (
    <div className="result-card">
      <h3>Monitoring</h3>

      <p>
        <strong>Data Drift:</strong> <span className={classifyDrift(dataDrift)}>{dataDrift.toFixed(2)}</span>
      </p>

      <p>
        <strong>Bias Drift:</strong> <span className={classifyDrift(biasDrift)}>{biasDrift.toFixed(2)}</span>
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