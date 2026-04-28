function ColumnSelector({
  columns,
  targetColumn,
  selectedBias,
  loading,
  onTargetChange,
  onBiasChange,
  onInitContract,
  onSaveBias,
}) {
  const biasOptions = columns.filter((column) => column !== targetColumn);

  return (
    <section>
      <h2>Step 2: Select Target + Bias Columns</h2>

      <div className="field-group">
        <label htmlFor="target-column">Target Column</label>
        <div className="inline-row">
          <select id="target-column" value={targetColumn} onChange={(e) => onTargetChange(e.target.value)}>
            <option value="">Select target column</option>
            {columns.map((column) => (
              <option key={column} value={column}>
                {column}
              </option>
            ))}
          </select>
          <button className="btn-secondary" onClick={onInitContract} disabled={loading || !targetColumn}>
            Initialize Contract
          </button>
        </div>
      </div>

      <div className="field-group">
        <label htmlFor="bias-columns">Bias Columns</label>
        <div className="inline-row">
          <select
            id="bias-columns"
            value={selectedBias[0] || ""}
            onChange={(e) => onBiasChange(e.target.value ? [e.target.value] : [])}
          >
            <option value="">Select bias column</option>
            {biasOptions.map((column) => (
              <option key={column} value={column}>
                {column}
              </option>
            ))}
          </select>
          <button className="btn-primary" onClick={onSaveBias} disabled={loading}>
            Save Bias Selection
          </button>
        </div>
      </div>
    </section>
  );
}

export default ColumnSelector;
