/**
 * RevenueCommandCenter.jsx
 *
 * Executive Command Center displaying primary financial recovery metrics,
 * opportunity value comparison (At Risk vs Expected vs Recovered),
 * and high-impact merchant recovery KPIs.
 *
 * All metrics originate from backend data.
 */
import React from 'react'

function fmtINR(amount) {
  return '₹' + Number(amount || 0).toLocaleString('en-IN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

function fmtPct(rate) {
  return (Number(rate || 0) * 100).toFixed(1) + '%'
}

export default function RevenueCommandCenter({ metrics }) {
  if (!metrics) return null

  return (
    <section className="revenue-command-center" aria-label="Revenue Recovery Command Center">
      {/* ──── REVENUE IMPACT HERO BLOCK ──── */}
      <div className="impact-hero-card card">
        <div className="impact-hero-header">
          <span className="impact-badge">REVIVEAI REVENUE IMPACT</span>
          <span className="live-tag">
            <span className="live-dot" /> LIVE RECOVERY METRICS
          </span>
        </div>

        <div className="impact-hero-body">
          <div className="impact-main-metric">
            <span className="impact-label">Total Revenue Recovered</span>
            <div className="impact-value-wrap">
              <h1 className="impact-amount">{fmtINR(metrics.total_revenue_recovered)}</h1>
              <span className="impact-tag-positive">
                +{fmtPct(metrics.revenue_recovery_rate)} Recovered
              </span>
            </div>
            <p className="impact-caption">
              Directly restored to merchant cashflow from{' '}
              <strong>{fmtINR(metrics.total_revenue_at_risk)}</strong> initial risk across{' '}
              <strong>{metrics.total_payments}</strong> payment failures.
            </p>
          </div>

          <div className="impact-stats-cluster">
            <div className="impact-stat-item">
              <span className="stat-label">Recovery Success Rate</span>
              <span className="stat-value text-success">{fmtPct(metrics.recovery_rate)}</span>
              <span className="stat-sub">{metrics.successful_recoveries} of {metrics.recovery_attempts} retries</span>
            </div>
            <div className="impact-stat-item">
              <span className="stat-label">Payments Recovered</span>
              <span className="stat-value text-white">{metrics.successful_recoveries}</span>
              <span className="stat-sub">Automated & Bounded</span>
            </div>
            <div className="impact-stat-item">
              <span className="stat-label">Guardrail Protected</span>
              <span className="stat-value text-danger">{metrics.blocked_payments}</span>
              <span className="stat-sub">Zero money wasted</span>
            </div>
          </div>
        </div>

        {/* Value Comparison Bar */}
        <div className="opportunity-value-bar-container">
          <div className="value-bar-header">
            <span>Opportunity Value Comparison</span>
            <span className="text-muted">Expected vs Actual Recovered</span>
          </div>
          <div className="value-bar-track">
            <div
              className="value-bar-fill value-bar-fill--recovered"
              style={{
                width: `${Math.min(100, Math.max(5, (metrics.total_revenue_recovered / (metrics.total_revenue_at_risk || 1)) * 100))}%`,
              }}
              title={`Recovered: ${fmtINR(metrics.total_revenue_recovered)}`}
            />
            <div
              className="value-bar-marker"
              style={{
                left: `${Math.min(95, Math.max(10, (metrics.total_expected_recovery / (metrics.total_revenue_at_risk || 1)) * 100))}%`,
              }}
              title={`Expected: ${fmtINR(metrics.total_expected_recovery)}`}
            />
          </div>
          <div className="value-bar-legend">
            <div className="legend-item">
              <span className="legend-box legend-box--risk" />
              <span>Revenue at Risk: <strong>{fmtINR(metrics.total_revenue_at_risk)}</strong></span>
            </div>
            <div className="legend-item">
              <span className="legend-box legend-box--expected" />
              <span>Expected Potential: <strong>{fmtINR(metrics.total_expected_recovery)}</strong></span>
            </div>
            <div className="legend-item">
              <span className="legend-box legend-box--recovered" />
              <span>Actually Recovered: <strong>{fmtINR(metrics.total_revenue_recovered)}</strong></span>
            </div>
          </div>
        </div>
      </div>

      {/* ──── COMMAND CENTER METRICS GRID ──── */}
      <div className="command-metrics-grid">
        <div className="cmd-metric-card card">
          <span className="cmd-metric-title">Payments Analyzed</span>
          <span className="cmd-metric-val">{metrics.total_payments}</span>
          <span className="cmd-metric-sub text-muted">100% Deterministic Scope</span>
        </div>
        <div className="cmd-metric-card card">
          <span className="cmd-metric-title">Recovery Eligible</span>
          <span className="cmd-metric-val text-brand">{metrics.eligible_payments}</span>
          <span className="cmd-metric-sub text-muted">Passed Policy Guardrails</span>
        </div>
        <div className="cmd-metric-card card">
          <span className="cmd-metric-title">Recovery Blocked</span>
          <span className="cmd-metric-val text-danger">{metrics.blocked_payments}</span>
          <span className="cmd-metric-sub text-muted">Prevented Bad Retries</span>
        </div>
        <div className="cmd-metric-card card">
          <span className="cmd-metric-title">Recovery Attempts</span>
          <span className="cmd-metric-val">{metrics.recovery_attempts}</span>
          <span className="cmd-metric-sub text-muted">Bounded Execution</span>
        </div>
        <div className="cmd-metric-card card">
          <span className="cmd-metric-title">Successful Recoveries</span>
          <span className="cmd-metric-val text-success">{metrics.successful_recoveries}</span>
          <span className="cmd-metric-sub text-muted">Transactions Settled</span>
        </div>
        <div className="cmd-metric-card card">
          <span className="cmd-metric-title">Escalations / Deferred</span>
          <span className="cmd-metric-val text-warning">
            {(metrics.escalated_payments || 0) + (metrics.deferred_payments || 0)}
          </span>
          <span className="cmd-metric-sub text-muted">Cooldown or Human Flag</span>
        </div>
      </div>
    </section>
  )
}
