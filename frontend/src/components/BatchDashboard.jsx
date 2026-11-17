/**
 * BatchDashboard.jsx
 *
 * Batch recovery execution dashboard.
 * Processes the 9-payment demo batch through the full deterministic pipeline.
 * Features:
 *  - Revenue Command Center (Total Revenue Recovered, Value Bar, KPIs)
 *  - Recovery Conversion Funnel
 *  - Detailed Per-Payment Audit Table
 */

import React, { useState } from 'react'
import { runBatchRecovery, getRecoveryExplanation } from '../api/recovery'
import RevenueCommandCenter from './RevenueCommandCenter.jsx'
import RecoveryFunnel from './RecoveryFunnel.jsx'
import RecoveryExplanation from './RecoveryExplanation.jsx'
import DecisionTimeline from './DecisionTimeline.jsx'

const DEMO_BATCH_IDS = [
  'pay_002610',  // eligible → temp failure → recovered (₹28,100.45)
  'pay_000041',  // eligible → temp failure → recovered (₹4,274.20)
  'pay_000039',  // eligible → network error → recovered (₹2,580.63)
  'pay_000012',  // eligible → insufficient funds → failed (₹0.00)
  'pay_000016',  // blocked → payment_method_issue
  'pay_000049',  // blocked → repeated_failure
  'pay_000116',  // blocked → unknown_failure
  'pay_000040',  // blocked → halted subscription
  'pay_000062',  // blocked → retry limit exceeded
]

function fmtINR(amount) {
  return '₹' + Number(amount || 0).toLocaleString('en-IN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

function fmtPct(v) {
  return (Number(v || 0) * 100).toFixed(1) + '%'
}

const STATUS_ICONS = {
  recovered:  { icon: '✅', label: 'Recovered', cls: 'item-recovered' },
  blocked:    { icon: '🚫', label: 'Blocked',   cls: 'item-blocked'   },
  deferred:   { icon: '⏳', label: 'Deferred',  cls: 'item-deferred'  },
  escalated:  { icon: '👤', label: 'Escalated', cls: 'item-escalated' },
  failed:     { icon: '❌', label: 'Failed',    cls: 'item-failed'    },
  not_found:  { icon: '🔍', label: 'Not Found', cls: 'item-notfound'  },
  error:      { icon: '⚠️', label: 'Error',     cls: 'item-error'     },
}

export default function BatchDashboard() {
  const [loading, setLoading] = useState(false)
  const [result,  setResult]  = useState(null)
  const [error,   setError]   = useState(null)

  // Explainability state for batch items
  const [selectedExplainId, setSelectedExplainId] = useState(null)
  const [explainData, setExplainData] = useState(null)
  const [loadingExplain, setLoadingExplain] = useState(false)
  const [explainError, setExplainError] = useState(null)

  async function handleExplain(paymentId) {
    setSelectedExplainId(paymentId)
    setExplainData(null)
    setExplainError(null)
    setLoadingExplain(true)
    try {
      const data = await getRecoveryExplanation(paymentId)
      setExplainData(data)
    } catch (err) {
      setExplainError(err.message || 'Failed to retrieve explanation.')
    } finally {
      setLoadingExplain(false)
    }
  }

  function handleCloseExplain() {
    setSelectedExplainId(null)
    setExplainData(null)
    setExplainError(null)
  }

  async function handleBatch() {
    setLoading(true)
    setResult(null)
    setError(null)
    try {
      const data = await runBatchRecovery(DEMO_BATCH_IDS)
      setResult(data)
    } catch (err) {
      setError(err.message || 'Batch processing failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="batch-dashboard" aria-labelledby="batch-heading">
      {/* Header */}
      <div className="batch-header">
        <div>
          <h2 id="batch-heading" className="section-title">Batch Revenue Recovery Intelligence</h2>
          <p className="section-subtitle">
            Execute bounded simulated recovery across {DEMO_BATCH_IDS.length} benchmark payments
          </p>
        </div>
        <span className="sim-badge">⚠ SIMULATION MODE</span>
      </div>

      {/* Control Bar */}
      <div className="batch-actions-bar">
        <button
          id="run-batch-btn"
          className="btn-execute"
          onClick={handleBatch}
          disabled={loading}
          aria-busy={loading}
        >
          {loading ? (
            <>
              <span className="spinner-sm" aria-hidden="true" />
              Executing Bounded Batch Pipeline…
            </>
          ) : (
            <>
              <span aria-hidden="true">⚡</span>
              Run Demo Batch ({DEMO_BATCH_IDS.length} payments)
            </>
          )}
        </button>
        <span className="text-muted text-sm" style={{ alignSelf: 'center' }}>
          Executes deterministic policy &amp; simulation gateway for all 9 scenarios
        </span>
      </div>

      {error && (
        <div className="workflow-error" role="alert">
          <span>⚠</span> {error}
        </div>
      )}

      {result && (
        <div className="batch-results-container" style={{ marginTop: 'var(--space-6)' }}>
          {/* 1. Executive Command Center (Hero KPIs + Value Comparison) */}
          <RevenueCommandCenter metrics={result.metrics} />

          <div style={{ height: 'var(--space-6)' }} />

          {/* 2. Recovery Conversion Funnel */}
          <RecoveryFunnel metrics={result.metrics} />

          <div style={{ height: 'var(--space-6)' }} />

          {/* 3. Detailed Batch Breakdown Table */}
          <div className="batch-table-container card">
            <div className="batch-table-header">
              <div>
                <h3 className="batch-table-heading">Deterministic Batch Outcomes</h3>
                <p className="section-subtitle">
                  Per-payment trace of eligibility, prediction, execution status, and recovered amount
                </p>
              </div>
              <span className="chip chip--neutral">{result.items.length} Records</span>
            </div>

            <table className="batch-table" aria-label="Batch payment results">
              <thead>
                <tr>
                  <th>Rank / ID</th>
                  <th>Eligibility</th>
                  <th>Recovery Prob.</th>
                  <th>Revenue at Risk</th>
                  <th>Execution Status</th>
                  <th>Amount Recovered</th>
                  <th>Explainability</th>
                </tr>
              </thead>
              <tbody>
                {result.items.map((item, idx) => {
                  const cfg = STATUS_ICONS[item.execution_status] || STATUS_ICONS.error
                  return (
                    <tr key={item.payment_id} className={cfg.cls}>
                      <td className="payment-id-cell">
                        <span className="row-index">0{idx + 1}</span>
                        <code>{item.payment_id}</code>
                      </td>
                      <td>
                        {item.eligible ? (
                          <span className="yes-pill">Eligible</span>
                        ) : (
                          <span className="no-pill">Blocked</span>
                        )}
                      </td>
                      <td>
                        {item.recovery_probability != null
                          ? fmtPct(item.recovery_probability)
                          : '—'}
                      </td>
                      <td className="risk-amount-cell">{fmtINR(item.revenue_at_risk)}</td>
                      <td>
                        <span className="exec-status">
                          <span aria-hidden="true">{cfg.icon}</span> {cfg.label}
                        </span>
                      </td>
                      <td
                        className={
                          item.amount_recovered > 0
                            ? 'amount-recovered-cell'
                            : 'amount-zero-cell'
                        }
                      >
                        {item.amount_recovered > 0 ? fmtINR(item.amount_recovered) : '—'}
                      </td>
                      <td>
                        <button
                          type="button"
                          className="btn-secondary"
                          style={{ padding: '0.25rem 0.65rem', fontSize: '0.8rem' }}
                          onClick={() => handleExplain(item.payment_id)}
                          aria-label={`Explain recovery decision for ${item.payment_id}`}
                        >
                          🔍 Explain
                        </button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* On-Demand Explanation Modal / Drawer */}
      {selectedExplainId && (
        <div
          className="modal-backdrop"
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.75)',
            backdropFilter: 'blur(4px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: '1.5rem',
          }}
          onClick={handleCloseExplain}
        >
          <div
            className="modal-card"
            style={{
              background: 'var(--gray-950, #030712)',
              border: '1px solid var(--gray-800, #1f2937)',
              borderRadius: 'var(--radius-lg, 12px)',
              width: '100%',
              maxWidth: '920px',
              maxHeight: '90vh',
              overflowY: 'auto',
              padding: '1.75rem',
              boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.7)',
            }}
            onClick={e => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-labelledby="explain-modal-title"
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', borderBottom: '1px solid var(--gray-800, #1f2937)', paddingBottom: '0.75rem' }}>
              <div>
                <h3 id="explain-modal-title" style={{ margin: 0, fontSize: '1.2rem', color: 'var(--text-primary, #f3f4f6)' }}>
                  Decision Transparency · <code>{selectedExplainId}</code>
                </h3>
                <span className="text-muted text-sm">Deterministic Policy &amp; Calibrated ML Breakdown</span>
              </div>
              <button
                type="button"
                className="btn-secondary"
                style={{ padding: '0.35rem 0.75rem', fontSize: '0.9rem' }}
                onClick={handleCloseExplain}
              >
                ✕ Close
              </button>
            </div>

            {loadingExplain && (
              <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--gray-400)' }}>
                <span className="spinner-sm" aria-hidden="true" /> Loading deterministic explanation…
              </div>
            )}

            {explainError && (
              <div className="error-banner" role="alert">
                <span>⚠</span> {explainError}
              </div>
            )}

            {explainData && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                <RecoveryExplanation data={explainData} />
                <DecisionTimeline steps={explainData.decision_trace} />
              </div>
            )}
          </div>
        </div>
      )}
    </section>
  )
}
