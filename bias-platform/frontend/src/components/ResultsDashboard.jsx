import { useState } from "react";
import DecisionCard from "./DecisionCard";
import ExplainabilityPanel from "./ExplainabilityPanel";
import FairnessPanel from "./FairnessPanel";
import MonitoringCard from "./MonitoringCard";
import ValidationCard from "./ValidationCard";

function AiAccordion({ title, content, icon }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="ai-accordion">
      <button className="ai-accordion-btn" onClick={() => setOpen((o) => !o)} aria-expanded={open}>
        <span className="ai-accordion-label">
          {icon && <span className="ai-accordion-icon">{icon}</span>}
          {title}
        </span>
        <svg className={`chevron ${open ? "open" : ""}`} width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      <div className={`ai-accordion-body ${open ? "open" : ""}`}>
        <div className="ai-accordion-inner">
          <p style={{ lineHeight: 1.7, margin: 0 }}>{content || "Explanation unavailable"}</p>
        </div>
      </div>
    </div>
  );
}

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
          <h3>AI Explanation</h3>
          <AiAccordion
            title="Decision Explanation"
            content={results.decision?.ai_explanation}
            icon={
              <svg width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            }
          />
          <AiAccordion
            title="Feature Insights"
            content={results.decision?.explanation}
            icon={
              <svg width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3v11.25A2.25 2.25 0 006 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0118 16.5h-2.25m-7.5 0h7.5m-7.5 0l-1 3m8.5-3l1 3m0 0l.5 1.5m-.5-1.5h-9.5m0 0l-.5 1.5M9 11.25v1.5M12 9v3.75m3-6v6" />
              </svg>
            }
          />
          <AiAccordion
            title="Monitoring Insight"
            content={results.monitoring?.driftExplanation}
            icon={
              <svg width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 18L9 11.25l4.306 4.307a11.95 11.95 0 015.814-5.519l2.74-1.22m0 0l-5.94-2.28m5.94 2.28l-2.28 5.941" />
              </svg>
            }
          />
        </div>

      </div>
    </section>
  );
}

export default ResultsDashboard;