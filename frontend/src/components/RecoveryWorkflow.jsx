/**
 * RecoveryWorkflow.jsx
 *
 * Visual workflow stepper for bounded recovery execution.
 * Shows: Decision → Attempt → Result → Amount Recovered → Final State.
 *
 * Clearly labeled SIMULATION MODE.
 * Disclaimer: "AI recommends. Policy controls. Recovery Orchestrator executes."
 */

import { useState, useEffect } from 'react'
import { executeRecovery, draftReminder, getRecoveryExplanation } from '../api/recovery'
import RecoveryExplanation from './RecoveryExplanation.jsx'
import DecisionTimeline from './DecisionTimeline.jsx'

const STATUS_CONFIG = {
  recovered:  { icon: '✅', label: 'Recovery Successful',  cls: 'status-recovered'  },
  blocked:    { icon: '🚫', label: 'Recovery Blocked',     cls: 'status-blocked'    },
  deferred:   { icon: '⏳', label: 'Recovery Deferred',    cls: 'status-deferred'   },
  escalated:  { icon: '👤', label: 'Escalated to Human',   cls: 'status-escalated'  },
  failed:     { icon: '❌', label: 'Attempt Failed',       cls: 'status-failed'     },
  pending:    { icon: '⏳', label: 'Pending',               cls: 'status-deferred'   },
  outreach_required: { icon: '📧', label: 'Outreach Required', cls: 'status-escalated' },
}

const ACTION_LABELS = {
  RETRY_PAYMENT:       'Retry Payment',
  RETRY_WITH_CAUTION:  'Retry with Caution',
  DEFER_RECOVERY:      'Defer Recovery',
  DO_NOT_RETRY:        'Do Not Retry',
  ESCALATE_TO_HUMAN:   'Escalate to Human',
  WAIT_FOR_COOLDOWN:   'Wait for Cooldown',
  SEND_PAYMENT_REMINDER: 'Send Payment Reminder',
}

const EVENT_ICONS = {
  workflow_started:      '🚀',
  eligibility_verified:  '✔',
  decision_ready:        '🧠',
  recovery_blocked:      '🚫',
  recovery_deferred:     '⏳',
  recovery_escalated:    '👤',
  recovery_outreach_required: '📧',
  attempt_started:       '⚡',
  attempt_succeeded:     '✅',
  attempt_failed:        '❌',
  retry_limit_reached:   '⚠️',
  workflow_stopped:      '⛔',
  workflow_complete:     '🏁',
}

function fmt(amount) {
  return '₹' + Number(amount).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function fmt_pct(v) {
  return (Number(v) * 100).toFixed(1) + '%'
}

export default function RecoveryWorkflow({ paymentId, decision, eligible }) {
  const [loading,  setLoading]  = useState(false)
  const [result,   setResult]   = useState(null)
  const [error,    setError]    = useState(null)
  
  const [drafting, setDrafting] = useState(false)
  const [draft, setDraft]       = useState(null)
  const [draftError, setDraftError] = useState(null)

  // Explainability state
  const [showExplanation, setShowExplanation] = useState(false)
  const [explanationData, setExplanationData] = useState(null)
  const [loadingExplanation, setLoadingExplanation] = useState(false)
  const [explanationError, setExplanationError] = useState(null)

  useEffect(() => {
    // Reset explanation data on paymentId change
    setExplanationData(null)
    setShowExplanation(false)
    setExplanationError(null)
  }, [paymentId])

  async function handleToggleExplanation() {
    const nextState = !showExplanation
    setShowExplanation(nextState)

    if (nextState && !explanationData && !loadingExplanation) {
      setLoadingExplanation(true)
      setExplanationError(null)
      try {
        const data = await getRecoveryExplanation(paymentId)
        setExplanationData(data)
      } catch (err) {
        setExplanationError(err.message || 'Failed to load recovery explanation.')
      } finally {
        setLoadingExplanation(false)
      }
    }
  }

  async function handleExecute() {
    setLoading(true)
    setResult(null)
    setError(null)
    try {
      const data = await executeRecovery(paymentId)
      setResult(data)
    } catch (err) {
      setError(err.message || 'Execution failed')
    } finally {
      setLoading(false)
    }
  }

  const cfg = result ? (STATUS_CONFIG[result.execution?.status] || STATUS_CONFIG.pending) : null

  return (
    <section className="recovery-workflow" aria-labelledby="workflow-heading">
      {/* Header */}
      <div className="workflow-header">
        <div>
          <h2 id="workflow-heading" className="section-title">
            Recovery Workflow
          </h2>
          <p className="section-subtitle">
            Bounded execution governed by deterministic policy guardrails
          </p>
        </div>
        <span className="sim-badge">⚠ SIMULATION MODE</span>
      </div>

      {/* Safety disclaimer */}
      <div className="workflow-disclaimer">
        <span className="disclaimer-icon">🛡</span>
        <div className="disclaimer-text">
          <p className="disclaimer-main">
            <strong>AI investigates and explains. Deterministic policy decides what is allowed. The Recovery Orchestrator executes bounded actions.</strong>
          </p>
          <p className="disclaimer-sub">
            The LLM never directly executes financial transactions. All retries run within strict policy guardrails in simulation mode.
          </p>
        </div>
      </div>

      {/* Pre-execution state */}
      {!result && (
        <div className="workflow-pre">
          {/* Decision summary */}
          <div className="workflow-decision-card">
            <div className="workflow-step">
              <span className="step-icon step-decision">🧠</span>
              <div>
                <p className="step-label">AI + Policy Decision</p>
                <p className="step-value">
                  {ACTION_LABELS[decision?.recommended_action] || decision?.recommended_action || '—'}
                </p>
                <p className="step-sub">Priority: {decision?.priority || 'NONE'}</p>
              </div>
            </div>

            <div className="workflow-arrow">↓</div>

            <div className="workflow-step">
              <span className={`step-icon ${eligible ? 'step-eligible' : 'step-blocked'}`}>
                {eligible ? '✔' : '🚫'}
              </span>
              <div>
                <p className="step-label">Eligibility Check</p>
                <p className="step-value">{eligible ? 'ELIGIBLE' : 'BLOCKED'}</p>
                <p className="step-sub">Deterministic policy enforced</p>
              </div>
            </div>
          </div>

          {/* Execute button */}
          {eligible ? (
            <button
              id="execute-recovery-btn"
              className="btn-execute"
              onClick={handleExecute}
              disabled={loading}
              aria-busy={loading}
            >
              {loading ? (
                <><span className="spinner-sm" aria-hidden="true" />Running Orchestrator…</>
              ) : (
                <><span aria-hidden="true">⚡</span> Execute Bounded Recovery</>
              )}
            </button>
          ) : (
            <div className="workflow-blocked-notice">
              <span>🚫</span>
              <span>Recovery execution blocked — payment is not eligible. No action will be taken.</span>
            </div>
          )}

          {error && (
            <div className="workflow-error" role="alert">
              <span>⚠</span> {error}
            </div>
          )}
        </div>
      )}

      {/* Post-execution result */}
      {result && (
        <div className="workflow-result">
          {/* Status banner */}
          <div className={`workflow-status-banner ${cfg.cls}`}>
            <span className="status-icon-lg">{cfg.icon}</span>
            <div>
              <p className="status-label">{cfg.label}</p>
              <p className="status-sub">Workflow {result.execution?.stopped ? 'stopped' : 'complete'}</p>
            </div>
            {result.execution?.status === 'recovered' && (
              <div className="recovered-amount">
                <p className="recovered-label">Revenue Recovered</p>
                <p className="recovered-value">{fmt(result.execution.amount_recovered)}</p>
              </div>
            )}
          </div>

          {/* Workflow steps */}
          <div className="workflow-steps-row">
            <WorkflowStep icon="🧠" label="Decision" value={ACTION_LABELS[result.action] || result.action} />
            <StepArrow />
            <WorkflowStep
              icon={result.execution?.attempts > 0 ? '⚡' : '🚫'}
              label="Attempts"
              value={String(result.execution?.attempts ?? 0)}
            />
            <StepArrow />
            <WorkflowStep icon={cfg.icon} label="Result" value={cfg.label} />
            {result.execution?.status === 'recovered' && (
              <>
                <StepArrow />
                <WorkflowStep
                  icon="💰"
                  label="Recovered"
                  value={fmt(result.execution.amount_recovered)}
                  highlight
                />
              </>
            )}
          </div>

          {/* Stopping reason */}
          <div className="workflow-stopping-reason">
            <span className="reason-icon">⛔</span>
            <div>
              <p className="reason-label">Stopping Reason</p>
              <p className="reason-text">{result.execution?.stopping_reason}</p>
            </div>
            {result.execution?.escalated && (
              <span className="escalated-badge">👤 Escalated</span>
            )}
          </div>

          {result.execution?.status === 'outreach_required' && (
            <div className="workflow-outreach-section">
              <h3 className="section-title" style={{ marginTop: '1rem', fontSize: '1rem' }}>AI Drafted Reminder</h3>
              <p className="section-subtitle">Use ReviveAI to draft a contextual email reminder.</p>
              
              {!draft && !drafting && (
                <button className="btn-primary" onClick={async () => {
                  setDrafting(true); setDraftError(null);
                  try {
                    const res = await draftReminder(paymentId)
                    setDraft(res.email_draft)
                  } catch (e) {
                    setDraftError(e.message || 'Failed to draft email.')
                  } finally {
                    setDrafting(false)
                  }
                }} style={{ marginTop: '0.5rem' }}>
                  ✎ Draft Email with AI
                </button>
              )}
              {drafting && <p><span className="spinner-sm" /> Drafting email...</p>}
              {draftError && <p className="error-text">{draftError}</p>}
              {draft && (
                <div className="email-draft-box">
                  <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'inherit', margin: 0 }}>{draft}</pre>
                  <button className="btn-execute" style={{ marginTop: '1rem' }} onClick={() => alert('Email sent! (Simulated)')}>
                    📧 Send Reminder (Simulated)
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Reset button */}
          <button
            className="btn-secondary"
            onClick={() => setResult(null)}
          >
            ↩ Reset Workflow
          </button>
        </div>
      )}

      {/* Audit timeline */}
      {result && result.audit_events && result.audit_events.length > 0 && (
        <AuditTimeline events={result.audit_events} workflowId={result.workflow_id} />
      )}

      <div style={{ height: 'var(--space-4, 1rem)' }} />

      {/* Expandable Explainability & Decision Transparency */}
      <div
        className="explanation-toggle-section card"
        style={{
          border: '1px solid var(--gray-800, #1f2937)',
          background: 'var(--gray-900, #111827)',
          padding: '1.25rem',
          borderRadius: 'var(--radius-lg, 12px)',
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            cursor: 'pointer',
            userSelect: 'none',
          }}
          onClick={handleToggleExplanation}
          role="button"
          tabIndex={0}
          onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') handleToggleExplanation() }}
          aria-expanded={showExplanation}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <span style={{ fontSize: '1.25rem' }}>🧠</span>
            <div>
              <h3 style={{ margin: 0, fontSize: '1.05rem', color: 'var(--text-primary, #f3f4f6)', fontWeight: 600 }}>
                WHY DID REVIVEAI MAKE THIS DECISION?
              </h3>
              <p style={{ margin: '0.2rem 0 0', fontSize: '0.825rem', color: 'var(--gray-400, #9ca3af)' }}>
                Inspect deterministic policy factors, calibrated ML prediction, and the 5-step decision trace
              </p>
            </div>
          </div>
          <button
            type="button"
            className="btn-secondary"
            style={{ padding: '0.35rem 0.85rem', fontSize: '0.85rem', pointerEvents: 'none' }}
          >
            {showExplanation ? '▲ Hide Explanation' : '▼ View Explanation'}
          </button>
        </div>

        {showExplanation && (
          <div style={{ marginTop: '1.5rem', borderTop: '1px solid var(--gray-800, #1f2937)', paddingTop: '1.5rem' }}>
            {loadingExplanation && (
              <div style={{ padding: '1.5rem', textAlign: 'center', color: 'var(--gray-400)' }}>
                <span className="spinner-sm" aria-hidden="true" /> Generating deterministic explanation &amp; decision trace…
              </div>
            )}

            {explanationError && (
              <div className="error-banner" role="alert">
                <span>⚠</span> {explanationError}
              </div>
            )}

            {explanationData && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                {/* 1. Structured Explanation */}
                <RecoveryExplanation data={explanationData} />

                {/* 2. Step-by-Step Decision Trace */}
                <DecisionTimeline steps={explanationData.decision_trace} />
              </div>
            )}
          </div>
        )}
      </div>
    </section>
  )
}

function WorkflowStep({ icon, label, value, highlight = false }) {
  return (
    <div className={`wf-step ${highlight ? 'wf-step-highlight' : ''}`}>
      <span className="wf-step-icon">{icon}</span>
      <p className="wf-step-label">{label}</p>
      <p className="wf-step-value">{value}</p>
    </div>
  )
}

function StepArrow() {
  return <span className="wf-arrow" aria-hidden="true">→</span>
}

// ============================================================
// Audit Timeline (inline, used by RecoveryWorkflow)
// ============================================================

function AuditTimeline({ events, workflowId }) {
  return (
    <div className="audit-timeline" aria-label="Workflow Audit Trail">
      <div className="audit-timeline-header">
        <h3 className="audit-title">Audit Trail</h3>
        <span className="audit-workflow-id">Workflow: {workflowId}</span>
      </div>
      <ol className="audit-event-list">
        {events.map((evt, i) => {
          const icon = EVENT_ICONS[evt.event_type] || '•'
          const ts   = evt.timestamp ? new Date(evt.timestamp).toLocaleTimeString() : ''
          return (
            <li key={i} className="audit-event">
              <span className="audit-event-icon" aria-hidden="true">{icon}</span>
              <div className="audit-event-body">
                <p className="audit-event-type">{_humanise(evt.event_type)}</p>
                {ts && <p className="audit-event-time">{ts}</p>}
                {evt.details && Object.keys(evt.details).length > 0 && (
                  <p className="audit-event-details">
                    {Object.entries(evt.details)
                      .map(([k, v]) => `${k}: ${_fmtValue(k, v)}`)
                      .join('  ·  ')}
                  </p>
                )}
              </div>
            </li>
          )
        })}
      </ol>
    </div>
  )
}

function _humanise(str) {
  return str
    .replace(/_/g, ' ')
    .replace(/\b\w/g, c => c.toUpperCase())
}

function _fmtValue(key, value) {
  if (key === 'amount_recovered' || key === 'revenue_at_risk') {
    return fmt(value)
  }
  if (typeof value === 'boolean') return value ? 'yes' : 'no'
  return String(value)
}
