/**
 * RecoveryExplanation.jsx
 *
 * Explainable Recovery Intelligence & Decision Transparency UI.
 * Consumes the structured output from POST /api/v1/recovery/explain.
 *
 * Sections:
 * 1. Intelligence Summary (Confidence, Probability, Action, Priority, EV)
 * 2. Why This Decision? (Deterministic Factors, Policy Guardrails, Summary)
 */

import React from 'react'

function fmtINR(amount) {
  return '₹' + Number(amount || 0).toLocaleString('en-IN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

function fmtPct(v) {
  if (v == null) return 'N/A'
  return (Number(v) * 100).toFixed(1) + '%'
}

export default function RecoveryExplanation({ data }) {
  if (!data || !data.explainability) return null

  const {
    eligibility_explanation: elig,
    prediction_explanation: pred,
    decision_explanation: dec,
    financial_impact: fin,
  } = data.explainability

  const isEligible = elig.eligible
  const confidence = pred.confidence_level || 'NOT_APPLICABLE'

  const confColors = {
    HIGH: 'var(--green-400, #4ade80)',
    MEDIUM: 'var(--amber-400, #fbbf24)',
    LOW: 'var(--red-400, #f87171)',
    NOT_APPLICABLE: 'var(--gray-400, #9ca3af)',
  }

  return (
    <div className="recovery-explanation-card" aria-label="Explainable Recovery Intelligence">
      {/* Header */}
      <div className="explanation-header" style={{ marginBottom: '1.25rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ fontSize: '1.25rem' }}>🔍</span>
          <h3 className="section-title" style={{ fontSize: '1.15rem', margin: 0 }}>
            Explainable Recovery Intelligence
          </h3>
        </div>
        <p className="section-subtitle" style={{ margin: '0.25rem 0 0' }}>
          Transparent, deterministic explanation of eligibility, ML prediction, and decision rationale
        </p>
      </div>

      {/* Section 1: Recovery Intelligence KPI Grid */}
      <div
        className="explanation-kpi-grid"
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
          gap: '0.75rem',
          marginBottom: '1.5rem',
        }}
      >
        <div className="kpi-box" style={{ background: 'var(--gray-900, #111827)', padding: '0.85rem', borderRadius: '8px', border: '1px solid var(--gray-800, #1f2937)' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--gray-400, #9ca3af)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Recovery Probability
          </div>
          <div style={{ fontSize: '1.25rem', fontWeight: 'bold', color: 'var(--text-primary, #f3f4f6)', marginTop: '0.25rem' }}>
            {isEligible && pred.recovery_probability != null ? fmtPct(pred.recovery_probability) : 'Blocked'}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--gray-400, #9ca3af)', marginTop: '0.15rem' }}>
            Calibrated ML Model
          </div>
        </div>

        <div className="kpi-box" style={{ background: 'var(--gray-900, #111827)', padding: '0.85rem', borderRadius: '8px', border: '1px solid var(--gray-800, #1f2937)' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--gray-400, #9ca3af)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Confidence
          </div>
          <div style={{ fontSize: '1.25rem', fontWeight: 'bold', color: confColors[confidence] || 'inherit', marginTop: '0.25rem' }}>
            {confidence}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--gray-400, #9ca3af)', marginTop: '0.15rem' }}>
            Deterministic Band
          </div>
        </div>

        <div className="kpi-box" style={{ background: 'var(--gray-900, #111827)', padding: '0.85rem', borderRadius: '8px', border: '1px solid var(--gray-800, #1f2937)' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--gray-400, #9ca3af)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Recommended Action
          </div>
          <div style={{ fontSize: '1.05rem', fontWeight: 'bold', color: 'var(--blue-400, #60a5fa)', marginTop: '0.25rem', textTransform: 'capitalize' }}>
            {dec.recommended_action ? dec.recommended_action.replace(/_/g, ' ') : '—'}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--gray-400, #9ca3af)', marginTop: '0.15rem' }}>
            Policy Engine Output
          </div>
        </div>

        <div className="kpi-box" style={{ background: 'var(--gray-900, #111827)', padding: '0.85rem', borderRadius: '8px', border: '1px solid var(--gray-800, #1f2937)' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--gray-400, #9ca3af)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Priority
          </div>
          <div style={{ fontSize: '1.25rem', fontWeight: 'bold', color: dec.priority === 'HIGH' ? 'var(--orange-400, #fb923c)' : 'var(--text-primary, #f3f4f6)', marginTop: '0.25rem' }}>
            {dec.priority || 'NONE'}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--gray-400, #9ca3af)', marginTop: '0.15rem' }}>
            Opportunity Tier
          </div>
        </div>

        <div className="kpi-box" style={{ background: 'var(--gray-900, #111827)', padding: '0.85rem', borderRadius: '8px', border: '1px solid var(--gray-800, #1f2937)' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--gray-400, #9ca3af)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Revenue at Risk
          </div>
          <div style={{ fontSize: '1.25rem', fontWeight: 'bold', color: 'var(--text-primary, #f3f4f6)', marginTop: '0.25rem' }}>
            {fmtINR(fin.revenue_at_risk)}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--gray-400, #9ca3af)', marginTop: '0.15rem' }}>
            Gross Failure Value
          </div>
        </div>

        <div className="kpi-box" style={{ background: 'var(--gray-900, #111827)', padding: '0.85rem', borderRadius: '8px', border: '1px solid var(--gray-800, #1f2937)' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--gray-400, #9ca3af)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Expected Recovery
          </div>
          <div style={{ fontSize: '1.25rem', fontWeight: 'bold', color: isEligible ? 'var(--green-400, #4ade80)' : 'var(--gray-500, #6b7280)', marginTop: '0.25rem' }}>
            {fmtINR(fin.expected_recovery_value)}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--gray-400, #9ca3af)', marginTop: '0.15rem' }}>
            Probabilistic Value
          </div>
        </div>
      </div>

      {/* Section 2: Why This Decision? & Factors */}
      <div
        className="explanation-details-card"
        style={{
          background: 'var(--gray-950, #030712)',
          padding: '1.25rem',
          borderRadius: '8px',
          border: '1px solid var(--gray-800, #1f2937)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.5rem' }}>
          <h4 style={{ margin: 0, fontSize: '1rem', color: 'var(--text-primary, #f3f4f6)' }}>
            Why Did ReviveAI Make This Decision?
          </h4>
          <span
            style={{
              fontSize: '0.75rem',
              padding: '0.2rem 0.6rem',
              borderRadius: '9999px',
              fontWeight: 600,
              background: isEligible ? 'rgba(74, 222, 128, 0.15)' : 'rgba(239, 68, 68, 0.15)',
              color: isEligible ? '#4ade80' : '#ef4444',
              border: isEligible ? '1px solid rgba(74, 222, 128, 0.3)' : '1px solid rgba(239, 68, 68, 0.3)',
            }}
          >
            {isEligible ? '✓ Recovery Eligible' : '🚫 Recovery Blocked'}
          </span>
        </div>

        {/* Narrative Summaries */}
        <div style={{ marginBottom: '1rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <p style={{ margin: 0, fontSize: '0.9rem', color: 'var(--gray-300, #d1d5db)', lineHeight: '1.45' }}>
            <strong>Decision Summary:</strong> {dec.summary}
          </p>
          <p style={{ margin: 0, fontSize: '0.9rem', color: 'var(--gray-400, #9ca3af)', lineHeight: '1.45' }}>
            <strong>Eligibility Policy:</strong> {elig.summary}
          </p>
          <p style={{ margin: 0, fontSize: '0.9rem', color: 'var(--gray-400, #9ca3af)', lineHeight: '1.45' }}>
            <strong>ML Interpretation:</strong> {pred.summary}
          </p>
        </div>

        {/* Deterministic Factor Cards */}
        {elig.factors && elig.factors.length > 0 && (
          <div style={{ marginTop: '1.25rem' }}>
            <div style={{ fontSize: '0.8rem', color: 'var(--gray-400, #9ca3af)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.75rem' }}>
              Deterministic Evaluation Factors
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '0.75rem' }}>
              {elig.factors.map((f, i) => {
                const isPos = f.impact === 'positive'
                const isNeg = f.impact === 'negative'
                return (
                  <div
                    key={i}
                    style={{
                      background: 'var(--gray-900, #111827)',
                      padding: '0.75rem 1rem',
                      borderRadius: '6px',
                      borderLeft: isPos
                        ? '3px solid #4ade80'
                        : isNeg
                        ? '3px solid #ef4444'
                        : '3px solid #60a5fa',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                      <span style={{ fontSize: '0.9rem' }}>{isPos ? '✓' : isNeg ? '🚫' : 'ℹ'}</span>
                      <strong style={{ fontSize: '0.85rem', color: 'var(--text-primary, #f3f4f6)' }}>
                        {f.factor}
                      </strong>
                    </div>
                    <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--gray-400, #9ca3af)', lineHeight: '1.4' }}>
                      {f.explanation}
                    </p>
                  </div>
                )
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
