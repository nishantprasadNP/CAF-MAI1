function PipelineRunner({ loading, hasResults, onRunPipeline }) {
  return (
    <section>
      <h2>Step 3: Run Full Pipeline</h2>
      <p className="muted">
        This executes data, bias, model, fairness, debiasing, context-aware inference, decision, validation,
        compliance, and monitoring stages.
      </p>
      <button className="btn-primary" onClick={onRunPipeline} disabled={loading}>
        {loading ? "Running..." : hasResults ? "Re-run Full Pipeline" : "Run Full Pipeline"}
      </button>
    </section>
  );
}

export default PipelineRunner;
