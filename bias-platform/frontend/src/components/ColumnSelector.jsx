function ColumnSelector({
  columns,
  targetColumn,
  selectedBias,
  loading,
  onTargetChange,
  onBiasChange,
}) {
  const biasOptions = columns.filter((column) => column !== targetColumn);

  return (
    <section>
      <h2>Select Target + Bias Columns</h2>

      <div className="inline-row align-top">
        <div className="field-group" style={{ flex: 1 }}>
          <label htmlFor="target-column">Target Column</label>
          <select 
            id="target-column" 
            value={targetColumn} 
            onChange={(e) => onTargetChange(e.target.value)}
            disabled={loading}
          >
            <option value="">Select target column</option>
            {columns.map((column) => (
              <option key={column} value={column}>
                {column}
              </option>
            ))}
          </select>
        </div>

        <div className="field-group" style={{ flex: 1 }}>
          <label htmlFor="bias-columns">Sensitive Attribute (Bias Column)</label>
          <select
            id="bias-columns"
            value={selectedBias[0] || ""}
            onChange={(e) => onBiasChange(e.target.value ? [e.target.value] : [])}
            disabled={loading}
          >
            <option value="">Select bias column</option>
            {biasOptions.map((column) => (
              <option key={column} value={column}>
                {column}
              </option>
            ))}
          </select>
        </div>
      </div>
      <p className="muted">Selection is automatically saved.</p>
    </section>
  );
}

export default ColumnSelector;
