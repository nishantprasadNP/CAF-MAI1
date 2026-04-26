import axios from "axios";

const API_BASE =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    "Content-Type": "application/json",
  },
});

// ---------------- FILE UPLOAD ---------------- //

export async function uploadFile(file) {
  const formData = new FormData();
  formData.append("file", file);

  const res = await api.post("/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });

  return res.data;
}

// ---------------- CONTRACT ---------------- //

export async function initContract(targetColumn) {
  const res = await api.post("/init_contract", {
    target_column: targetColumn,
  });
  return res.data;
}

// ---------------- BIAS ---------------- //

export async function selectBias(biasColumns) {
  const res = await api.post("/select_bias", {
    bias_columns: biasColumns,
  });
  return res.data;
}

// ---------------- PIPELINE ---------------- //

export async function runPipeline() {
  const res = await api.post("/run_pipeline", {});
  return res.data;
}

// ---------------- RESULTS (🔥 FIXED) ---------------- //

export async function getResults() {
  const res = await api.get("/results");
  const data = res.data || {};

  return {
    decision: {
      decision: data?.decision?.decision || "UNKNOWN",
      confidence: data?.decision?.confidence || 0,
      bias_flag: data?.decision?.bias_flag || "unknown",
      context_influence: data?.decision?.context_influence || "unknown",
      explanation: data?.decision?.explanation || "",
      top_features: data?.decision?.top_features || [],
      contextContribution: data?.decision?.contextContribution ?? 0,
      biasContribution: data?.decision?.biasContribution ?? 0,
      ai_explanation: data?.decision?.ai_explanation || "",
    },

    fairness: {
      accuracy: data?.fairness?.accuracy ?? 0,
      f1: data?.fairness?.f1 ?? 0,
      num_fairness_metrics:
        data?.fairness?.num_fairness_metrics ?? 0,
      summary: data?.fairness?.summary || {},
    },

    validation: data?.validation || {},

    compliance: data?.compliance || {},

    monitoring: {
      data_drift: data?.monitoring?.data_drift ?? 0,
      bias_drift: data?.monitoring?.bias_drift ?? 0,
      previous_bias: data?.monitoring?.previous_bias ?? 0,
      current_bias: data?.monitoring?.current_bias ?? 0,
      trend: data?.monitoring?.trend || "stable",
      alerts: data?.monitoring?.alerts || [],
      driftExplanation: data?.monitoring?.driftExplanation || "",

      // 🔥 IMPORTANT
      debiasing_effect:
        data?.module6?.debiasing_effect ||
        data?.monitoring?.debiasing_effect ||
        {},
    },
  };
}

// ---------------- CONTEXT ---------------- //

export async function setContext(data) {
  const res = await api.post("/context", data);
  return res.data;
}

// Deprecated endpoints

export async function applyContext(data) {
  const res = await api.post("/context/apply-context", data);
  return res.data;
}

export async function getFinalDecision(data) {
  const res = await api.post("/decision/final", data);
  return res.data;
}

export async function explainDecision(data) {
  const res = await api.post("/decision/explain-final", data);
  return res.data;
}