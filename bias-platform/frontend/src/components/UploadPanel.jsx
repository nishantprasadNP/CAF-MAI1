function UploadPanel({ file, loading, onFileChange, onUpload }) {
  return (
    <section>
      <h2>Upload Dataset</h2>
      <p className="muted">Upload a CSV to initialize the full pipeline.</p>
      <div className="inline-row">
        <input type="file" accept=".csv" onChange={(e) => onFileChange(e.target.files?.[0] || null)} />
        <button className="btn-primary" onClick={onUpload} disabled={loading || !file}>
          {loading ? "Uploading..." : "Upload CSV"}
        </button>
      </div>
    </section>
  );
}

export default UploadPanel;
