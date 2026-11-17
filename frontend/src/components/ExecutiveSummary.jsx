/**
 * ExecutiveSummary.jsx — Top-level recovery opportunity summary
 * Phase 4: Primary business metrics at a glance
 */

function formatINR(amount) {
  if (amount == null || amount === 0) return '₹0.00'
  return '₹' + Number(amount).toLocaleString('en-IN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

const ACTION_META = {
  RETRY_PAYMENT:      { icon: '↺', label: 'RETRY PAYMENT',      color: 'var(--color-success)' },
  RETRY_WITH_CAUTION: { icon: '⚠', label: 'RETRY WITH CAUTION', color: 'var(--color-warning)' },
  DO_NOT_RETRY:       { icon: '✕', label: 'DO NOT RETRY',       color: 'var(--color-danger)'  },
  DEFER_RECOVERY:     { icon: '⏳', label: 'DEFER RECOVERY',     color: 'var(--color-text-secondary)' },
  ESCALATE_TO_HUMAN:  { icon: '↑', label: 'ESCALATE TO HUMAN',  color: 'var(--color-brand)'   },
  WAIT_FOR_COOLDOWN:  { icon: '⏸', label: 'WAIT FOR COOLDOWN',  color: 'var(--color-text-secondary)' },
}

const PRIORITY_META = {
  HIGH:   { color: 'var(--color-priority-high)',   bg: 'rgba(244,63,94,0.12)',   border: 'rgba(244,63,94,0.25)'   },
  MEDIUM: { color: 'var(--color-priority-medium)', bg: 'rgba(245,158,11,0.12)',  border: 'rgba(245,158,11,0.25)'  },
  LOW:    { color: 'var(--color-priority-low)',     bg: 'rgba(100,116,139,0.12)', border: 'rgba(100,116,139,0.25)' },
  NONE:   { color: 'var(--color-text-muted)',       bg: 'rgba(51,65,85,0.12)',    border: 'rgba(51,65,85,0.25)'    },
}

export function ExecutiveSummary({ decision }) {
  if (!decision) return null

  const action   = decision.recommended_action || 'UNKNOWN'
  const actionMeta   = ACTION_META[action]   || { icon: '?', label: action, color: 'var(--color-text-muted)' }
  const priority = decision.priority || 'NONE'
  const priorityMeta = PRIORITY_META[priority] || PRIORITY_META.NONE
  const eligible = decision.eligible

  const probability   = decision.recovery_probability ?? null
  const revAtRisk     = decision.revenue_at_risk        ?? null
  const expectedRecov = decision.expected_recovery_value ?? null

  const isBlocked = !eligible

  return (
    <div className="card exec-summary" id="executive-summary" aria-label="Recovery Summary">
      {/* Header */}
      <div className="exec-header">
        <div className="exec-header-left">
          <div className="exec-header-icon" aria-hidden="true">
            {isBlocked ? '🚫' : '🎯'}
          </div>
          <div className="exec-header-text">
            <div className="exec-title">
              {isBlocked ? 'Recovery Blocked' : 'Recovery Opportunity'}
            </div>
            <div className="exec-subtitle">
              {isBlocked
                ? 'This payment is not eligible for automated recovery'
                : 'AI-powered recovery intelligence summary'}
            </div>
          </div>
        </div>
        <div className="exec-header-right">
          {!isBlocked && (
            <span
              className="priority-pill"
              style={{
                color:            priorityMeta.color,
                background:       priorityMeta.bg,
                borderColor:      priorityMeta.border,
              }}
            >
              {priority} PRIORITY
            </span>
          )}
          <span
            className="action-badge"
            style={{
              color:       actionMeta.color,
              background:  isBlocked ? 'rgba(239,68,68,0.08)' : `${actionMeta.color}1A`,
              borderColor: isBlocked ? 'rgba(239,68,68,0.25)' : `${actionMeta.color}40`,
            }}
          >
            {actionMeta.label}
          </span>
        </div>
      </div>

      {/* Metrics */}
      <div className="exec-metrics">
        {/* Primary: Expected Recovery */}
        <div className="exec-metric exec-metric--primary">
          <div className="exec-metric-label">Expected Recovery Value</div>
          <div className="exec-metric-value exec-metric-value--recovery">
            {isBlocked ? '—' : formatINR(expectedRecov)}
          </div>
          <div className="exec-metric-sub">
            {isBlocked ? 'Not eligible for recovery' : 'Probability-weighted recovery'}
          </div>
        </div>

        {/* Revenue at Risk */}
        <div className="exec-metric">
          <div className="exec-metric-label">Revenue at Risk</div>
          <div className="exec-metric-value exec-metric-value--risk">
            {revAtRisk != null ? formatINR(revAtRisk) : '—'}
          </div>
          <div className="exec-metric-sub">Total payment amount</div>
        </div>

        {/* Recovery Probability */}
        <div className="exec-metric">
          <div className="exec-metric-label">Recovery Probability</div>
          <div className="exec-metric-value exec-metric-value--prob">
            {isBlocked || probability == null
              ? 'N/A'
              : `${(probability * 100).toFixed(2)}%`}
          </div>
          <div className="exec-metric-sub">
            {isBlocked ? 'Ineligible — not calculated' : 'Estimated likelihood of success'}
          </div>
        </div>

        {/* Recovery Priority */}
        <div className="exec-metric">
          <div className="exec-metric-label">Recovery Priority</div>
          <div
            className="exec-metric-value"
            style={{ color: isBlocked ? 'var(--color-text-muted)' : priorityMeta.color }}
          >
            {isBlocked ? 'NONE' : priority}
          </div>
          <div className="exec-metric-sub">
            {isBlocked ? 'Blocked by policy' : 'Based on value and probability'}
          </div>
        </div>
      </div>
    </div>
  )
}