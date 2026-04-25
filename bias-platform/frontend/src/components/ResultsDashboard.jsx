import ComplianceCard from "./ComplianceCard";
import DecisionCard from "./DecisionCard";
import ExplainabilityPanel from "./ExplainabilityPanel";
import FairnessPanel from "./FairnessPanel";
import MonitoringCard from "./MonitoringCard";
import ValidationCard from "./ValidationCard";

function toPercent(value) {
  if (typeof value !== "number" || Number.isNaN(value)) return "N/A";
  return `${(value * 100).toFixed(1)}%`;
}

function toFixed(value, digits = 2) {
  if (typeof value !== "number" || Number.isNaN(value)) return "N/A";
  return value.toFixed(digits);
}

function firstNumber(value, fallback = 0) {
  if (typeof value === "number" && !Number.isNaN(value)) return value;
  if (Array.isArray(value)) {
    const numeric = value.find((item) => typeof item === "number" && !Number.isNaN(item));
    return typeof numeric === "number" ? numeric : fallback;
  }
  return fallback;
}

function extractProbability(value) {
  if (typeof value === "number" && !Number.isNaN(value)) return value;
  if (!Array.isArray(value) || value.length === 0) return null;
  if (value.every((item) => typeof item === "number")) {
    if (value.length >= 2) return value[1];
    return value[0];
  }
  for (const item of value) {
    const nested = extractProbability(item);
    if (typeof nested === "number") return nested;
  }
  return null;
}

function clampDelta(value, min = -0.2, max = 0.2) {
  if (typeof value !== "number" || Number.isNaN(value)) return null;
  return Math.max(min, Math.min(max, value));
}

function normalizeDecisionLabel(value) {
  if (value === 1 || value === "1") return "APPROVE";
  if (value === 0 || value === "0") return "REJECT";
  const normalized = String(value ?? "").trim().toLowerCase();
  if (normalized === "approve" || normalized === "approved") return "APPROVE";
  if (normalized === "reject" || normalized === "rejected") return "REJECT";
  return value || "N/A";
}

function contributionLabel(percent) {
  if (percent >= 60) return "Strong";
  if (percent >= 30) return "Moderate";
  return "Weak";
}

function summarizeResults(results) {
  const modelMetrics = results?.module4?.model?.metrics || {};
  const fairnessMetrics = results?.module5?.fairness_metrics || {};
  const biasGaps = results?.module5?.bias_gaps || {};
  const fairnessValues = Object.values(fairnessMetrics).flatMap((entry) =>
    Object.values(entry || {}).filter((metric) => typeof metric === "number"),
  );
  const beforeFairness = fairnessValues.length
    ? fairnessValues.reduce((sum, value) => sum + value, 0) / fairnessValues.length
    : null;
  const afterFairness = firstNumber(results?.module6?.debiasing_effect?.fairness_improvement, null);

  const baseProbability = extractProbability(results?.module4?.inference?.batch?.probabilities?.[0]);
  const debiasedProbability = extractProbability(
    results?.module6?.reweighted_results?.probabilities?.[0] ?? results?.module6?.resampled_results?.probabilities?.[0],
  );
  const adjustedProbability = extractProbability(results?.module7?.adjusted_probabilities?.[0]);
  const rawImpact =
    typeof baseProbability === "number" && typeof adjustedProbability === "number"
      ? adjustedProbability - baseProbability
      : null;
  const impact = clampDelta(rawImpact);

  const confidenceRaw = results?.module8?.confidence ?? results?.decision?.confidence;
  const confidence = typeof confidenceRaw === "number" ? toPercent(confidenceRaw) : confidenceRaw || "N/A";
  const explanationStructured =
    results?.decision?.explanation_structured ?? results?.module8?.explanation_structured ?? {};

  const biasScore = firstNumber(results?.module7?.bias_score, null);
  const riskLevel = biasScore == null ? "Unknown" : biasScore >= 0.7 ? "High" : biasScore >= 0.4 ? "Moderate" : "Low";
  const contextInfluence =
    impact == null ? "Unknown" : Math.abs(impact) >= 0.08 ? "High" : Math.abs(impact) >= 0.03 ? "Moderate" : "Low";

  const module8Importance = Object.entries(results?.module8?.feature_importance || {}).map(([name, score]) => ({
    name,
    score: Number(score),
  }));
  const module4Importance = Object.entries(results?.module4?.model?.feature_importance || {}).map(
    ([name, score]) => ({
      name,
      score: Number(score),
    }),
  );
  const coefficients = Object.entries(results?.module4?.model?.coefficients || {}).map(([name, score]) => ({
    name,
    score: Number(score),
  }));
  const fallbackFeatures = [
    { name: "context_delta", score: Math.abs(impact || 0) },
    { name: "bias_score", score: Math.abs(biasScore || 0) },
    { name: "resource_level", score: 0.2 },
  ];
  const topFeaturesSource = module8Importance.length
    ? module8Importance
    : module4Importance.length
      ? module4Importance
      : coefficients.length
        ? coefficients
        : fallbackFeatures;
  const topFeatures = topFeaturesSource
    .sort((a, b) => Math.abs(b.score) - Math.abs(a.score))
    .slice(0, 5)
    .map((item) => ({
      name: item.name,
      score: Math.min(100, Math.max(0, Math.round(Math.abs(Number(item.score) || 0) * 100))),
    }));

  const validationModule = results?.module9 || {};
  const complianceModule = results?.module10 || {};
  const monitoringModule = results?.module11 || {};

  const dataDrift = firstNumber(monitoringModule.data_drift ?? monitoringModule.dataDrift, 0);
  const biasDrift = firstNumber(monitoringModule.bias_drift ?? monitoringModule.biasDrift, 0);

  return {
    modelFairness: {
      accuracy: toPercent(modelMetrics.accuracy),
      f1: toPercent(modelMetrics.f1_score ?? modelMetrics.f1),
      biasGap: toFixed(results?.module5?.summary?.bias_gap ?? firstNumber(Object.values(biasGaps)[0], 0)),
      fairnessMetricsCount: Object.keys(fairnessMetrics).length || 0,
    },
    debias: {
      before: beforeFairness == null ? "No significant change detected" : toFixed(beforeFairness),
      after: afterFairness == null ? "No significant change detected" : toFixed(afterFairness),
      improvement:
        beforeFairness != null && afterFairness != null
          ? `${(((afterFairness - beforeFairness) / Math.max(Math.abs(beforeFairness), 1e-6)) * 100).toFixed(1)}%`
          : "No significant change detected",
    },
    contextImpact: {
      base: baseProbability == null ? "N/A" : toFixed(baseProbability),
      debiased: debiasedProbability == null ? "N/A" : toFixed(debiasedProbability),
      adjusted: adjustedProbability == null ? "N/A" : toFixed(adjustedProbability),
      impact: impact == null ? "N/A" : `${impact > 0 ? "+" : ""}${impact.toFixed(2)}`,
      reason: `resource_level = ${results?.context?.resource_level || "unknown"}`,
    },
    decision: {
      finalDecision: normalizeDecisionLabel(results?.decision?.label ?? results?.module8?.final_decision),
      confidence,
      biasRisk: riskLevel,
      contextInfluence,
      explanation:
        explanationStructured?.summary ||
        results?.module8?.explanation ||
        "Decision derived from model score, fairness constraints, and context.",
      featureImpacts: explanationStructured?.top_features || [],
      contributions: explanationStructured?.contributions || {},
    },
    explainability: {
      topFeatures,
      contextContribution:
        typeof explanationStructured?.contributions?.context === "number"
          ? `${contributionLabel(explanationStructured.contributions.context * 100)} (${(
              explanationStructured.contributions.context * 100
            ).toFixed(0)}%)`
          : impact == null
            ? "Weak (0%)"
            : `${contributionLabel(Math.abs(impact) * 100)} (${(Math.abs(impact) * 100).toFixed(0)}%)`,
      biasContribution:
        typeof explanationStructured?.contributions?.bias === "number"
          ? `${contributionLabel(explanationStructured.contributions.bias * 100)} (${(
              explanationStructured.contributions.bias * 100
            ).toFixed(0)}%)`
          : biasScore == null
            ? "Weak (0%)"
            : `${contributionLabel(biasScore * 100)} (${(biasScore * 100).toFixed(0)}%)`,
    },
    validation: {
      action: validationModule.action || "Allocate Resources",
      status: validationModule.status || "Not Feasible",
      alternative: validationModule.alternative || "Delay Allocation",
      requiredResources: validationModule.required_resources ?? "N/A",
      availableResources: validationModule.available_resources ?? "N/A",
      reason:
        validationModule.reason ||
        (String(validationModule.status || "").toLowerCase().includes("fallback")
          ? "insufficient resources"
          : "insufficient resources"),
    },
    compliance: {
      role: complianceModule.role || "Analyst",
      status: complianceModule.status || "Allowed",
      piiRemoved: Boolean(complianceModule.pii_removed ?? true),
      policyViolations: complianceModule.policy_violations || "None",
    },
    monitoring: {
      dataDrift,
      dataDriftLabel: dataDrift > 0.2 ? "High" : dataDrift > 0.1 ? "Moderate" : "Low",
      biasDrift,
      biasDriftLabel: biasDrift > 0.2 ? "High" : biasDrift > 0.1 ? "Watch" : "Stable",
      previousBiasDrift: firstNumber(monitoringModule.previous_bias_drift, 0),
      currentBiasDrift: firstNumber(monitoringModule.current_bias_drift, biasDrift),
      alerts:
        Array.isArray(monitoringModule.alerts) && monitoringModule.alerts.length
          ? monitoringModule.alerts.join(", ")
          : monitoringModule.alerts || "No anomalies detected",
    },
    contextConfidence: results?.module7?.context_confidence || "Low",
  };
}

function ResultsDashboard({ results, contextApplied }) {
  const summary = summarizeResults(results);

  return (
    <section id="results">
      <h2>Step 6: Multi-Layer Results Dashboard</h2>
      <p className="muted">
        Decision intelligence view across fairness, context, validation, compliance, and monitoring layers.
      </p>

      <div className="results-grid">
        <FairnessPanel summary={summary.modelFairness} debias={summary.debias} />

        <div className="result-card">
          <h3>Context Impact</h3>
          <p>
            <strong>Base Probability:</strong> {summary.contextImpact.base}
          </p>
          <p>
            <strong>Debiased Probability:</strong> {summary.contextImpact.debiased}
          </p>
          <p>
            <strong>Context-adjusted Probability:</strong> {summary.contextImpact.adjusted}
          </p>
          <p className={summary.contextImpact.impact.startsWith("+") ? "risk-safe" : "risk-moderate"}>
            <strong>Impact:</strong> {summary.contextImpact.impact}
          </p>
          <p>
            <strong>Reason:</strong> {summary.contextImpact.reason}
          </p>
          <p>
            <strong>Context Confidence:</strong> {summary.contextConfidence}
          </p>
          <p className="muted">{contextApplied ? "Context-aware inference active" : "Base run shown"}</p>
        </div>

        <DecisionCard decision={summary.decision} />
        <ValidationCard validation={summary.validation} />
        <ComplianceCard compliance={summary.compliance} />
        <MonitoringCard monitoring={summary.monitoring} />
        <ExplainabilityPanel explainability={summary.explainability} />
      </div>
    </section>
  );
}

export default ResultsDashboard;
