/**
 * PaymentCard.jsx — Payment detail data table
 * Phase 4: Cleaner layout, FAILED status highlight, proper formatting
 */

function formatAmount(amount, currency) {
  if (amount == null) return '—'
  const sym = currency === 'INR' ? '₹' : (currency || '')
  return `${sym}${Number(amount).toLocaleString('en-IN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`
}

function titleCase(str) {
  if (!str) return '—'
  return str.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

export function PaymentCard({ payment }) {
  if (!payment) return null

  const isFailed = payment.payment_status === 'failed'

  const rows = [
    {
      label: 'Payment Status',
      value: titleCase(payment.payment_status),
      className: isFailed ? 'data-value--failed' : '',
    },
    {
      label: 'Amount',
      value: formatAmount(payment.amount, payment.currency),
      className: 'data-value--amount',
    },
    {
      label: 'Payment Method',
      value: titleCase(payment.payment_method),
    },
    {
      label: 'Failure Reason',
      value: titleCase(payment.failure_reason),
    },
    {
      label: 'Retry Count',
      value: payment.retry_count != null
        ? `${payment.retry_count} attempt${payment.retry_count === 1 ? '' : 's'}`
        : '—',
    },
    {
      label: 'Subscription',
      value: titleCase(payment.subscription_status),
    },
    {
      label: 'Customer Tenure',
      value: payment.customer_age_days != null
        ? `${payment.customer_age_days} days`
        : '—',
    },
    {
      label: 'Lifetime Value',
      value: formatAmount(payment.lifetime_value, 'INR'),
    },
  ]

  return (
    <div className="card" aria-label="Payment Details">
      <div className="card-header">
        <div className="card-icon card-icon--blue" aria-hidden="true">💳</div>
        <span className="card-title">Payment Details</span>
      </div>

      <div className="payment-id-row">
        <span className="payment-id-label">Payment ID</span>
        <code className="payment-id-value">{payment.payment_id}</code>
      </div>

      <div role="list" aria-label="Payment data">
        {rows.map(row => (
          <div className="data-row" key={row.label} role="listitem">
            <span className="data-label">{row.label}</span>
            <span className={`data-value data-value--mono ${row.className || ''}`}>
              {row.value}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
