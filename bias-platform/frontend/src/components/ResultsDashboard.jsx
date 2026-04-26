import DecisionCard from "./DecisionCard";
import ExplainabilityPanel from "./ExplainabilityPanel";
import FairnessPanel from "./FairnessPanel";
import MonitoringCard from "./MonitoringCard";
import ValidationCard from "./ValidationCard";

function ResultsDashboard({ results }) {
  if (!results) return null;

  return (
    <section id="results">
      <h2>Step 6: Multi-Layer Results Dashboard</h2>
      <p className="muted">
        Decision intelligence view across fairness, validation, and monitoring layers.
      </p>

      <div className="results-grid">

        {/* ✅ FAIRNESS */}
        <FairnessPanel
          data={results.fairness}
          debias={results.monitoring?.debiasing_effect || {}}
        />

        {/* ✅ DECISION */}
        <DecisionCard decision={results.decision} />

        {/* ✅ VALIDATION */}
        <ValidationCard validation={results.validation} />

        {/* ✅ MONITORING */}
        <MonitoringCard monitoring={results.monitoring} />

        {/* ✅ EXPLAINABILITY */}
        <ExplainabilityPanel explainability={results.decision} />

        {/* ✅ AI EXPLANATION */}
        <div className="result-card wide">
          <h3>AI Explanation (Gemini)</h3>

          <h4>Decision Explanation</h4>
          <p>{results.decision?.ai_explanation || "Explanation unavailable"}</p>

          <h4>Feature Insights</h4>
          <p>{results.decision?.explanation || "Explanation unavailable"}</p>

          <h4>Monitoring Insight</h4>
          <p>{results.monitoring?.driftExplanation || "Explanation unavailable"}</p>
        </div>

      </div>
    </section>
  );
}

export default ResultsDashboard;