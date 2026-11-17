/**
 * App.jsx — ReviveAI Phase 7 Dashboard
 *
 * Product: AI-powered payment recovery intelligence + execution system
 * Architecture: deterministic eligibility + ML prediction + AI agent + bounded execution
 */
import { useState } from 'react'
import './index.css'
import { analyzeRecovery }    from './api/recovery.js'
import { SearchForm }         from './components/SearchForm.jsx'
import { ResultsDashboard }   from './components/ResultsDashboard.jsx'
import RecoveryWorkflow       from './components/RecoveryWorkflow.jsx'
import BatchDashboard         from './components/BatchDashboard.jsx'
import EscalationHub          from './components/EscalationHub.jsx'

// ============================================================
// Loading State
// ============================================================
function LoadingState() {
  const steps = [
    'Retrieving payment record…',
    'Evaluating recovery eligibility…',
    'Running recovery probability model…',
    'Calculating revenue at risk…',
    'Generating AI recovery explanation…',
  ]

  return (
    <div className="loading-container" role="status" aria-live="polite" aria-label="Analyzing payment">
      <div className="loading-header">
        <div className="loading-spinner" aria-hidden="true" />
        <div>
          <div className="loading-title">Analyzing Payment</div>
          <div className="loading-subtitle">Please wait</div>
        </div>
      </div>
      <div className="loading-steps" aria-label="Analysis steps">
        {steps.map((step, i) => (
          <div className="loading-step" key={i} aria-hidden="true">
            <div className="loading-step-icon loading-step-icon--active">
              {i + 1}
            </div>
            {step}
          </div>
        ))}
      </div>
    </div>
  )
}

// ============================================================
// Error State
// ============================================================
function ErrorState({ error }) {
  const is404 = error?.status === 404

  return (
    <div
      className={`error-banner ${is404 ? 'error-banner--404' : ''}`}
      role="alert"
      aria-live="assertive"
    >
      <div className="error-icon-wrap" aria-hidden="true">
        {is404 ? '🔎' : '⚠'}
      </div>
      <div>
        <div className="error-title">
          {is404 ? 'Payment Not Found' : 'Analysis Failed'}
        </div>
        <div className="error-message">
          {is404
            ? 'This payment ID was not found in the recovery dataset. Verify the payment ID and try again.'
            : (error?.message || 'An unexpected error occurred. Please try again.')}
        </div>
      </div>
    </div>
  )
}

// ============================================================
// Empty State
// ============================================================
function EmptyState() {
  return (
    <div className="empty-state" aria-label="Recovery Intelligence — ready to analyze">
      <div className="empty-icon-wrap" aria-hidden="true">📊</div>
      <div className="empty-title">Single Payment Recovery Intelligence</div>
      <div className="empty-body">
        Enter a failed payment ID to analyze its recovery potential.
        ReviveAI assesses eligibility, predicts recovery probability, quantifies revenue
        at risk, and uses an AI agent to explain the recovery recommendation.
      </div>
      <div className="empty-examples">
        <div className="empty-examples-label">Example Payment IDs</div>
        <code className="example-id" title="Eligible for recovery">pay_002610</code>
        <code className="example-id" title="Ineligible — payment method issue">pay_000016</code>
        <code className="example-id" title="Ineligible — halted subscription">pay_000040</code>
      </div>
    </div>
  )
}

// ============================================================
// How ReviveAI Works
// ============================================================
function HowItWorks() {
  return (
    <div className="how-it-works" aria-label="How ReviveAI works">
      <div className="how-it-works-title">How ReviveAI Works</div>
      <div className="how-flow">
        {/* Deterministic Layer */}
        <div className="how-layer how-layer--deterministic">
          <div className="how-layer-title">Deterministic Policy Layer</div>
          <div className="how-step">
            <div className="how-step-num">1</div>
            Eligibility Guardrails — rule-based filter
          </div>
          <div className="how-step">
            <div className="how-step-num">2</div>
            ML Recovery Prediction — calibrated probability estimate
          </div>
          <div className="how-step">
            <div className="how-step-num">3</div>
            Revenue Risk Engine — at-risk &amp; expected value
          </div>
          <div className="how-step">
            <div className="how-step-num">4</div>
            Decision Engine — priority and recommended action
          </div>
        </div>

        {/* Divider */}
        <div className="how-flow-divider">
          <div className="how-flow-divider-line" />
          <div className="how-flow-divider-text">+</div>
          <div className="how-flow-divider-line" />
        </div>

        {/* AI Layer */}
        <div className="how-layer how-layer--ai">
          <div className="how-layer-title">AI Investigation Agent</div>
          <div className="how-step">
            <div className="how-step-num">A</div>
            Autonomous tool selection from registered tools
          </div>
          <div className="how-step">
            <div className="how-step-num">B</div>
            Evidence gathering via controlled ToolExecutor
          </div>
          <div className="how-step">
            <div className="how-step-num">C</div>
            Reasoning over verified tool outputs
          </div>
          <div className="how-step">
            <div className="how-step-num">D</div>
            Operational narrative explanation
          </div>
        </div>
      </div>
      <div className="how-note">
        <strong>The LLM does not control financial eligibility or execute payments.</strong>
        <br />
        Deterministic guardrails enforce all financial safety. The AI agent investigates, diagnoses, and explains.
      </div>
    </div>
  )
}

// ============================================================
// Footer
// ============================================================
function Footer() {
  return (
    <footer className="footer">
      <div className="footer-inner">
        <div className="footer-text">
          ReviveAI · Razorpay Buildathon Track 03 — AI Revenue Recovery
        </div>
        <div className="footer-notice">
          ReviveAI identifies failed payments worth recovering and recommends bounded recovery actions.
          All decisions are governed by deterministic eligibility policy.
        </div>
      </div>
    </footer>
  )
}

// ============================================================
// App Root
// ============================================================
export default function App() {
  const [loading, setLoading] = useState(false)
  const [result,  setResult]  = useState(null)
  const [error,   setError]   = useState(null)
  const [lastId,  setLastId]  = useState(null)

  async function handleAnalyze(paymentId) {
    setLoading(true)
    setError(null)
    setResult(null)
    setLastId(paymentId)

    try {
      const data = await analyzeRecovery(paymentId)
      setResult(data)
    } catch (err) {
      setError(err)
    } finally {
      setLoading(false)
    }
  }

  const showResults = !loading && !error && result

  return (
    <div className="app">

      {/* ── Header ── */}
      <header className="header">
        <div className="header-inner">
          <div className="logo">
            <div className="logo-icon-wrap" aria-hidden="true">⚡</div>
            <span className="logo-name">Revive<span>AI</span></span>
            <span className="logo-badge">Beta</span>
          </div>

          <div className="header-right">
            <span className="header-tagline">
              AI-powered Payment Recovery Intelligence
            </span>

            {/* System Status */}
            <div className="system-status" aria-label="System status">
              <span className="status-dot" aria-hidden="true" />
              Operational
            </div>
          </div>
        </div>
      </header>

      {/* ── Main ── */}
      <main className="main-content" id="main-content">

        {/* Hero + Search */}
        <section className="hero" aria-labelledby="hero-title">
          <div className="hero-eyebrow">
            Payment Recovery Intelligence
          </div>
          <h1 className="hero-title" id="hero-title">
            Identify Revenue Worth <em>Recovering</em>
          </h1>
          <p className="hero-subtitle">
            Analyze failed payments. Get recovery eligibility, ML-predicted
            recovery probability, revenue at risk, and a recommended action —
            explained by an AI agent using verified data.
          </p>
          <SearchForm onSubmit={handleAnalyze} loading={loading} />
        </section>

        {/* Loading */}
        {loading && <LoadingState />}

        {/* Error */}
        {!loading && error && <ErrorState error={error} />}

        {/* Empty */}
        {!loading && !error && !result && <EmptyState />}

        {/* Results */}
        {showResults && (
          <section aria-label={`Analysis results for ${lastId}`}>
            <div className="results-context">
              <div className="results-context-left">
                <span className="results-context-label">Results for</span>
                <code className="results-context-id">{lastId}</code>
              </div>
              <div className="results-context-right">
                {result?.decision?.eligible
                  ? '✓ Recovery Eligible'
                  : result?.decision
                    ? '✕ Recovery Blocked'
                    : ''}
              </div>
            </div>
            <ResultsDashboard data={result} />

            {/* Recovery Workflow — bounded execution */}
            <RecoveryWorkflow
              paymentId={lastId}
              decision={result?.decision}
              eligible={!!result?.decision?.eligible}
            />
          </section>
        )}



        <div style={{ height: 'var(--space-6)' }} />

        {/* Batch Recovery Dashboard (includes Command Center + Funnel) */}
        <BatchDashboard />

        <div style={{ height: 'var(--space-6)' }} />

        {/* Escalation Hub */}
        <EscalationHub />

        <div style={{ height: 'var(--space-6)' }} />

        {/* How It Works — Architecture transparency */}
        <HowItWorks />

      </main>

      {/* ── Footer ── */}
      <Footer />

    </div>
  )
}