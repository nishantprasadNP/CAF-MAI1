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
        <strong>Data Drift (train vs. evaluation, PSI):</strong> <span className={classifyDrift(dataDrift)}>{dataDrift.toFixed(2)}</span>
      </p>

      <p>
        <strong>Bias Drift:</strong> <span className={classifyDrift(biasDrift)}>{biasDrift.toFixed(2)}</span>
      </p>

      <p>
        <strong>Bias Trend:</strong> {monitoring?.trend || "baseline"}
        {typeof monitoring?.previous_bias === "number" &&
          ` (${monitoring.previous_bias.toFixed(2)} → ${Number(monitoring?.current_bias ?? 0).toFixed(2)})`}
      </p>

      <strong>Alerts:</strong>
      {monitoring?.alerts?.length ? (
        <ul className="alert-list">
          {monitoring.alerts.map((alert) => (
            <li key={alert}>{alert}</li>
          ))}
        </ul>
      ) : (
        <p>None</p>
      )}
    </div>
  );
}

export default MonitoringCard;