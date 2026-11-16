
import { useEffect, useState } from 'react'
import {
  ResponsiveContainer,
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  AreaChart, Area, BarChart, Bar,
  PieChart, Pie, Cell, Legend
} from 'recharts'
import './style.css'

const API = 'http://127.0.0.1:8000'

const fields = [
  ['Global_active_power', 'Current active power (kW)', '1.10'],
  ['Global_reactive_power', 'Reactive power', '0.15'],
  ['Voltage', 'Voltage (V)', '240'],
  ['Global_intensity', 'Current intensity (A)', '5'],
  ['Sub_metering_1', 'Kitchen sub-metering', '0'],
  ['Sub_metering_2', 'Laundry sub-metering', '1'],
  ['Sub_metering_3', 'Other appliances sub-metering', '7'],
  ['power_lag_1', 'Active power 1 hour ago', '1.05'],
  ['power_lag_2', 'Active power 2 hours ago', '0.98'],
  ['power_lag_3', 'Active power 3 hours ago', '1.12'],
  ['power_rolling_mean_3', '3-hour rolling average', '1.08'],
  ['hour', 'Hour (0–23)', '14'],
  ['day_of_week', 'Day of week (Mon=0, Sun=6)', '2'],
]

const initial = Object.fromEntries(
  fields.map(([key, , value]) => [key, value])
)

const chartColors = ['#f4b942', '#4dd4ac', '#6c9cff']

function ChartCard({ title, subtitle, children }) {
  return (
    <section className="chart-card">
      <div className="chart-heading">
        <h3>{title}</h3>
        <p>{subtitle}</p>
      </div>
      {children}
    </section>
  )
}

function EmptyChart({ message }) {
  return <div className="empty-chart">{message}</div>
}

export default function App() {
  const [values, setValues] = useState(initial)
  const [result, setResult] = useState(null)
  const [predictionHistory, setPredictionHistory] = useState([])
  const [error, setError] = useState('')
  const [apiStatus, setApiStatus] = useState('Checking API...')
  const [loading, setLoading] = useState(false)
  const [analytics, setAnalytics] = useState(null)
  const [analyticsError, setAnalyticsError] = useState('')

  async function loadDashboard() {
    try {
      const [healthResponse, analyticsResponse] = await Promise.all([
        fetch(`${API}/health`),
        fetch(`${API}/analytics`)
      ])

      if (!healthResponse.ok) throw new Error('Backend is not responding')

      const health = await healthResponse.json()
      setApiStatus(
        health.model_ready
          ? 'API connected · model ready'
          : 'API connected · train model first'
      )

      if (!analyticsResponse.ok) {
        const data = await analyticsResponse.json()
        throw new Error(data.detail || 'Analytics are not available')
      }

      const data = await analyticsResponse.json()
      setAnalytics(data)
      setAnalyticsError('')
    } catch (err) {
      setApiStatus('API offline · start FastAPI backend')
      setAnalyticsError(err.message)
    }
  }

  useEffect(() => {
    loadDashboard()
  }, [])

  function update(key, value) {
    setValues(old => ({ ...old, [key]: value }))
  }

  async function predict(event) {
    event.preventDefault()
    setLoading(true)
    setError('')
    setResult(null)

    try {
      const payload = Object.fromEntries(
        Object.entries(values).map(([key, value]) => [key, Number(value)])
      )

      const response = await fetch(`${API}/predict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })

      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || 'Prediction failed')

      setResult(data)

      setPredictionHistory(old => [
        ...old.slice(-9),
        {
          prediction: Number(data.predicted_next_hour_active_power_kw),
          label: `Prediction ${old.length + 1}`
        }
      ])
    } catch (err) {
      setError(err.message || 'Could not reach the API')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="shell">
      <header className="top">
        <div className="brand-mark">⚡</div>
        <div>
          <p className="eyebrow">MACHINE LEARNING PROJECT</p>
          <h1>Smart Energy <span>Predictor</span></h1>
          <p className="sub">
            Monitor household electricity usage and predict future consumption.
          </p>
        </div>
        <div className="status">
          <i className={apiStatus.includes('offline') ? 'offline-dot' : ''} />
          {apiStatus}
        </div>
      </header>

      <section className="intro">
        <div>
          <p className="eyebrow">SMART ENERGY ANALYTICS</p>
          <h2>Understand your electricity consumption with machine learning.</h2>
          <p>Explore usage trends, appliance readings and model performance.</p>
        </div>
        <div className="bolt">⚡</div>
      </section>

      {analytics && (
        <>
          <section className="section-title">
            <div>
              <p className="eyebrow">OVERVIEW</p>
              <h2>Energy dashboard</h2>
              <p className="muted">
                Dataset period: {analytics.date_from} to {analytics.date_to}
              </p>
            </div>
            <button className="refresh-btn" type="button" onClick={loadDashboard}>
              ↻ Refresh data
            </button>
          </section>

          <section className="stats-grid">
            <div className="stat-card">
              <span>Total records</span>
              <strong>{analytics.total_records.toLocaleString()}</strong>
              <small>Processed hourly records</small>
            </div>
            <div className="stat-card">
              <span>Average active power</span>
              <strong>{analytics.average_active_power} <small>kW</small></strong>
              <small>Across the available dataset</small>
            </div>
            <div className="stat-card">
              <span>Maximum active power</span>
              <strong>{analytics.maximum_active_power} <small>kW</small></strong>
              <small>Highest recorded reading</small>
            </div>
            <div className="stat-card">
              <span>Models compared</span>
              <strong>{analytics.models.length}</strong>
              <small>Regression algorithms</small>
            </div>
          </section>

          <section className="charts-grid">
            <ChartCard
              title="Hourly energy consumption"
              subtitle="Most recent 48 processed readings · active power (kW)"
            >
              {analytics.hourly.length ? (
                <ResponsiveContainer width="100%" height={280}>
                  <AreaChart data={analytics.hourly}>
                    <defs>
                      <linearGradient id="powerFill" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#f4b942" stopOpacity={0.35} />
                        <stop offset="95%" stopColor="#f4b942" stopOpacity={0.01} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid stroke="#26374d" strokeDasharray="3 3" />
                    <XAxis dataKey="time" tick={{ fill: '#9baac0', fontSize: 10 }} />
                    <YAxis tick={{ fill: '#9baac0', fontSize: 11 }} />
                    <Tooltip contentStyle={{ background: '#101a29', border: '1px solid #35465c', borderRadius: 10 }} />
                    <Area
                      type="monotone"
                      dataKey="active_power"
                      name="Active power"
                      stroke="#f4b942"
                      fill="url(#powerFill)"
                      strokeWidth={2}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              ) : <EmptyChart message="No hourly readings available." />}
            </ChartCard>

            <ChartCard
              title="Daily consumption pattern"
              subtitle="Daily average active power · kW"
            >
              {analytics.daily.length ? (
                <ResponsiveContainer width="100%" height={280}>
                  <LineChart data={analytics.daily}>
                    <CartesianGrid stroke="#26374d" strokeDasharray="3 3" />
                    <XAxis dataKey="date" tick={{ fill: '#9baac0', fontSize: 11 }} />
                    <YAxis tick={{ fill: '#9baac0', fontSize: 11 }} />
                    <Tooltip contentStyle={{ background: '#101a29', border: '1px solid #35465c', borderRadius: 10 }} />
                    <Line
                      type="monotone"
                      dataKey="average_power"
                      name="Average power"
                      stroke="#4dd4ac"
                      strokeWidth={3}
                      dot={{ r: 3, fill: '#4dd4ac' }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              ) : <EmptyChart message="No daily readings available." />}
            </ChartCard>

            <ChartCard
              title="Appliance usage distribution"
              subtitle="Total sub-meter readings · Wh"
            >
              {analytics.appliances.length ? (
                <ResponsiveContainer width="100%" height={280}>
                  <PieChart>
                    <Pie
                      data={analytics.appliances}
                      dataKey="value"
                      nameKey="name"
                      cx="50%"
                      cy="46%"
                      outerRadius={90}
                      innerRadius={48}
                      paddingAngle={4}
                      label={({ name, percent }) =>
                        `${name} ${(percent * 100).toFixed(1)}%`
                      }
                    >
                      {analytics.appliances.map((item, index) => (
                        <Cell key={item.name} fill={chartColors[index % chartColors.length]} />
                      ))}
                    </Pie>
                    <Tooltip
                      formatter={(value) => `${Number(value).toLocaleString()} Wh`}
                      contentStyle={{ background: '#101a29', border: '1px solid #35465c', borderRadius: 10 }}
                    />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              ) : <EmptyChart message="No appliance readings available." />}
            </ChartCard>

            <ChartCard
              title="Machine learning model comparison"
              subtitle="Validation RMSE · lower values indicate better performance"
            >
              {analytics.models.length ? (
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={analytics.models} layout="vertical" margin={{ left: 12, right: 20 }}>
                    <CartesianGrid stroke="#26374d" strokeDasharray="3 3" />
                    <XAxis type="number" tick={{ fill: '#9baac0', fontSize: 11 }} />
                    <YAxis
                      type="category"
                      dataKey="model"
                      width={135}
                      tick={{ fill: '#c6d1df', fontSize: 10 }}
                    />
                    <Tooltip contentStyle={{ background: '#101a29', border: '1px solid #35465c', borderRadius: 10 }} />
                    <Bar dataKey="rmse" name="Validation RMSE" fill="#6c9cff" radius={[0, 6, 6, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : <EmptyChart message="Train the five models to display comparison." />}
            </ChartCard>
          </section>
        </>
      )}

      {!analytics && (
        <section className="panel analytics-message">
          <p className="eyebrow">DASHBOARD DATA</p>
          <h2>Charts are waiting for dataset analytics</h2>
          <p>{analyticsError || 'Connect the backend and prepare the dataset to load charts.'}</p>
          <button type="button" className="refresh-btn" onClick={loadDashboard}>
            Try again
          </button>
        </section>
      )}

      <section className="section-title prediction-heading">
        <div>
          <p className="eyebrow">MACHINE LEARNING</p>
          <h2>Next-hour prediction</h2>
          <p className="muted">Enter the latest meter readings to estimate future active power.</p>
        </div>
      </section>

      <form className="panel" onSubmit={predict}>
        <div className="panel-head">
          <div>
            <p className="eyebrow">INPUT DATA</p>
            <h2>Meter readings</h2>
          </div>
          <span className="tag">13 features</span>
        </div>

        <div className="fields">
          {fields.map(([key, label]) => (
            <label key={key}>
              <span>{label}</span>
              <input
                type="number"
                step="any"
                required
                value={values[key]}
                onChange={e => update(key, e.target.value)}
              />
            </label>
          ))}
        </div>

        <button disabled={loading} type="submit">
          {loading ? 'Predicting...' : 'Predict next-hour consumption →'}
        </button>

        {error && <p className="error">{error}</p>}

        {result && (
          <div className="result">
            <p className="eyebrow">PREDICTED NEXT-HOUR ACTIVE POWER</p>
            <strong>
              {result.predicted_next_hour_active_power_kw} <small>kW</small>
            </strong>
            <p>Generated by the trained regression model.</p>
          </div>
        )}
      </form>

      {predictionHistory.length > 0 && (
        <ChartCard
          title="Your prediction history"
          subtitle="Predictions generated during this browser session"
        >
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={predictionHistory}>
              <CartesianGrid stroke="#26374d" strokeDasharray="3 3" />
              <XAxis dataKey="label" tick={{ fill: '#9baac0', fontSize: 11 }} />
              <YAxis tick={{ fill: '#9baac0', fontSize: 11 }} />
              <Tooltip contentStyle={{ background: '#101a29', border: '1px solid #35465c', borderRadius: 10 }} />
              <Line
                type="monotone"
                dataKey="prediction"
                name="Predicted power (kW)"
                stroke="#4dd4ac"
                strokeWidth={3}
                dot={{ r: 5 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>
      )}

      <footer>
        Academic project prototype · Charts use processed dataset and model outputs.
      </footer>
    </main>
  )
}
