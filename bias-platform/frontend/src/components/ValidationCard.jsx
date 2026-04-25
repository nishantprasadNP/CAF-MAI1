function ValidationCard({ validation }) {
  // 🔥 SAFE EXTRACTION
  const action = validation?.action || "N/A";
  const status = validation?.status || "unknown";
  const alternative = validation?.alternative || "N/A";
  const reason = validation?.reason || "N/A";

  const required = validation?.required_resources;
  const available = validation?.available_resources;

  // 🔥 FORMAT
  const formatValue = (val) =>
    typeof val === "number" ? val : "N/A";

  return (
    <div className="result-card">
      <h3>Validation (Module 9)</h3>

      <p>
        <strong>Action:</strong> {action}
      </p>

      <p
        className={
          status.toLowerCase().includes("not")
            ? "risk-high"
            : "risk-safe"
        }
      >
        <strong>Status:</strong> {status}
      </p>

      <p>
        <strong>Alternative:</strong> {alternative}
      </p>

      <p>
        <strong>Reason:</strong> {reason}
      </p>

      <p>
        <strong>Required vs Available:</strong>{" "}
        {formatValue(required)} vs {formatValue(available)}
      </p>
    </div>
  );
}

export default ValidationCard;