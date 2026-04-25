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
        <select id="target-column" value={targetColumn} onChange={(e) => onTargetChange(e.target.value)}>
          <option value="">Select target column</option>
          {columns.map((column) => (
            <option key={column} value={column}>
              {column}
            </option>
          ))}
        </select>
        <button onClick={onInitContract} disabled={loading || !targetColumn}>
          Initialize Contract
        </button>
      </div>

      <div className="field-group">
        <label htmlFor="bias-columns">Bias Columns</label>
        <select
          id="bias-columns"
          multiple
          value={selectedBias}
          onChange={(e) => onBiasChange(Array.from(e.target.selectedOptions).map((option) => option.value))}
        >
          {biasOptions.map((column) => (
            <option key={column} value={column}>
              {column}
            </option>
          ))}
        </select>
        <button onClick={onSaveBias} disabled={loading}>
          Save Bias Selection
        </button>
      </div>
    </section>
  );
}

export default ColumnSelector;
