/**
 * SearchForm.jsx — Payment ID input + Analyze button
 * Phase 4 Polish
 */
import { useState } from 'react'

export function SearchForm({ onSubmit, loading }) {
  const [value, setValue] = useState('')
  const [validationError, setValidationError] = useState('')

  function handleSubmit(e) {
    e.preventDefault()
    const id = value.trim()
    if (!id) {
      setValidationError('Please enter a payment ID.')
      return
    }
    if (!id.startsWith('pay_')) {
      setValidationError('Payment IDs must start with "pay_".')
      return
    }
    setValidationError('')
    onSubmit(id)
  }

  function handleChange(e) {
    setValue(e.target.value)
    if (validationError) setValidationError('')
  }

  return (
    <div>
      <form className="search-form" onSubmit={handleSubmit} id="search-form" role="search">
        <div className="search-field">
          <span className="search-icon" aria-hidden="true">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="11" cy="11" r="8"/>
              <line x1="21" y1="21" x2="16.65" y2="16.65"/>
            </svg>
          </span>
          <input
            id="payment-id-input"
            name="paymentId"
            type="text"
            className="search-input"
            placeholder="pay_002610"
            autoComplete="off"
            spellCheck={false}
            disabled={loading}
            aria-label="Payment ID"
            value={value}
            onChange={handleChange}
            aria-describedby={validationError ? 'search-error' : 'search-hint'}
            aria-invalid={!!validationError}
          />
        </div>
        <button
          id="analyze-btn"
          type="submit"
          className="btn-analyze"
          disabled={loading}
          aria-label={loading ? 'Analyzing payment, please wait' : 'Analyze payment'}
        >
          {loading ? (
            <>
              <span className="spinner-sm" aria-hidden="true" />
              Analyzing…
            </>
          ) : (
            <>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
              </svg>
              Analyze Payment
            </>
          )}
        </button>
      </form>

      {validationError && (
        <div id="search-error" role="alert" style={{ fontSize: 12, color: 'var(--color-danger)', textAlign: 'center', marginTop: 8 }}>
          {validationError}
        </div>
      )}

      {!validationError && (
        <div id="search-hint" className="search-hint">
          Try <code>pay_002610</code> for an eligible payment, or <code>pay_000016</code> for a blocked one
        </div>
      )}
    </div>
  )
}
