function ComplianceCard({ compliance }) {
  return (
    <div className="result-card">
      <h3>Compliance (Module 10)</h3>

      <p>
        <strong>Role:</strong> {compliance?.role || "N/A"}
      </p>

      <p
        className={
          String(compliance?.status || "")
            .toLowerCase()
            .includes("allow")
            ? "risk-safe"
            : "risk-high"
        }
      >
        <strong>Status:</strong> {compliance?.status || "unknown"}
      </p>

      <p
        className={
          compliance?.pii_removed ? "risk-safe" : "risk-high"
        }
      >
        <strong>PII Removed:</strong>{" "}
        {compliance?.pii_removed ? "Yes" : "No"}
      </p>

      <p>
        <strong>Policy Violations:</strong>{" "}
        {Array.isArray(compliance?.violations) &&
        compliance.violations.length
          ? compliance.violations.join(", ")
          : "None"}
      </p>
    </div>
  );
}

export default ComplianceCard;