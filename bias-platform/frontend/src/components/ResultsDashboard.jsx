import ComplianceCard from "./ComplianceCard";
import DecisionCard from "./DecisionCard";
import ExplainabilityPanel from "./ExplainabilityPanel";
import FairnessPanel from "./FairnessPanel";
import MonitoringCard from "./MonitoringCard";
import ValidationCard from "./ValidationCard";

function ResultsDashboard({ results, contextApplied }) {
  if (!results) return null;

  return (
    <section id="results">
      <h2>Step 6: Multi-Layer Results Dashboard</h2>
      <p className="muted">
        Decision intelligence view across fairness, context, validation, compliance, and monitoring layers.
      </p>

      <div className="results-grid">

        {/* ✅ FAIRNESS */}
        <FairnessPanel
          data={results.fairness}
          debias={results.monitoring?.debiasing_effect || {}}
        />

        {/* ✅ CONTEXT */}
        <div className="result-card">
          <h3>Context Impact</h3>

          <p>
            <strong>Base Probability:</strong>{" "}
            {results.context?.base_probability?.[1]?.toFixed?.(2) ?? "N/A"}
          </p>

          <p>
            <strong>Context-adjusted Probability:</strong>{" "}
            {results.context?.final_probability?.[1]?.toFixed?.(2) ?? "N/A"}
          </p>

          <p>
            <strong>Impact:</strong>{" "}
            {typeof results.context?.impact === "number"
              ? results.context.impact.toFixed(2)
              : "N/A"}
          </p>

          <p>
            <strong>Bias Amplification (CBAS):</strong>{" "}
            {typeof results.context?.cbas === "number"
              ? results.context.cbas.toFixed(2)
              : "N/A"}
          </p>

          <p>
            <strong>Context Confidence:</strong>{" "}
            {results.context?.confidence || "Unknown"}
          </p>

          <p>
            <strong>Reason:</strong>{" "}
            {results.context?.reason || "N/A"}
          </p>

          <p className="muted">
            {contextApplied
              ? "Context-aware inference active"
              : "Base run shown"}
          </p>
        </div>

        {/* ✅ DECISION */}
        <DecisionCard decision={results.decision} />

        {/* ✅ VALIDATION */}
        <ValidationCard validation={results.validation} />

        {/* ✅ COMPLIANCE */}
        <ComplianceCard compliance={results.compliance} />

        {/* ✅ MONITORING */}
        <MonitoringCard monitoring={results.monitoring} />

        {/* ✅ EXPLAINABILITY */}
        <ExplainabilityPanel explainability={results.decision} />

        <div className="result-card wide">
          <h3>AI Explanation (Gemini)</h3>
          <p>{results.context?.reason || "Explanation unavailable"}</p>

          <h4>Decision Explanation</h4>
          <p>{results.decision?.decisionExplanation || "Explanation unavailable"}</p>

          <h4>Feature Insights</h4>
          <p>{results.decision?.featureExplanation || "Explanation unavailable"}</p>

          <h4>Compliance Insight</h4>
          <p>{results.compliance?.aiComplianceNote || "Explanation unavailable"}</p>
        </div>
      </div>
    </section>
  );
}

export default ResultsDashboard;