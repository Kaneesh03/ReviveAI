/**
 * RecoveryFunnel.jsx
 *
 * Visual Recovery Funnel displaying the end-to-end conversion:
 * Failed Payments -> Eligible -> Recovery Attempts -> Successful Recoveries -> Revenue Recovered
 *
 * All values are derived from backend BatchMetrics.
 * No numbers are fabricated or estimated on the client.
 */
import React from 'react'

function fmtINR(amount) {
  return '₹' + Number(amount).toLocaleString('en-IN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

function fmtPct(rate) {
  return (Number(rate) * 100).toFixed(1) + '%'
}

export default function RecoveryFunnel({ metrics }) {
  if (!metrics) return null

  const steps = [
    {
      id: 'failed',
      label: 'Failed Payments',
      count: metrics.total_payments,
      value: fmtINR(metrics.total_revenue_at_risk),
      subtext: 'Identified at Risk',
      color: 'var(--color-slate-400)',
      bg: 'rgba(148, 163, 184, 0.1)',
      border: 'rgba(148, 163, 184, 0.25)',
      widthPct: 100,
    },
    {
      id: 'eligible',
      label: 'Policy Eligible',
      count: metrics.eligible_payments,
      value: fmtINR(metrics.total_expected_recovery),
      subtext: `${metrics.blocked_payments} Blocked by Guardrails`,
      color: 'var(--color-brand)',
      bg: 'rgba(99, 102, 241, 0.1)',
      border: 'rgba(99, 102, 241, 0.3)',
      widthPct: 82,
    },
    {
      id: 'attempts',
      label: 'Recovery Attempts',
      count: metrics.recovery_attempts,
      value: `${metrics.recovery_attempts} Automated Retries`,
      subtext: `${metrics.deferred_payments || 0} Deferred / Cooldown`,
      color: 'var(--color-warning)',
      bg: 'rgba(245, 158, 11, 0.1)',
      border: 'rgba(245, 158, 11, 0.3)',
      widthPct: 65,
    },
    {
      id: 'successful',
      label: 'Successful Recoveries',
      count: metrics.successful_recoveries,
      value: `${fmtPct(metrics.recovery_rate)} Attempt Success Rate`,
      subtext: `${metrics.failed_recoveries} Failed Attempts`,
      color: 'var(--color-success)',
      bg: 'rgba(16, 185, 129, 0.1)',
      border: 'rgba(16, 185, 129, 0.3)',
      widthPct: 48,
    },
    {
      id: 'recovered',
      label: 'Revenue Recovered',
      count: fmtINR(metrics.total_revenue_recovered),
      value: `${fmtPct(metrics.revenue_recovery_rate)} Total Recovery Rate`,
      subtext: 'Actual Verified Value',
      color: 'var(--color-success)',
      bg: 'rgba(16, 185, 129, 0.18)',
      border: 'rgba(16, 185, 129, 0.5)',
      widthPct: 35,
      isHero: true,
    },
  ]

  return (
    <div className="recovery-funnel card" aria-label="Recovery Conversion Funnel">
      <div className="funnel-header">
        <div>
          <h3 className="funnel-title">Revenue Recovery Funnel</h3>
          <p className="funnel-subtitle">
            Deterministic attrition from risk detection to realized revenue
          </p>
        </div>
        <span className="chip chip--neutral">Verified Pipeline</span>
      </div>

      <div className="funnel-container">
        {steps.map((step, idx) => (
          <div key={step.id} className="funnel-step-wrapper">
            <div
              className={`funnel-step ${step.isHero ? 'funnel-step--hero' : ''}`}
              style={{
                width: `${step.widthPct}%`,
                borderColor: step.border,
                background: step.bg,
              }}
            >
              <div className="funnel-step-left">
                <span className="funnel-step-num">0{idx + 1}</span>
                <span className="funnel-step-label">{step.label}</span>
              </div>
              <div className="funnel-step-center">
                <span className="funnel-step-count" style={{ color: step.color }}>
                  {step.count}
                </span>
                <span className="funnel-step-subtext">{step.subtext}</span>
              </div>
              <div className="funnel-step-right">
                <span className="funnel-step-value">{step.value}</span>
              </div>
            </div>
            {idx < steps.length - 1 && (
              <div className="funnel-connector" aria-hidden="true">
                ↓
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
