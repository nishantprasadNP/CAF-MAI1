function PipelineRunner({ loading, hasResults, canRun, availableResources, onResourcesChange, onRunPipeline }) {
  return (
    <section>
      <h2>Run Full Pipeline</h2>
      <p className="muted">
        Trains a model on 80% of the data, measures fairness on the held-out 20%, mitigates bias
        (reweighing + group-specific thresholds), then produces a decision, a resource feasibility
        check and monitoring signals.
      </p>
      <div className="inline-row">
        <div className="field-group">
          <label htmlFor="available-resources">Available Resources</label>
          <input
            id="available-resources"
            type="number"
            min={0}
            max={1000}
            value={availableResources}
            disabled={loading}
            onChange={(e) => onResourcesChange(Math.max(0, Math.min(1000, Number(e.target.value) || 0)))}
          />
        </div>
        <button className="btn-primary" onClick={onRunPipeline} disabled={loading || !canRun}>
          {loading ? "Running..." : hasResults ? "Re-run Full Pipeline" : "Run Full Pipeline"}
        </button>
      </div>
      {!canRun && <p className="muted">Select a sensitive attribute above to enable the pipeline.</p>}
    </section>
  );
}

export default PipelineRunner;
