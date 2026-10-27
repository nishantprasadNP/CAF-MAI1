function FairnessPanel({ data, debias }) {
  if (!data) return null;

  const summary = data.summary || {};

  const accuracy = data.accuracy ?? 0;
  const f1 = data.f1 ?? 0;

  const biasGap = summary.bias_gap ?? 0;
  const fairnessCount = data.num_fairness_metrics ?? 0;

  const before = debias?.before;
  const after = debias?.after;
  const improvement = debias?.improvement;
  // Matches the backend's mitigation threshold (module6 MIN_BIAS_GAP).
  const alreadyFair = typeof before === "number" && before < 0.03;

  // Same bands as the backend's classify_bias: <0.1 low, <0.2 moderate, else high.
  const getBadgeClass = (value) => {
    if (value < 0.1) return "badge good";
    if (value < 0.2) return "badge warning";
    return "badge error";
  };

  // Determine progress bar class
  const getProgressClass = (value) => {
    if (value >= 0.8) return "fill good";
    if (value >= 0.6) return "fill warning";
    return "fill error";
  };

  return (
    <div className="result-card wide">
      <h3>Model + Fairness Summary</h3>

      <div className="summary-grid">
        <div className="stat-card">
          <div className="stat-header">
            <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M10.5 6a7.5 7.5 0 107.5 7.5h-7.5V6z" /><path strokeLinecap="round" strokeLinejoin="round" d="M13.5 10.5H21A7.5 7.5 0 0013.5 3v7.5z" /></svg>
            <div className="label">Accuracy</div>
          </div>
          <div className="stat-body">
            <div className="stat-front">
              <div className="value">{(accuracy * 100).toFixed(1)}%</div>
              <div className="stat-desc">Overall predictive performance</div>
              <div className="progress-bar">
                <div 
                  className={getProgressClass(accuracy)} 
                  style={{ 
                    width: `${(accuracy * 100).toFixed(1)}%`,
                    minWidth: accuracy > 0 ? '4px' : '0'
                  }}
                ></div>
              </div>
            </div>
            <div className="stat-back">
              Percentage of correctly predicted outcomes on the held-out evaluation split (after bias mitigation). A higher value indicates better general performance, but must be weighed against fairness metrics.
            </div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z" /></svg>
            <div className="label">F1 Score</div>
          </div>
          <div className="stat-body">
            <div className="stat-front">
              <div className="value">{(f1 * 100).toFixed(1)}%</div>
              <div className="stat-desc">Balance of precision and recall</div>
              <div className="progress-bar">
                <div 
                  className={getProgressClass(f1)} 
                  style={{ 
                    width: `${(f1 * 100).toFixed(1)}%`,
                    minWidth: f1 > 0 ? '4px' : '0'
                  }}
                ></div>
              </div>
            </div>
            <div className="stat-back">
              Harmonic mean of precision and recall. Useful for imbalanced datasets where raw accuracy might be misleading. Shows overall robustness of the model predictions.
            </div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M12 3v2.25m6.364.386l-1.591 1.591M21 12h-2.25m-.386 6.364l-1.591-1.591M12 18.75V21m-4.773-4.227l-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z" /></svg>
            <div className="label">Bias Gap</div>
          </div>
          <div className="stat-body">
            <div className="stat-front">
              <div className="value">{biasGap.toFixed(2)}</div>
              <div className="stat-desc" style={{marginBottom: "8px"}}>Difference across groups</div>
              <span className={getBadgeClass(biasGap)}>
                {biasGap < 0.1 ? "Low" : biasGap < 0.2 ? "Moderate" : "High"}
              </span>
            </div>
            <div className="stat-back">
              Largest difference in positive-prediction rate between groups of your sensitive attribute, measured on the held-out split after mitigation. 0.0 means every group is approved at the same rate.
            </div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3v11.25A2.25 2.25 0 006 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0118 16.5h-2.25m-7.5 0h7.5m-7.5 0l-1 3m8.5-3l1 3m0 0l.5 1.5m-.5-1.5h-9.5m0 0l-.5 1.5M9 11.25v1.5M12 9v3.75m3-6v6" /></svg>
            <div className="label">Fairness Metrics</div>
          </div>
          <div className="stat-body">
            <div className="stat-front">
              <div className="value">{fairnessCount}</div>
              <div className="stat-desc" style={{marginBottom: "8px"}}>Metrics evaluated</div>
              <span className="badge good">Active</span>
            </div>
            <div className="stat-back">
              Demographic parity, equal opportunity, equalized odds and predictive parity, computed per sensitive attribute on the held-out split.
            </div>
          </div>
        </div>
      </div>

      <h4 style={{ marginTop: '24px', fontFamily: "'Plus Jakarta Sans', sans-serif", fontWeight: 800 }}>Debiasing Impact</h4>

      <div className="summary-grid">
        <div className="stat-card">
          <div className="stat-header">
            <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
            <div className="label">Before Fairness</div>
          </div>
          <div className="stat-body">
            <div className="stat-front">
              <div className="value">{typeof before === "number" ? before.toFixed(2) : "—"}</div>
              <div className="stat-desc">Original disparity measure</div>
            </div>
            <div className="stat-back">
              The bias gap of the baseline model on the held-out split, before any mitigation was applied.
            </div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
            <div className="label">After Fairness</div>
          </div>
          <div className="stat-body">
            <div className="stat-front">
              <div className="value">{typeof after === "number" ? after.toFixed(2) : "—"}</div>
              <div className="stat-desc">Disparity after mitigation</div>
            </div>
            <div className="stat-back">
              The bias gap on the same held-out split after mitigation: reweighing the training data plus group-specific decision thresholds fitted on the training split.
            </div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M2.25 18L9 11.25l4.306 4.307a11.95 11.95 0 015.814-5.519l2.74-1.22m0 0l-5.94-2.28m5.94 2.28l-2.28 5.941" /></svg>
            <div className="label">Improvement</div>
          </div>
          <div className="stat-body">
            <div className="stat-front">
              <div className="value">
                {alreadyFair
                  ? "N/A"
                  : typeof improvement === "number"
                  ? improvement.toFixed(2)
                  : "—"}
              </div>
              <div className="stat-desc" style={{marginBottom: "8px"}}>
                Net reduction in bias gap
                {typeof debias?.accuracy_before === "number" && typeof debias?.accuracy_after === "number" &&
                  ` · accuracy ${(debias.accuracy_before * 100).toFixed(1)}% → ${(debias.accuracy_after * 100).toFixed(1)}%`}
              </div>
              {alreadyFair && <span className="badge good">Already Fair</span>}
              {!alreadyFair && typeof improvement === "number" && improvement < 0 && (
                <span className="badge error">Gap increased</span>
              )}
            </div>
            <div className="stat-back">
              Before minus after. Positive values mean mitigation reduced the gap; compare the accuracy change to see what it cost in predictive performance.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default FairnessPanel;