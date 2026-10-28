import axios from "axios";

// Same-origin by default: the dev server proxies /api to the backend.
const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api";

// Large CSVs (hundreds of MB) take a while to upload and parse, and the
// pipeline trains models and may wait on Gemini.
const DEFAULT_TIMEOUT_MS = 30_000;
const DATA_TIMEOUT_MS = 300_000;
const PIPELINE_TIMEOUT_MS = 900_000;

// One backend session per browser tab, so parallel users/tabs don't collide.
function getSessionId() {
  const KEY = "bias-platform-session";
  try {
    const existing = sessionStorage.getItem(KEY);
    if (existing) return existing;
  } catch {
    // storage unavailable — fall through to an in-memory id
  }
  const id =
    globalThis.crypto?.randomUUID?.() ||
    `${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`;
  try {
    sessionStorage.setItem(KEY, id);
  } catch {
    // ignore
  }
  return id;
}

const api = axios.create({
  baseURL: API_BASE,
  headers: { "X-Session-ID": getSessionId() },
  timeout: DEFAULT_TIMEOUT_MS,
});

// ---------------- FILE UPLOAD ---------------- //

export async function getLimits() {
  try {
    const res = await api.get("/limits");
    return res.data;
  } catch {
    return { max_rows: 100_000 };
  }
}

export async function uploadFile(blob, filename, onUploadPercent) {
  const formData = new FormData();
  formData.append("file", blob, filename);

  const res = await api.post("/upload", formData, {
    timeout: DATA_TIMEOUT_MS,
    onUploadProgress: (e) => {
      if (e.total) onUploadPercent?.(Math.round((e.loaded / e.total) * 100));
    },
  });
  return res.data;
}

// ---------------- CONTRACT ---------------- //

export async function initContract(targetColumn) {
  const res = await api.post(
    "/init_contract",
    { target_column: targetColumn },
    { timeout: DATA_TIMEOUT_MS }
  );
  return res.data;
}

// ---------------- BIAS ---------------- //

export async function selectBias(biasColumns) {
  const res = await api.post(
    "/select_bias",
    { bias_columns: biasColumns },
    { timeout: DATA_TIMEOUT_MS }
  );
  return res.data;
}

// ---------------- PIPELINE ---------------- //

export async function runPipeline({ rowIndex = 0, availableResources = 8 } = {}) {
  const res = await api.post(
    "/run_pipeline",
    { row_index: rowIndex, available_resources: availableResources },
    { timeout: PIPELINE_TIMEOUT_MS }
  );
  return normalizeResults(res.data);
}

// ---------------- DECISION (single record) ---------------- //

export async function scoreRecord({ rowIndex, availableResources }) {
  const res = await api.post(
    "/decision",
    { row_index: rowIndex, available_resources: availableResources },
    { timeout: PIPELINE_TIMEOUT_MS }
  );
  return {
    decision: normalizeDecision(res.data?.decision),
    validation: res.data?.validation || {},
  };
}

// ---------------- NORMALIZATION ---------------- //

function normalizeDecision(d = {}) {
  return {
    decision: d?.decision || "UNKNOWN",
    predicted_class: d?.predicted_class ?? null,
    target_column: d?.target_column || "",
    confidence: d?.confidence ?? 0,
    bias_flag: d?.bias_flag || "unknown",
    bias_gap: d?.bias_gap ?? 0,
    row_index: d?.row_index ?? 0,
    n_rows: d?.n_rows ?? 0,
    debiased: Boolean(d?.debiased),
    probabilities: d?.probabilities || [],
    original_probabilities: d?.original_probabilities || [],

    explanation: d?.explanation || "",
    top_features: d?.top_features || [],
    ai_explanation: d?.ai_explanation || "",
    ai_status: d?.ai_status || "",
  };
}

function normalizeResults(data = {}) {
  return {
    decision: normalizeDecision(data?.decision),

    fairness: {
      accuracy: data?.fairness?.accuracy ?? 0,
      f1: data?.fairness?.f1 ?? 0,
      evaluated_rows: data?.fairness?.evaluated_rows ?? 0,
      num_fairness_metrics: data?.fairness?.num_fairness_metrics ?? 0,
      summary: data?.fairness?.summary || {},
      insight: data?.fairness?.insight || {},
      global_confusion_matrix: data?.fairness?.global_confusion_matrix || null,
      outcome_distribution: data?.fairness?.outcome_distribution || null,
      fairness_metrics: data?.fairness?.fairness_metrics || null,
    },

    classLabels: data?.class_labels || { 0: "0", 1: "1" },

    validation: data?.validation || {},

    monitoring: {
      data_drift: data?.monitoring?.data_drift ?? 0,
      bias_drift: data?.monitoring?.bias_drift ?? 0,
      previous_bias: data?.monitoring?.previous_bias ?? null,
      current_bias: data?.monitoring?.current_bias ?? 0,
      trend: data?.monitoring?.trend || "baseline",
      alerts: data?.monitoring?.alerts || [],
      driftExplanation: data?.monitoring?.driftExplanation || "",

      debiasing_effect: data?.module6?.debiasing_effect || {},
    },
  };
}
