/**
 * src/api/recovery.js
 *
 * API wrapper for all ReviveAI recovery endpoints.
 *
 * Uses the Vite proxy (/api → http://localhost:8000)
 * so no API keys or backend URLs appear in frontend code.
 */

const BASE_URL = '/api/v1'

// ============================================================
// Shared fetch helpers
// ============================================================

async function _get(path) {
  const response = await fetch(`${BASE_URL}${path}`, {
    method: 'GET',
    headers: {
      Accept: 'application/json',
    },
  })

  if (!response.ok) {
    let detail = `HTTP ${response.status}`
    try {
      const err = await response.json()
      detail = err.detail || detail
    } catch {
      // ignore JSON parse error
    }
    const error = new Error(detail)
    error.status = response.status
    throw error
  }

  return response.json()
}

async function _post(path, body) {
  const response = await fetch(`${BASE_URL}${path}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify(body),
  })

  if (!response.ok) {
    let detail = `HTTP ${response.status}`
    try {
      const err = await response.json()
      detail = err.detail || detail
    } catch {
      // ignore JSON parse error
    }
    const error = new Error(detail)
    error.status = response.status
    throw error
  }

  return response.json()
}

// ============================================================
// POST /api/v1/recovery/analyze
// ============================================================

/**
 * Analyze a payment for recovery eligibility and recommendation.
 * Includes AI narrative explanation.
 *
 * @param {string} paymentId  — e.g. "pay_002610"
 * @returns {Promise<Object>} — Structured recovery analysis
 */
export async function analyzeRecovery(paymentId) {
  return _post('/recovery/analyze', { payment_id: paymentId })
}

// ============================================================
// POST /api/v1/recovery/execute
// ============================================================

/**
 * Execute bounded recovery for one payment (SIMULATION MODE).
 * LLM is NOT involved — fully deterministic.
 *
 * @param {string} paymentId  — e.g. "pay_002610"
 * @returns {Promise<Object>} — Execution result + audit events
 */
export async function executeRecovery(paymentId) {
  return _post('/recovery/execute', { payment_id: paymentId })
}

// ============================================================
// POST /api/v1/recovery/batch
// ============================================================

/**
 * Batch recovery execution for multiple payments (SIMULATION MODE).
 * Returns per-payment results and aggregate metrics.
 *
 * @param {string[]} paymentIds — e.g. ["pay_002610", "pay_000016"]
 * @returns {Promise<Object>}   — { items: [...], metrics: {...} }
 */
export async function runBatchRecovery(paymentIds) {
  return _post('/recovery/batch', { payment_ids: paymentIds })
}

// ============================================================
// POST /api/v1/recovery/opportunities
// ============================================================

/**
 * Deterministic recovery opportunity ranking for a list of payments.
 * No LLM. No execution. Pure ranking of what SHOULD be done.
 *
 * @param {string[]} paymentIds — e.g. ["pay_002610", "pay_000016"]
 * @returns {Promise<Object>}   — { opportunities: [...], summary: {...} }
 */
export async function getRecoveryOpportunities(paymentIds) {
  return _post('/recovery/opportunities', { payment_ids: paymentIds })
}

// ============================================================
// POST /api/v1/recovery/draft_reminder
// ============================================================

export async function draftReminder(paymentId) {
  return _post('/recovery/draft_reminder', { payment_id: paymentId })
}

// ============================================================
// GET /api/v1/recovery/escalated
// ============================================================

export async function getEscalatedCases() {
  return _get('/recovery/escalated')
}

// ============================================================
// POST /api/v1/recovery/explain
// ============================================================

/**
 * Get deterministic recovery explanation & decision trace for a payment.
 * Read-only, no execution or LLM.
 *
 * @param {string} paymentId — e.g. "pay_002610"
 * @returns {Promise<Object>} — { payment_id, explainability, decision_trace }
 */
export async function getRecoveryExplanation(paymentId) {
  return _post('/recovery/explain', { payment_id: paymentId })
}


