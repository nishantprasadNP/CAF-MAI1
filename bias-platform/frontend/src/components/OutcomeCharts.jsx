import { Tooltip, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Legend } from 'recharts';

const COLORS = ['#C8F000', '#111111', '#EF4444', '#F59E0B', '#22C55E'];

function ConfusionMatrix({ cm }) {
  if (!cm || typeof cm !== 'object') {
    return (
      <div className="empty-chart" style={{ height: 450 }}>
        <p>Run pipeline to generate matrix</p>
      </div>
    );
  }

  const tp = cm.tp ?? 0;
  const fp = cm.fp ?? 0;
  const tn = cm.tn ?? 0;
  const fn = cm.fn ?? 0;
  const total = tp + fp + tn + fn;

  const getIntensity = (val) => {
    if (total === 0) return 0.1;
    return 0.1 + (val / total) * 0.9;
  };

  return (
    <div className="cm-container" style={{ width: '100%' }}>
      <div className="cm-grid" style={{ margin: '0 auto', maxWidth: '400px' }}>
        <div className="cm-label-corner">Actual \ Pred</div>
        <div className="cm-label-top">Pos (1)</div>
        <div className="cm-label-top">Neg (0)</div>

        <div className="cm-label-side">Pos (1)</div>
        <div className="cm-cell" style={{ background: `rgba(200, 240, 0, ${getIntensity(tp)})` }}>
          <span className="cm-value">{tp}</span>
          <span className="cm-type">TP</span>
        </div>
        <div className="cm-cell" style={{ background: `rgba(239, 68, 68, ${getIntensity(fn)})` }}>
          <span className="cm-value">{fn}</span>
          <span className="cm-type">FN</span>
        </div>

        <div className="cm-label-side">Neg (0)</div>
        <div className="cm-cell" style={{ background: `rgba(245, 158, 11, ${getIntensity(fp)})` }}>
          <span className="cm-value">{fp}</span>
          <span className="cm-type">FP</span>
        </div>
        <div className="cm-cell" style={{ background: `rgba(34, 197, 94, ${getIntensity(tn)})` }}>
          <span className="cm-value">{tn}</span>
          <span className="cm-type">TN</span>
        </div>
      </div>
      <div className="cm-legend">
        <p className="muted">Heatmap intensity reflects sample frequency</p>
      </div>
    </div>
  );
}

function OutcomeCharts({ fairness }) {
  if (!fairness) return null;

  const { global_confusion_matrix, fairness_metrics } = fairness;

  // 1. Prepare Bar Chart Data
  const barData = [];
  if (fairness_metrics && typeof fairness_metrics === 'object') {
    Object.entries(fairness_metrics).forEach(([column, config]) => {
      if (config?.groups) {
        Object.entries(config.groups).forEach(([groupName, metrics]) => {
          barData.push({
            group: `${column}: ${groupName}`,
            DP: Number((metrics.demographic_parity * 100).toFixed(1)),
            EO: Number((metrics.equal_opportunity * 100).toFixed(1)),
          });
        });
      }
    });
  }

  return (
    <div className="outcome-charts-wrapper">
      <div className="charts-grid-side-by-side">
        {/* Fairness Metrics Bar Chart */}
        <div className="chart-card">
          <h4>Fairness Metrics by Subgroup</h4>
          {barData.length > 0 ? (
            <div style={{ width: '100%', height: 600 }}>
              <ResponsiveContainer>
                <BarChart 
                  data={barData} 
                  layout="vertical"
                  margin={{ top: 20, right: 30, left: 100, bottom: 20 }}
                >
                  <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke="#f0f0f0" />
                  <XAxis type="number" unit="%" domain={[0, 100]} axisLine={false} tickLine={false} />
                  <YAxis 
                    dataKey="group" 
                    type="category" 
                    width={150}
                    axisLine={false} 
                    tickLine={false}
                    tick={{ fontSize: 12, fill: '#666' }}
                  />
                  <Tooltip cursor={{fill: 'rgba(0,0,0,0.02)'}} />
                  <Legend verticalAlign="top" height={36}/>
                  <Bar dataKey="DP" name="Demographic Parity" fill="#C8F000" radius={[0, 4, 4, 0]} barSize={20} />
                  <Bar dataKey="EO" name="Equal Opportunity" fill="#111111" radius={[0, 4, 4, 0]} barSize={20} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="empty-chart" style={{ height: 450 }}>
              <p>Select a Sensitive Attribute in Step 2 to see subgroup analysis</p>
            </div>
          )}
        </div>

        {/* Confusion Matrix */}
        <div className="chart-card">
          <h4>Performance Heatmap</h4>
          <div style={{ height: 450, display: 'flex', alignItems: 'center', width: '100%' }}>
            <ConfusionMatrix cm={global_confusion_matrix} />
          </div>
        </div>
      </div>
    </div>
  );
}

export default OutcomeCharts;
