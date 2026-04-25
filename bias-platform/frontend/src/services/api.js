import axios from "axios";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export async function uploadFile(file) {
  const formData = new FormData();
  formData.append("file", file);
  const response = await axios.post(`${API_BASE}/upload`, formData);
  return response.data;
}

export async function initContract(targetColumn) {
  const response = await axios.post(`${API_BASE}/init_contract`, {
    target_column: targetColumn,
  });
  return response.data;
}

export async function selectBias(biasColumns) {
  const response = await axios.post(`${API_BASE}/select_bias`, {
    bias_columns: biasColumns,
  });
  return response.data;
}

export async function runPipeline() {
  const response = await axios.post(`${API_BASE}/run_pipeline`, {});
  return response.data;
}

export async function getResults() {
  const response = await axios.get(`${API_BASE}/results`);
  return response.data;
}

export async function setContext(data) {
  const response = await axios.post(`${API_BASE}/context`, data);
  return response.data;
}

// Deprecated: prefer context + runPipeline + getResults flow.
export async function applyContext(data) {
  const response = await axios.post(`${API_BASE}/context/apply-context`, data);
  return response.data;
}

// Deprecated: prefer context + runPipeline + getResults flow.
export async function getFinalDecision(data) {
  const response = await axios.post(`${API_BASE}/decision/final`, data);
  return response.data;
}

export async function explainDecision(data) {
  const response = await axios.post(`${API_BASE}/decision/explain-final`, data);
  return response.data;
}
