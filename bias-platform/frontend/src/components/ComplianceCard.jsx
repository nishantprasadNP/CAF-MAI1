function ComplianceCard({ compliance }) {
  return (
    <div className="result-card">
      <h3>Compliance (Module 10)</h3>
      <p>
        <strong>Role:</strong> {compliance.role}
      </p>
      <p className={compliance.status.toLowerCase().includes("allow") ? "risk-safe" : "risk-high"}>
        <strong>Status:</strong> {compliance.status}
      </p>
      <p className={compliance.piiRemoved ? "risk-safe" : "risk-high"}>
        <strong>PII Removed:</strong> {compliance.piiRemoved ? "Yes" : "No"}
      </p>
      <p>
        <strong>Policy Violations:</strong> {compliance.policyViolations}
      </p>
    </div>
  );
}

export default ComplianceCard;
