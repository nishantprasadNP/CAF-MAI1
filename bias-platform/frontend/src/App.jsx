import { useMemo, useState } from "react";
import { getResults, initContract, runPipeline, selectBias, uploadFile } from "./services/api";

const steps = [
  "Upload Dataset",
  "Select Target Column",
  "Select Bias Columns",
  "Run Analysis",
  "Results Dashboard",
];

function App() {
  const [step, setStep] = useState(1);
  const [file, setFile] = useState(null);
  const [uploadData, setUploadData] = useState(null);
  const [contract, setContract] = useState(null);
  const [targetColumn, setTargetColumn] = useState("");
  const [selectedBias, setSelectedBias] = useState([]);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const selectableColumns = useMemo(() => {
    if (!contract?.X?.length) return [];
    return Object.keys(contract.X[0]);
  }, [contract]);

  const resultSnapshot = useMemo(() => {
    if (!results) return null;
    return {
      profile: results.profile,
      registry: results.registry,
      module2: {
        B_hidden: results.module2?.B_hidden,
        cluster_distribution: results.module2?.cluster_distribution,
      },
      module4: results.module4,
      module5: results.module5,
      module6: results.module6,
      dataset_summary: {
        rows: results.profile?.row_count ?? 0,
        columns: results.profile?.column_count ?? 0,
        B_user: results.dataset?.B_user ?? [],
        B_suggested: results.dataset?.B_suggested ?? [],
        B_hidden: results.dataset?.B_hidden ?? [],
      },
    };
  }, [results]);

  const onUpload = async () => {
    if (!file) {
      setError("Please choose a CSV file.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const data = await uploadFile(file);
      setUploadData(data);
      setTargetColumn(data.columns?.[data.columns.length - 1] || "");
      setStep(2);
    } catch (err) {
      setError(err?.response?.data?.detail || "Upload failed.");
    } finally {
      setLoading(false);
    }
  };

  const onInitContract = async () => {
    if (!targetColumn) {
      setError("Select a target column.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const data = await initContract(targetColumn);
      setContract(data);
      setSelectedBias([]);
      setStep(3);
    } catch (err) {
      setError(err?.response?.data?.detail || "Contract initialization failed.");
    } finally {
      setLoading(false);
    }
  };

  const onSelectBias = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await selectBias(selectedBias);
      setContract((prev) => ({ ...prev, ...data }));
      setStep(4);
    } catch (err) {
      setError(err?.response?.data?.detail || "Bias selection failed.");
    } finally {
      setLoading(false);
    }
  };

  const onRunPipeline = async () => {
    setLoading(true);
    setError("");
    try {
      await runPipeline();
      const data = await getResults();
      setResults(data);
      setStep(5);
    } catch (err) {
      setError(err?.response?.data?.detail || "Pipeline run failed.");
    } finally {
      setLoading(false);
    }
  };

  const renderList = (title, values) => (
    <div className="result-card">
      <h3>{title}</h3>
      {values?.length ? (
        <ul>
          {values.map((value) => (
            <li key={value}>{value}</li>
          ))}
        </ul>
      ) : (
        <p className="muted">No values available.</p>
      )}
    </div>
  );

  return (
    <div className="container">
      <h1>Bias Platform Pipeline</h1>
      <div className="stepper">
        {steps.map((label, idx) => (
          <div key={label} className={`step ${step >= idx + 1 ? "active" : ""}`}>
            <span>{idx + 1}</span>
            <p>{label}</p>
          </div>
        ))}
      </div>

      {step === 1 && (
        <section>
          <h2>Step 1: Upload Dataset</h2>
          <input type="file" accept=".csv" onChange={(e) => setFile(e.target.files?.[0] || null)} />
          <button onClick={onUpload} disabled={loading}>
            Upload
          </button>
        </section>
      )}

      {step === 2 && (
        <section>
          <h2>Step 2: Select Target Column</h2>
          <select value={targetColumn} onChange={(e) => setTargetColumn(e.target.value)}>
            <option value="">Select target column</option>
            {(uploadData?.columns || []).map((column) => (
              <option key={column} value={column}>
                {column}
              </option>
            ))}
          </select>
          <button onClick={onInitContract} disabled={loading}>
            Initialize Contract
          </button>
        </section>
      )}

      {step === 3 && (
        <section>
          <h2>Step 3: Select Bias Columns</h2>
          <select
            multiple
            value={selectedBias}
            onChange={(e) =>
              setSelectedBias(Array.from(e.target.selectedOptions).map((option) => option.value))
            }
          >
            {selectableColumns
              .filter((column) => column !== targetColumn)
              .map((column) => (
                <option key={column} value={column}>
                  {column}
                </option>
              ))}
          </select>
          <button onClick={onSelectBias} disabled={loading}>
            Save Bias Selection
          </button>
        </section>
      )}

      {step === 4 && (
        <section>
          <h2>Step 4: Run Analysis</h2>
          <button onClick={onRunPipeline} disabled={loading}>
            Run Pipeline
          </button>
        </section>
      )}

      {step === 5 && (
        <section>
          <h2>Step 5: Results Dashboard</h2>
          <div className="results-grid">
            <div className="result-card">
              <h3>Dataset Summary</h3>
              <p>
                <strong>Rows:</strong> {results?.profile?.row_count ?? 0}
              </p>
              <p>
                <strong>Columns:</strong> {results?.profile?.column_count ?? 0}
              </p>
              <p>
                <strong>Registry Size:</strong> {results?.registry?.length ?? 0}
              </p>
            </div>

            {renderList("User Selected Bias", results?.dataset?.B_user)}
            {renderList("Suggested Bias", results?.dataset?.B_suggested)}
            {renderList("Hidden Bias", results?.dataset?.B_hidden)}

            <div className="result-card wide">
              <h3>Cluster Distribution</h3>
              <div className="pill-wrap">
                {Object.entries(results?.module2?.cluster_distribution || {}).map(([label, count]) => (
                  <span key={label} className="pill">
                    Cluster {label}: {count}
                  </span>
                ))}
              </div>
            </div>

            <div className="result-card wide">
              <h3>Module 4 Model Metrics</h3>
              <p>
                <strong>Model:</strong> {results?.module4?.model?.name || "N/A"}
              </p>
              <p>
                <strong>Accuracy:</strong> {results?.module4?.model?.metrics?.accuracy ?? "N/A"}
              </p>
              <p>
                <strong>Precision:</strong> {results?.module4?.model?.metrics?.precision ?? "N/A"}
              </p>
              <p>
                <strong>Recall:</strong> {results?.module4?.model?.metrics?.recall ?? "N/A"}
              </p>
              <p>
                <strong>F1:</strong> {results?.module4?.model?.metrics?.f1_score ?? "N/A"}
              </p>
            </div>

            <div className="result-card wide">
              <h3>Module 5 Fairness Layer</h3>
              <h4>Task 5.1 - Subgroup Metric Calculator</h4>
              {Object.entries(results?.module5?.subgroup_metrics || {}).length ? (
                Object.entries(results?.module5?.subgroup_metrics || {}).map(([column, groups]) => (
                  <div key={`subgroup-${column}`}>
                    <p>
                      <strong>{column}</strong>
                    </p>
                    <pre>{JSON.stringify(groups, null, 2)}</pre>
                  </div>
                ))
              ) : (
                <p className="muted">No subgroup metrics available.</p>
              )}

              <h4>Task 5.2 - Bias Gap Calculator</h4>
              {Object.entries(results?.module5?.bias_gaps || {}).length ? (
                <pre>{JSON.stringify(results?.module5?.bias_gaps, null, 2)}</pre>
              ) : (
                <p className="muted">No bias gap values available.</p>
              )}

              <h4>Task 5.3 - Intersectional Bias Analysis</h4>
              {Object.entries(results?.module5?.intersectional || {}).length ? (
                <pre>{JSON.stringify(results?.module5?.intersectional, null, 2)}</pre>
              ) : (
                <p className="muted">No intersectional metrics available.</p>
              )}

              <h4>Task 5.4 - Fairness Metrics Engine</h4>
              {Object.entries(results?.module5?.fairness_metrics || {}).length ? (
                <pre>{JSON.stringify(results?.module5?.fairness_metrics, null, 2)}</pre>
              ) : (
                <p className="muted">No fairness metrics available.</p>
              )}
            </div>

            <div className="result-card wide">
              <h3>Module 6 Debiasing Results</h3>
              <h4>Weights Summary</h4>
              {results?.module6?.weights_summary ? (
                <div>
                  <p><strong>Min Weight:</strong> {results?.module6?.weights_summary?.min?.toFixed(4)}</p>
                  <p><strong>Max Weight:</strong> {results?.module6?.weights_summary?.max?.toFixed(4)}</p>
                  <p><strong>Mean Weight:</strong> {results?.module6?.weights_summary?.mean?.toFixed(4)}</p>
                </div>
              ) : (
                <p className="muted">No weights summary available.</p>
              )}

              <h4>Reweighted Model Results</h4>
              {results?.module6?.reweighted_results ? (
                <div>
                  <p><strong>Predictions:</strong> [{results?.module6?.reweighted_results?.predictions?.join(", ")}]</p>
                  <p><strong>Probabilities:</strong></p>
                  <pre>{JSON.stringify(results?.module6?.reweighted_results?.probabilities, null, 2)}</pre>
                </div>
              ) : (
                <p className="muted">No reweighted results available.</p>
              )}

              <h4>Resampled Model Results</h4>
              {results?.module6?.resampled_results ? (
                <div>
                  <p><strong>Predictions:</strong> [{results?.module6?.resampled_results?.predictions?.join(", ")}]</p>
                  <p><strong>Probabilities:</strong></p>
                  <pre>{JSON.stringify(results?.module6?.resampled_results?.probabilities, null, 2)}</pre>
                </div>
              ) : (
                <p className="muted">No resampled results available.</p>
              )}

              <h4>Debiasing Effect</h4>
              {Object.keys(results?.module6?.debiasing_effect || {}).length ? (
                <div>
                  <p><strong>Bias Reduction:</strong></p>
                  <pre>{JSON.stringify(results?.module6?.debiasing_effect?.bias_reduction, null, 2)}</pre>
                  <p><strong>Fairness Improvement:</strong></p>
                  <pre>{JSON.stringify(results?.module6?.debiasing_effect?.fairness_improvement, null, 2)}</pre>
                </div>
              ) : (
                <p className="muted">No debiasing effect available.</p>
              )}
            </div>

            <div className="result-card wide">
              <h3>Result Snapshot (JSON)</h3>
              <pre>{JSON.stringify(resultSnapshot, null, 2)}</pre>
            </div>
          </div>
        </section>
      )}

      {error && <p className="error">{error}</p>}
      {loading && <p className="muted">Working on current step...</p>}
    </div>
  );
}

export default App;
