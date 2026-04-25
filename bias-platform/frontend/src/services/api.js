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

// ---------------- RESULTS (🔥 MOST IMPORTANT FIX) ---------------- //

export async function getResults() {
  const res = await api.get("/results");
  const data = res.data || {};

  // 🔥 NORMALIZATION LAYER (CRITICAL)
  return {
    // -------- DECISION -------- //
    decision: {
      decision: data?.decision?.decision || "UNKNOWN",
      confidence: data?.decision?.confidence || 0,
      bias_flag: data?.decision?.bias_flag || "unknown",
      context_influence: data?.decision?.context_influence || "unknown",
      explanation: data?.decision?.explanation || "",
      top_features: data?.decision?.top_features || [],
    },

    // -------- FAIRNESS -------- //
    fairness: {
      accuracy: data?.fairness?.accuracy ?? null,
      f1: data?.fairness?.f1 ?? null,
      bias_gap: data?.fairness?.bias_gap ?? 0,
      fairness_metrics:
        data?.fairness?.fairness_metrics ||
        data?.fairness?.metrics ||
        {},
    },

    // -------- CONTEXT -------- //
    context: {
      values: data?.context?.values || {},
      base_probability: data?.context?.base_probability || [],
      final_probability: data?.context?.final_probability || [],
      confidence: data?.context?.confidence || "unknown",
      reason: data?.context?.reason || "",
    },

    // -------- VALIDATION -------- //
    validation: {
      status: data?.validation?.status || "unknown",
      action: data?.validation?.action || "none",
      reason: data?.validation?.reason || "",
      alternative: data?.validation?.alternative || "",
      required_resources:
        data?.validation?.required_resources ?? null,
      available_resources:
        data?.validation?.available_resources ?? null,
    },

    // -------- COMPLIANCE -------- //
    compliance: {
      status: data?.compliance?.status || "unknown",
      pii_removed: data?.compliance?.pii_removed ?? false,
      violations: data?.compliance?.violations || [],
      role: data?.compliance?.role || "",
    },

    // -------- MONITORING -------- //
    monitoring: {
      data_drift: data?.monitoring?.data_drift ?? 0,
      bias_drift: data?.monitoring?.bias_drift ?? 0,
      trend: data?.monitoring?.trend || "stable",
      alerts: data?.monitoring?.alerts || [],
    },
  };
}

// ---------------- CONTEXT ---------------- //

export async function setContext(data) {
  const res = await api.post("/context", data);
  return res.data;
}

// Deprecated endpoints (kept for compatibility)

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