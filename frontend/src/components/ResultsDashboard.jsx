/**
 * ResultsDashboard.jsx — Assembled results layout
 * Phase 4: Proper data flow, payment passed to DecisionPanel for evidence
 */
import { EligibilityBadge }   from './EligibilityBadge.jsx'
import { PaymentCard }        from './PaymentCard.jsx'
import { ProbabilityGauge }   from './ProbabilityGauge.jsx'
import { RevenueCards }       from './RevenueCards.jsx'
import { DecisionPanel }      from './DecisionPanel.jsx'
import { AgentSteps }         from './AgentSteps.jsx'
import { ExecutiveSummary }   from './ExecutiveSummary.jsx'

export function ResultsDashboard({ data }) {
  if (!data) return null

  const { payment, eligibility, decision, agent } = data

  // Recovery probability — prefer from decision (authoritative), fall back to prediction
  const probability = decision?.recovery_probability ?? data.prediction?.recovery_probability ?? null
  const eligible    = decision?.eligible ?? eligibility?.eligible ?? null

  return (
    <div id="results-dashboard" aria-label="Recovery Analysis Results">

      {/* Executive Summary — top priority */}
      <ExecutiveSummary decision={decision} />

      <div style={{ height: 'var(--space-5)' }} />

      {/* Row 1 — Payment info + Eligibility + Probability gauge */}
      <div className="grid-2col">
        <PaymentCard payment={payment} />

        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-5)' }}>
          {/* Eligibility */}
          <div className="card" aria-label="Recovery Eligibility">
            <div className="card-header">
              <div className="card-icon card-icon--green" aria-hidden="true">🛡</div>
              <span className="card-title">Recovery Eligibility</span>
            </div>
            <EligibilityBadge eligibility={eligibility} />
          </div>

          {/* Probability Gauge */}
          <ProbabilityGauge probability={probability} eligible={eligible} />
        </div>
      </div>

      <div style={{ height: 'var(--space-5)' }} />

      {/* Row 2 — Revenue Intelligence + Decision Panel */}
      <div className="grid-2col">
        <RevenueCards decision={decision} />
        <DecisionPanel decision={decision} payment={payment} />
      </div>

      <div style={{ height: 'var(--space-5)' }} />

      {/* Row 3 — AI Agent Activity (full width) */}
      <AgentSteps agent={agent} />

    </div>
  )
}
