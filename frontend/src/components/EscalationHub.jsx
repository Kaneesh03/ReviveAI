import { useState, useEffect } from 'react'
import { getEscalatedCases, draftReminder } from '../api/recovery'

function fmt(amount) {
  return '₹' + Number(amount).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

export default function EscalationHub() {
  const [cases, setCases] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  
  const [selectedCase, setSelectedCase] = useState(null)
  const [drafting, setDrafting] = useState(false)
  const [draft, setDraft] = useState(null)
  const [draftError, setDraftError] = useState(null)

  useEffect(() => {
    fetchCases()
  }, [])

  async function fetchCases() {
    setLoading(true)
    setError(null)
    try {
      const data = await getEscalatedCases()
      setCases(data.cases || [])
    } catch (err) {
      setError(err.message || 'Failed to load escalated cases.')
    } finally {
      setLoading(false)
    }
  }

  async function handleDraftReminder(paymentId) {
    setDrafting(true)
    setDraftError(null)
    setDraft(null)
    try {
      const res = await draftReminder(paymentId)
      setDraft(res.email_draft)
    } catch (err) {
      setDraftError(err.message || 'Failed to draft email.')
    } finally {
      setDrafting(false)
    }
  }

  function handleSelectCase(c) {
    setSelectedCase(c)
    setDraft(null)
    setDraftError(null)
  }

  return (
    <section className="escalation-hub" aria-labelledby="escalation-heading">
      <div className="escalation-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h2 id="escalation-heading" className="section-title">
            Escalation Hub
          </h2>
          <p className="section-subtitle">
            Review cases requiring human intervention or customer outreach.
          </p>
        </div>
        <button className="btn-secondary" onClick={fetchCases} disabled={loading}>
          {loading ? 'Refreshing...' : 'Refresh List'}
        </button>
      </div>

      {error && <div className="error-banner" role="alert" style={{ marginTop: '1rem' }}>⚠ {error}</div>}

      <div className="escalation-layout" style={{ display: 'flex', gap: '2rem', marginTop: '1.5rem' }}>
        {/* Left column: List of cases */}
        <div className="escalation-list" style={{ flex: '1 1 40%', background: 'var(--gray-900)', borderRadius: 'var(--radius-lg)', border: '1px solid var(--gray-800)', overflow: 'hidden' }}>
          {cases.length === 0 && !loading && !error && (
            <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--gray-400)' }}>
              No escalated cases found. Run a batch with failing payments to see escalations here.
            </div>
          )}
          
          <ul style={{ listStyle: 'none', padding: 0, margin: 0, maxHeight: '600px', overflowY: 'auto' }}>
            {cases.map(c => (
              <li 
                key={c.workflow_id} 
                onClick={() => handleSelectCase(c)}
                style={{
                  padding: '1rem', 
                  borderBottom: '1px solid var(--gray-800)',
                  cursor: 'pointer',
                  background: selectedCase?.workflow_id === c.workflow_id ? 'var(--gray-800)' : 'transparent',
                  transition: 'background 0.2s'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <strong>{c.payment_id}</strong>
                  <span style={{ color: 'var(--text-primary)' }}>{fmt(c.amount)}</span>
                </div>
                <div style={{ fontSize: '0.85rem', color: 'var(--gray-400)', marginTop: '0.25rem' }}>
                  Status: <span style={{ color: c.status === 'outreach_required' ? 'var(--blue-400)' : 'var(--orange-400)' }}>{c.status.replace('_', ' ')}</span>
                </div>
                <div style={{ fontSize: '0.85rem', color: 'var(--gray-500)', marginTop: '0.25rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  Reason: {c.failure_reason}
                </div>
              </li>
            ))}
          </ul>
        </div>

        {/* Right column: Case details and actions */}
        <div className="escalation-details" style={{ flex: '1 1 60%', background: 'var(--gray-900)', borderRadius: 'var(--radius-lg)', border: '1px solid var(--gray-800)', padding: '1.5rem' }}>
          {!selectedCase ? (
            <div style={{ textAlign: 'center', color: 'var(--gray-500)', marginTop: '4rem' }}>
              Select a case from the list to view details and take action.
            </div>
          ) : (
            <div>
              <h3 style={{ fontSize: '1.25rem', marginBottom: '1rem', color: 'var(--text-primary)' }}>Case Details: {selectedCase.payment_id}</h3>
              
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '2rem' }}>
                <div>
                  <div style={{ color: 'var(--gray-400)', fontSize: '0.85rem' }}>Revenue at Risk</div>
                  <div style={{ fontSize: '1.1rem', fontWeight: 600 }}>{fmt(selectedCase.amount)}</div>
                </div>
                <div>
                  <div style={{ color: 'var(--gray-400)', fontSize: '0.85rem' }}>Status</div>
                  <div style={{ fontSize: '1.1rem', textTransform: 'capitalize' }}>{selectedCase.status.replace('_', ' ')}</div>
                </div>
                <div style={{ gridColumn: 'span 2' }}>
                  <div style={{ color: 'var(--gray-400)', fontSize: '0.85rem' }}>Stopping Reason</div>
                  <div style={{ fontSize: '1rem', background: 'var(--gray-950)', padding: '0.75rem', borderRadius: '4px', border: '1px solid var(--gray-800)', marginTop: '0.25rem' }}>
                    {selectedCase.failure_reason}
                  </div>
                </div>
              </div>

              <div style={{ borderTop: '1px solid var(--gray-800)', paddingTop: '1.5rem' }}>
                <h4 style={{ marginBottom: '1rem' }}>AI Customer Outreach</h4>
                <p style={{ color: 'var(--gray-400)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
                  Use the Outreach Agent to draft a personalized email to this customer based on their payment history and failure reason.
                </p>

                {!draft && !drafting && (
                  <button className="btn-primary" onClick={() => handleDraftReminder(selectedCase.payment_id)}>
                    ✎ Draft Email with AI
                  </button>
                )}

                {drafting && <p style={{ color: 'var(--gray-400)' }}><span className="spinner-sm" /> The AI is drafting the email...</p>}
                
                {draftError && <p className="error-text">⚠ {draftError}</p>}

                {draft && (
                  <div className="email-draft-box" style={{ background: 'var(--gray-950)', padding: '1.5rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--gray-700)' }}>
                    <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'inherit', margin: 0, fontSize: '0.95rem', lineHeight: '1.5', color: 'var(--gray-200)' }}>
                      {draft}
                    </pre>
                    <div style={{ marginTop: '1.5rem', display: 'flex', gap: '1rem' }}>
                      <button className="btn-execute" onClick={() => alert('Email sent! (Simulated)')}>
                        📧 Send Reminder (Simulated)
                      </button>
                      <button className="btn-secondary" onClick={() => setDraft(null)}>
                        Discard Draft
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  )
}
