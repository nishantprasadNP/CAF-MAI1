import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Legend, LineChart, Line } from 'recharts';

const COLORS = ['#C8F000', '#111111', '#EF4444', '#F59E0B', '#22C55E'];

function ConfusionMatrix({ cm }) {
  if (!cm || typeof cm !== 'object') return null;

  const tp = cm.tp || 0;
  const fp = cm.fp || 0;
  const tn = cm.tn || 0;
  const fn = cm.fn || 0;
  const total = tp + fp + tn + fn;

  const getIntensity = (val) => {
    if (total === 0) return 0.1;
    return 0.1 + (val / total) * 0.9;
  };

  return (
    <div className="cm-container">
      <div className="cm-grid">
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
        <p className="muted">Heatmap intensity based on sample distribution.</p>
      </div>
    </div>
  );
}

function OutcomeCharts({ fairness, debias }) {
  if (!fairness) return null;

  const { outcome_distribution, global_confusion_matrix, fairness_metrics } = fairness;

  // Prepare Pie Chart Data
  const pieData = outcome_distribution?.predicted ? Object.entries(outcome_distribution.predicted).map(([label, value]) => ({
    name: label === '1' ? 'Positive' : 'Negative',
    value: value
  })) : [];

  // Prepare Bar Chart Data (Fairness Metrics across groups)
  const barData = [];
  if (fairness_metrics) {
    Object.entries(fairness_metrics).forEach(([column, data]) => {
      if (data.groups) {
        Object.entries(data.groups).forEach(([group, metrics]) => {
          barData.push({
            group: `${column}: ${group}`,
            DP: parseFloat((metrics.demographic_parity * 100).toFixed(1)),
            EO: parseFloat((metrics.equal_opportunity * 100).toFixed(1)),
          });
        });
      }
    });
  }

  // Prepare Debiasing Trend Data
  const trendData = [
    { name: 'Before', value: debias?.before || 0 },
    { name: 'After', value: debias?.after || 0 },
  ];

  return (
    <div className="outcome-charts-wrapper">
      <div className="charts-grid">
        {/* Outcome Distribution Pie */}
        <div className="chart-card">
          <h4>Predicted Distribution</h4>
          <div style={{ width: '100%', height: 300 }}>
            <ResponsiveContainer>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <p className="muted text-center">Class balance of model predictions</p>
        </div>

        {/* Debiasing Trend Line Chart */}
        <div className="chart-card">
          <h4>Debiasing Disparity Trend</h4>
          <div style={{ width: '100%', height: 300 }}>
            <ResponsiveContainer>
              <LineChart data={trendData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="name" />
                <YAxis label={{ value: 'Bias Gap', angle: -90, position: 'insideLeft' }} />
                <Tooltip />
                <Line type="monotone" dataKey="value" stroke="#C8F000" strokeWidth={4} dot={{ r: 8, fill: '#C8F000' }} activeDot={{ r: 10 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <p className="muted text-center">Reduction in bias gap after mitigation</p>
        </div>

        {/* Fairness Metrics Bar Chart */}
        <div className="chart-card wide">
          <h4>Subgroup Performance Distribution</h4>
          <div style={{ width: '100%', height: 350 }}>
            <ResponsiveContainer>
              <BarChart data={barData} margin={{ top: 20, right: 30, left: 20, bottom: 80 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="group" angle={-45} textAnchor="end" interval={0} height={100} />
                <YAxis unit="%" />
                <Tooltip />
                <Legend verticalAlign="top" height={36}/>
                <Bar dataKey="DP" name="Demographic Parity" fill="#C8F000" radius={[4, 4, 0, 0]} />
                <Bar dataKey="EO" name="Equal Opportunity" fill="#111111" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Confusion Matrix */}
        <div className="chart-card">
          <h4>Confusion Matrix (Heatmap)</h4>
          <ConfusionMatrix cm={global_confusion_matrix} />
        </div>
      </div>
    </div>
  );
}

export default OutcomeCharts;
