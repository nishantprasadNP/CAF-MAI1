import { useEffect, useRef, useState } from "react";

function formatFeature(name) {
  if (!name) return "";
  return name
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function ExplainabilityPanel({ explainability }) {
  const features = explainability?.top_features || [];
  const [isVisible, setIsVisible] = useState(false);
  const sectionRef = useRef(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          observer.unobserve(entry.target);
        }
      },
      { threshold: 0.1 }
    );

    if (sectionRef.current) {
      observer.observe(sectionRef.current);
    }

    return () => observer.disconnect();
  }, []);

  return (
    <div className="result-card wide" ref={sectionRef}>
      <h3>Explainability</h3>

      <p>
        <strong>Bias Contribution:</strong>{" "}
        {explainability?.biasContribution ?? "N/A"}
      </p>

      <h4>Top Features</h4>

      <ul className="feature-list">
        {features.length ? (
          features.map((item, i) => (
            <li key={i} className={`feature-item ${isVisible ? "visible" : ""}`}>
              <span className="name">{formatFeature(item.feature)}</span>
              <strong className="value">
                {typeof item.impact === "number"
                  ? item.impact.toFixed(3)
                  : item.score ?? "N/A"}
              </strong>
            </li>
          ))
        ) : (
          <li className={`feature-item ${isVisible ? "visible" : ""}`}>
            <span className="name">No feature data</span>
          </li>
        )}
      </ul>
    </div>
  );
}

export default ExplainabilityPanel;