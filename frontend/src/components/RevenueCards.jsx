/**
 * RevenueCards.jsx — Revenue Intelligence section
 * Phase 4: Three-card layout with efficiency bar, proper N/A for ineligible
 */

function formatINR(amount) {
  if (amount == null) return '—'
  return '₹' + Number(amount).toLocaleString('en-IN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

export function RevenueCards({ decision }) {
  if (!decision) return null

  const eligible      = decision.eligible
  const revAtRisk     = decision.revenue_at_risk
  const expectedRecov = decision.expected_recovery_value
  const probability   = decision.recovery_probability

  // Display-only efficiency: expected / at-risk (frontend calc only for display)
  const efficiencyPct = (eligible && revAtRisk > 0 && expectedRecov != null)
    ? Math.min(100, Math.round((expectedRecov / revAtRisk) * 100))
    : null

  return (
    <div className="card" aria-label="Revenue Intelligence">
      <div className="card-header">
        <div className="card-icon card-icon--amber" aria-hidden="true">💰</div>
        <span className="card-title">Revenue Intelligence</span>
      </div>

      <div className="revenue-grid">
        {/* Revenue at Risk */}
        <div className="revenue-metric">
          <div className="revenue-metric-label">Revenue at Risk</div>
          <div className="revenue-metric-value revenue-metric-value--risk">
            {formatINR(revAtRisk)}
          </div>
          <div className="revenue-metric-sub">Total payment amount</div>
        </div>

        {/* Expected Recovery */}
        <div className="revenue-metric">
          <div className="revenue-metric-label">Expected Recovery</div>
          <div className="revenue-metric-value revenue-metric-value--recov">
            {eligible && expectedRecov != null ? formatINR(expectedRecov) : '—'}
          </div>
          <div className="revenue-metric-sub">
            {eligible && probability != null
              ? `At ${(probability * 100).toFixed(0)}% probability`
              : 'Not eligible'}
          </div>
        </div>

        {/* Recovery Efficiency (display-only) */}
        <div className="revenue-metric">
          <div className="revenue-metric-label">Recovery Efficiency</div>
          <div className="revenue-metric-value revenue-metric-value--eff">
            {efficiencyPct != null ? `${efficiencyPct}%` : 'N/A'}
          </div>
          <div className="revenue-metric-sub">Expected / at-risk ratio</div>
        </div>
      </div>

      {/* Efficiency bar — display only for eligible payments */}
      {efficiencyPct != null && (
        <div className="eff-bar-wrap">
          <div className="eff-bar-header">
            <span>Recovery Efficiency</span>
            <span>{efficiencyPct}%</span>
          </div>
          <div className="eff-bar-track" role="progressbar" aria-valuenow={efficiencyPct} aria-valuemin={0} aria-valuemax={100}>
            <div
              className="eff-bar-fill"
              style={{ width: `${efficiencyPct}%` }}
            />
          </div>
        </div>
      )}
    </div>
  )
}
