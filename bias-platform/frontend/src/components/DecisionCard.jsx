import { useState, useEffect } from "react";

function riskClass(value) {
  const normalized = String(value || "").toLowerCase();
  if (normalized.includes("high")) return "badge error";
  if (normalized.includes("moderate")) return "badge warning";
  return "badge good";
}

function formatFeature(name) {
  if (!name) return "";
  return name
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function pct(probabilities) {
  const p = probabilities?.[1];
  return typeof p === "number" ? (p * 100).toFixed(1) + "%" : "N/A";
}

function DecisionCard({ decision, loading, onScoreRecord }) {
  const [isOpen, setIsOpen] = useState(false);
  const [rowInput, setRowInput] = useState(String(decision?.row_index ?? 0));

  useEffect(() => {
    setRowInput(String(decision?.row_index ?? 0));
  }, [decision?.row_index]);
  const [visibleCount, setVisibleCount] = useState(0);
  const [animKey, setAnimKey] = useState(0);

  const features = Array.isArray(decision?.top_features) ? decision.top_features : [];

  // Stagger-reveal feature items when accordion opens or replay triggered
  useEffect(() => {
    if (!isOpen) {
      setVisibleCount(0);
      return;
    }
    setVisibleCount(0);
    const timers = features.map((_, i) =>
      setTimeout(() => setVisibleCount(i + 1), 200 + i * 220)
    );
    return () => timers.forEach(clearTimeout);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, animKey]);

  const handlePlay = (e) => {
    e.stopPropagation();
    setAnimKey((k) => k + 1);
  };

  if (!decision) return null;

  const confidence =
    typeof decision?.confidence === "number"
      ? (decision.confidence * 100).toFixed(1) + "%"
      : "N/A";

  const biasRisk = decision?.bias_flag || "unknown";

  const explanation =
    decision?.ai_explanation ||
    decision?.explanation ||
    "No explanation available";

  const maxRow = Math.max(0, (decision?.n_rows ?? 1) - 1);
  const rowValue = Number(rowInput);
  const rowValid = rowInput !== "" && Number.isInteger(rowValue) && rowValue >= 0 && rowValue <= maxRow;

  const submitRow = (e) => {
    e.preventDefault();
    if (rowValid && onScoreRecord) onScoreRecord(rowValue);
  };

  return (
    <div className="result-card decision-card">
      <h3>Decision</h3>

      <form className="inline-row" onSubmit={submitRow}>
        <div className="field-group">
          <label htmlFor="record-index">Record # (0–{maxRow.toLocaleString()})</label>
          <input
            id="record-index"
            type="number"
            min={0}
            max={maxRow}
            value={rowInput}
            disabled={loading}
            onChange={(e) => setRowInput(e.target.value)}
          />
        </div>
        <button type="submit" className="btn-primary" disabled={loading || !rowValid}>
          Score record
        </button>
      </form>

      <p>
        <strong>Decision:</strong> {decision?.decision || "N/A"}
        {decision?.predicted_class != null && ` (predicted: ${decision.predicted_class})`}
      </p>
      <p><strong>Confidence:</strong> {confidence}</p>
      <p>
        <strong>Positive probability:</strong> {pct(decision?.original_probabilities)} original
        {decision?.debiased && ` → ${pct(decision?.probabilities)} after mitigation`}
      </p>
      <p className={riskClass(biasRisk)}><strong>Bias Risk:</strong> {biasRisk}</p>

      <div className="decision-why-wrapper">
        <button
          className="decision-why-btn"
          onClick={() => setIsOpen((prev) => !prev)}
          aria-expanded={isOpen}
        >
          <span>Why this decision?</span>
          <div className="decision-why-actions">
            {isOpen && features.length > 0 && (
              <span className="play-btn" title="Replay animation" onClick={handlePlay}>
                <svg width="13" height="13" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.348a1.125 1.125 0 010 1.971l-11.54 6.347a1.125 1.125 0 01-1.667-.985V5.653z" />
                </svg>
              </span>
            )}
            <svg
              className={`chevron ${isOpen ? "open" : ""}`}
              width="16" height="16"
              fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
            </svg>
          </div>
        </button>

        <div className={`decision-why-content ${isOpen ? "open" : ""}`}>
          <div className="decision-why-inner">
            <p style={{ lineHeight: "1.6" }}>{explanation}</p>

            {features.length > 0 && (
              <ul className="feature-list">
                {features.map((item, i) => (
                  <li
                    key={`${animKey}-${i}`}
                    className={`feature-item ${i < visibleCount ? "visible" : ""}`}
                  >
                    <span>{formatFeature(item.feature)}</span>
                    <strong>
                      {typeof item.impact === "number"
                        ? item.impact.toFixed(3)
                        : item.score ?? "N/A"}
                    </strong>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default DecisionCard;