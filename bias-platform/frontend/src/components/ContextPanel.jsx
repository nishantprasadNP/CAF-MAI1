const options = {
  region: ["urban", "rural", "semi-urban"],
  hospital_type: ["private", "public", "teaching"],
  resource_level: ["high", "medium", "low"],
  time_of_day: ["day", "night", "evening"],
};

function ContextPanel({ contextInput, loading, onContextChange, onApplyContext }) {
  return (
    <section>
      <h2>Step 4: Set Context (Optional)</h2>
      <p className="muted">Apply context and trigger final inference by re-running the full pipeline.</p>
      <div className="context-grid">
        {Object.entries(options).map(([field, fieldOptions]) => (
          <div key={field} className="field-group">
            <label htmlFor={field}>{field}</label>
            <select id={field} value={contextInput[field]} onChange={(e) => onContextChange(field, e.target.value)}>
              {fieldOptions.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </div>
        ))}
      </div>
      <button onClick={onApplyContext} disabled={loading}>
        {loading ? "Applying Context..." : "Step 5: Re-run Final Inference"}
      </button>
    </section>
  );
}

export default ContextPanel;
