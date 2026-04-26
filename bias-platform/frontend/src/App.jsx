import { useMemo, useState } from "react";
import ColumnSelector from "./components/ColumnSelector";
import PipelineRunner from "./components/PipelineRunner";
import ResultsDashboard from "./components/ResultsDashboard";
import UploadPanel from "./components/UploadPanel";
import { getResults, initContract, runPipeline, selectBias, uploadFile } from "./services/api";

const steps = [
  "Upload Dataset",
  "Select Target + Bias",
  "Run Full Pipeline",
  "View Decision Dashboard",
];

function formatApiError(err, fallbackMessage) {
  const detail = err?.response?.data?.detail;
  const message = typeof detail === "string" ? detail : "";

  if (message.includes("Encoders require their input argument must be uniformly strings or numbers")) {
    return "Data preprocessing failed because one or more columns contain mixed value types. Please normalize those columns in the CSV and try again.";
  }

  return message || fallbackMessage;
}

function App() {
  const [step, setStep] = useState(0);
  const [file, setFile] = useState(null);
  const [uploadData, setUploadData] = useState(null);
  const [contract, setContract] = useState(null);
  const [targetColumn, setTargetColumn] = useState("");
  const [selectedBias, setSelectedBias] = useState([]);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const selectableColumns = useMemo(() => {
    if (uploadData?.columns?.length) return uploadData.columns;
    if (!contract?.X?.length) return [];
    return Object.keys(contract.X[0]);
  }, [contract, uploadData]);

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
      setStep(1);
    } catch (err) {
      setError(formatApiError(err, "Upload failed."));
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
      setStep(1);
    } catch (err) {
      setError(formatApiError(err, "Contract initialization failed."));
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
      setStep(2);
    } catch (err) {
      setError(formatApiError(err, "Bias selection failed."));
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
      setStep(3);
    } catch (err) {
      setError(formatApiError(err, "Pipeline run failed."));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <header className="topbar">
        <div className="brand">Bias Platform</div>
        <nav className="topnav">
          <a href="#home">Home</a>
          <a href="#pipeline">Pipeline</a>
          <a href="#results">Results</a>
        </nav>
      </header>

      <main className="container" id="home">
        <section className="hero">
          <h1>Decision Intelligence Dashboard</h1>
          <p className="lead">
            Upload data, run fairness-aware inference, and inspect decision, validation, and monitoring outputs.
          </p>
        </section>

        <section id="pipeline">
          <h2>Pipeline Progress</h2>
          <div className="stepper">
            {steps.map((label, idx) => (
              <div key={label} className={`step ${step >= idx ? "active" : ""}`}>
                <span>{idx + 1}</span>
                <p>{label}</p>
              </div>
            ))}
          </div>
        </section>

        <UploadPanel file={file} loading={loading} onFileChange={setFile} onUpload={onUpload} />

        {uploadData && (
          <ColumnSelector
            columns={selectableColumns}
            targetColumn={targetColumn}
            selectedBias={selectedBias}
            loading={loading}
            onTargetChange={setTargetColumn}
            onBiasChange={setSelectedBias}
            onInitContract={onInitContract}
            onSaveBias={onSelectBias}
          />
        )}

        {contract && <PipelineRunner loading={loading} hasResults={Boolean(results)} onRunPipeline={onRunPipeline} />}

        {results && <ResultsDashboard results={results} />}

        {error && <p className="error">{error}</p>}
        {loading && <p className="muted">Working on current step...</p>}
      </main>

      <footer className="footer">
        <a href="#home">Terms</a>
        <a href="#home">Privacy</a>
        <a href="#home">Contact</a>
      </footer>
    </div>
  );
}

export default App;