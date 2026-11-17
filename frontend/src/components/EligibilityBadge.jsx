/**
 * EligibilityBadge.jsx — Recovery eligibility indicator
 * Phase 4: Clear blocked vs eligible states
 */

function reasonLabel(reason) {
  const map = {
    payment_not_failed:       'Payment did not fail — not eligible for recovery',
    permanent_failure:        'Permanent failure reason — recovery not possible',
    payment_method_issue:     'Payment method issue — recovery not attempted',
    repeated_failure:         'Repeated failure — recovery attempts exhausted',
    unknown_failure:          'Unknown failure type — recovery not supported',
    halted_subscription:      'Subscription is halted — recovery requires manual review',
    retry_limit_exceeded:     'Maximum retry limit exceeded',
    amount_exceeds_limit:     'Payment amount exceeds automated recovery limit',
    insufficient_funds:       null, // eligible
    temporary_bank_failure:   null, // eligible
    network_error:            null, // eligible
  }
  if (reason && reason in map && map[reason]) return map[reason]
  if (reason) return reason.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
  return null
}

export function EligibilityBadge({ eligibility }) {
  if (!eligibility) return null

  const eligible = eligibility.eligible
  const rawReason = eligibility.reason || ''
  const label = reasonLabel(rawReason)

  if (eligible) {
    return (
      <div className="eligibility-result eligibility-result--eligible">
        <div className="eligibility-icon" aria-hidden="true">✓</div>
        <div>
          <div className="eligibility-status">Eligible for Recovery</div>
          <div className="eligibility-reason">Meets all deterministic policy requirements</div>
        </div>
      </div>
    )
  }

  return (
    <div>
      <div className="eligibility-result eligibility-result--blocked">
        <div className="eligibility-icon" aria-hidden="true">✕</div>
        <div>
          <div className="eligibility-status">Recovery Blocked</div>
          {label && <div className="eligibility-reason">{label}</div>}
        </div>
      </div>
      <div className="recovery-blocked-card">
        <div className="blocked-icon" aria-hidden="true">🚫</div>
        <div>
          <div className="blocked-title">Do Not Retry</div>
          <div className="blocked-reason">
            {label || 'This payment does not meet recovery eligibility criteria.'}
          </div>
        </div>
      </div>
    </div>
  )
}
