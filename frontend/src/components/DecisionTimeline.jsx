/**
 * DecisionTimeline.jsx
 *
 * Deterministic Decision Trace Visualization.
 * Renders the chronological step-by-step evaluation pipeline for a payment:
 * 1. Payment Analysis
 * 2. Eligibility Check
 * 3. Recovery Prediction
 * 4. Revenue Risk
 * 5. Decision
 */

import React from 'react'

const STEP_ICONS = {
  'Payment Analysis': '💳',
  'Eligibility Check': '🛡',
  'Recovery Prediction': '🤖',
  'Revenue Risk': '📊',
  'Decision': '🧠',
}

const STATUS_BADGES = {
  PASS: { label: 'PASS', bg: 'rgba(74, 222, 128, 0.15)', text: '#4ade80', border: 'rgba(74, 222, 128, 0.3)' },
  BLOCKED: { label: 'BLOCKED', bg: 'rgba(239, 68, 68, 0.15)', text: '#ef4444', border: 'rgba(239, 68, 68, 0.3)' },
  COMPLETE: { label: 'COMPLETE', bg: 'rgba(96, 165, 250, 0.15)', text: '#60a5fa', border: 'rgba(96, 165, 250, 0.3)' },
  SKIPPED: { label: 'SKIPPED', bg: 'rgba(156, 163, 175, 0.15)', text: '#9ca3af', border: 'rgba(156, 163, 175, 0.3)' },
  RECOMMENDED: { label: 'RECOMMENDED', bg: 'rgba(74, 222, 128, 0.15)', text: '#4ade80', border: 'rgba(74, 222, 128, 0.3)' },
  OUTREACH: { label: 'OUTREACH', bg: 'rgba(251, 191, 36, 0.15)', text: '#fbbf24', border: 'rgba(251, 191, 36, 0.3)' },
  ESCALATED: { label: 'ESCALATED', bg: 'rgba(251, 146, 60, 0.15)', text: '#fb923c', border: 'rgba(251, 146, 60, 0.3)' },
  DEFERRED: { label: 'DEFERRED', bg: 'rgba(156, 163, 175, 0.15)', text: '#9ca3af', border: 'rgba(156, 163, 175, 0.3)' },
}

export default function DecisionTimeline({ steps }) {
  if (!steps || steps.length === 0) return null

  return (
    <div className="decision-timeline-card" aria-label="Deterministic Decision Trace">
      <div className="timeline-header" style={{ marginBottom: '1.25rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ fontSize: '1.25rem' }}>⏱</span>
          <h4 className="section-title" style={{ fontSize: '1.05rem', margin: 0 }}>
            Deterministic Decision Trace
          </h4>
        </div>
        <p className="section-subtitle" style={{ margin: '0.25rem 0 0' }}>
          Exact deterministic path and rules evaluated by ReviveAI
        </p>
      </div>

      <div className="timeline-steps-flow" style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        {steps.map((step, idx) => {
          const badge = STATUS_BADGES[step.status] || STATUS_BADGES.COMPLETE
          const icon = STEP_ICONS[step.step] || '•'
          const isLast = idx === steps.length - 1

          return (
            <div key={idx} style={{ position: 'relative' }}>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '1rem',
                  background: 'var(--gray-900, #111827)',
                  padding: '1rem',
                  borderRadius: '8px',
                  border: '1px solid var(--gray-800, #1f2937)',
                }}
              >
                {/* Step Number + Icon */}
                <div
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    minWidth: '42px',
                    height: '42px',
                    borderRadius: '8px',
                    background: 'var(--gray-950, #030712)',
                    border: '1px solid var(--gray-700, #374151)',
                    fontSize: '1.2rem',
                  }}
                >
                  {icon}
                </div>

                {/* Content */}
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <span style={{ fontSize: '0.75rem', color: 'var(--gray-400, #9ca3af)', fontWeight: 600 }}>
                        STEP 0{idx + 1}
                      </span>
                      <strong style={{ fontSize: '0.95rem', color: 'var(--text-primary, #f3f4f6)' }}>
                        {step.step}
                      </strong>
                    </div>

                    <span
                      style={{
                        fontSize: '0.7rem',
                        padding: '0.15rem 0.5rem',
                        borderRadius: '4px',
                        fontWeight: 600,
                        background: badge.bg,
                        color: badge.text,
                        border: `1px solid ${badge.border}`,
                      }}
                    >
                      {badge.label}
                    </span>
                  </div>

                  {/* Value */}
                  <div style={{ fontSize: '0.9rem', color: 'var(--blue-400, #60a5fa)', fontWeight: 500, margin: '0.35rem 0 0.2rem' }}>
                    {step.value}
                  </div>

                  {/* Explanation */}
                  <p style={{ margin: 0, fontSize: '0.825rem', color: 'var(--gray-400, #9ca3af)', lineHeight: '1.4' }}>
                    {step.explanation}
                  </p>
                </div>
              </div>

              {/* Connecting Down Arrow */}
              {!isLast && (
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'center',
                    padding: '0.2rem 0',
                    color: 'var(--gray-600, #4b5563)',
                    fontSize: '0.9rem',
                  }}
                >
                  ↓
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
