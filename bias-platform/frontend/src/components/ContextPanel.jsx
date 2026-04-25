const options = {
  region: ["urban", "rural", "semi-urban"],
  hospital_type: ["private", "public", "teaching"],
  resource_level: ["high", "medium", "low"],
  time_of_day: ["day", "night", "evening"],
};

function ContextPanel({
  contextInput,
  contextResult,
  loading,
  onContextChange,
  onApplyContext,
}) {
  // 🔥 SAFE EXTRACTION
  const baseProb = Array.isArray(contextResult?.base_probability)
    ? contextResult.base_probability[1]
    : undefined;

  const finalProb = Array.isArray(contextResult?.final_probability)
    ? contextResult.final_probability[1]
    : undefined;

  const impact =
    typeof baseProb === "number" && typeof finalProb === "number"
      ? (finalProb - baseProb).toFixed(2)
      : null;

  return (
    <section>
      <h2>Step 4: Set Context (Optional)</h2>
      <p className="muted">
        Apply context and trigger final inference by re-running the full pipeline.
      </p>

      {/* -------- CONTEXT INPUT -------- */}
      <div className="context-grid">
        {Object.entries(options).map(([field, fieldOptions]) => (
          <div key={field} className="field-group">
            <label htmlFor={field}>{field}</label>

            <select
              id={field}
              value={contextInput?.[field] || fieldOptions[0]} // ✅ FIX HERE
              onChange={(e) => onContextChange(field, e.target.value)}
            >
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

      {/* -------- CONTEXT OUTPUT -------- */}
      {contextResult && (
        <div className="context-output">
          <h3>Context Impact</h3>

          <p>
            <strong>Base Probability:</strong>{" "}
            {typeof baseProb === "number" ? baseProb.toFixed(2) : "N/A"}
          </p>

          <p>
            <strong>Context-adjusted Probability:</strong>{" "}
            {typeof finalProb === "number" ? finalProb.toFixed(2) : "N/A"}
          </p>

          <p>
            <strong>Impact:</strong>{" "}
            {impact !== null ? (
              <span style={{ color: impact >= 0 ? "green" : "red" }}>
                {impact >= 0 ? "+" : ""}
                {impact}
              </span>
            ) : (
              "N/A"
            )}
          </p>

          <p>
            <strong>Context Confidence:</strong>{" "}
            {contextResult?.confidence || "Unknown"}
          </p>

          <p>
            <strong>Reason:</strong>{" "}
            {contextResult?.reason || "No context explanation available"}
          </p>
        </div>
      )}
    </section>
  );
}

export default ContextPanel;