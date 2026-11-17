/**
 * DecisionPanel.jsx — Priority, recommended action, reasons, decision evidence
 * Phase 4: Strong visual hierarchy; BLOCKED state for ineligible payments
 */

function formatINR(amount) {
  if (amount == null) return '—'
  return '₹' + Number(amount).toLocaleString('en-IN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

function titleCase(str) {
  if (!str) return '—'
  return str.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

const ACTION_META = {
  RETRY_PAYMENT:      { label: 'Retry Payment',      icon: '↺', color: 'var(--color-success)' },
  RETRY_WITH_CAUTION: { label: 'Retry with Caution', icon: '⚠', color: 'var(--color-warning)' },
  DO_NOT_RETRY:       { label: 'Do Not Retry',       icon: '✕', color: 'var(--color-danger)'  },
  DEFER_RECOVERY:     { label: 'Defer Recovery',     icon: '⏳', color: 'var(--color-text-secondary)' },
  ESCALATE_TO_HUMAN:  { label: 'Escalate to Human',  icon: '↑', color: 'var(--color-brand)'   },
  WAIT_FOR_COOLDOWN:  { label: 'Wait for Cooldown',  icon: '⏸', color: 'var(--color-text-secondary)' },
}

const PRIORITY_META = {
  HIGH:   { color: 'var(--color-priority-high)',   bg: 'rgba(244,63,94,0.12)',   border: 'rgba(244,63,94,0.25)'   },
  MEDIUM: { color: 'var(--color-priority-medium)', bg: 'rgba(245,158,11,0.12)',  border: 'rgba(245,158,11,0.25)'  },
  LOW:    { color: 'var(--color-priority-low)',     bg: 'rgba(100,116,139,0.12)', border: 'rgba(100,116,139,0.25)' },
  NONE:   { color: 'var(--color-text-muted)',       bg: 'rgba(51,65,85,0.12)',    border: 'rgba(51,65,85,0.25)'    },
}

export function DecisionPanel({ decision, payment }) {
  if (!decision) return null

  const action      = decision.recommended_action || 'UNKNOWN'
  const meta        = ACTION_META[action] || { label: action, icon: '?', color: 'var(--color-text-muted)' }
  const priority    = decision.priority || 'NONE'
  const priorityMeta = PRIORITY_META[priority] || PRIORITY_META.NONE
  const eligible    = decision.eligible

  return (
    <div className="card decision-panel" aria-label="Recovery Decision">
      <div className="card-header">
        <div className="card-icon card-icon--rose" aria-hidden="true">⚡</div>
        <span className="card-title">Recovery Decision</span>
        {!eligible && (
          <span
            style={{
              marginLeft: 'auto',
              fontSize: 10,
              fontWeight: 700,
              padding: '2px 8px',
              background: 'rgba(239,68,68,0.1)',
              color: 'var(--color-danger)',
              border: '1px solid rgba(239,68,68,0.25)',
              borderRadius: 'var(--radius-full)',
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
            }}
          >
            BLOCKED
          </span>
        )}
      </div>

      <div className="decision-flow">
        {/* Priority */}
        {eligible && (
          <>
            <div className="decision-step">
              <div className="decision-step-label">Recovery Priority</div>
              <div
                className="decision-step-value"
                style={{ color: priorityMeta.color }}
              >
                {priority}
              </div>
            </div>
            <div className="decision-arrow" aria-hidden="true">↓</div>
          </>
        )}

        {/* Recommended Action */}
        <div className="decision-step">
          <div className="decision-step-label">Recommended Action</div>
          <div className={`action-display action-display--${action}`} style={{ marginTop: 8 }}>
            <span className="action-icon-large" aria-hidden="true">{meta.icon}</span>
            <span className={`action-name action-name--${action}`}>{meta.label}</span>
          </div>
        </div>

        {/* Reasons */}
        {decision.reasons && decision.reasons.length > 0 && (
          <>
            <div className="decision-arrow" aria-hidden="true">↓</div>
            <div className="decision-step">
              <div className="decision-step-label">Why?</div>
              <ul className="reasons-list" aria-label="Decision reasons">
                {decision.reasons.map((reason, i) => (
                  <li className="reason-item" key={i}>
                    <span className="reason-dot" aria-hidden="true" />
                    <span className="reason-text">{reason}</span>
                  </li>
                ))}
              </ul>
            </div>
          </>
        )}
      </div>

      {/* Decision Evidence */}
      {payment && (
        <div style={{ marginTop: 'var(--space-5)' }}>
          <div className="section-label">Decision Evidence</div>
          <div className="evidence-grid">
            <div className="evidence-item">
              <div className="evidence-label">Failure Type</div>
              <div className="evidence-value">{titleCase(payment.failure_reason)}</div>
            </div>
            <div className="evidence-item">
              <div className="evidence-label">Subscription</div>
              <div className="evidence-value">{titleCase(payment.subscription_status)}</div>
            </div>
            <div className="evidence-item">
              <div className="evidence-label">Retry Count</div>
              <div className="evidence-value">{payment.retry_count ?? '—'}</div>
            </div>
            <div className="evidence-item">
              <div className="evidence-label">Lifetime Value</div>
              <div className="evidence-value">{formatINR(payment.lifetime_value)}</div>
            </div>
            {eligible && decision.recovery_probability != null && (
              <div className="evidence-item">
                <div className="evidence-label">Recovery Probability</div>
                <div className="evidence-value">{(decision.recovery_probability * 100).toFixed(2)}%</div>
              </div>
            )}
            <div className="evidence-item">
              <div className="evidence-label">Revenue at Risk</div>
              <div className="evidence-value">{formatINR(decision.revenue_at_risk)}</div>
            </div>
            {eligible && decision.expected_recovery_value != null && (
              <div className="evidence-item">
                <div className="evidence-label">Expected Recovery</div>
                <div className="evidence-value">{formatINR(decision.expected_recovery_value)}</div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
