/**
 * ProbabilityGauge.jsx — SVG circular gauge for Recovery Probability
 * Phase 4: Proper N/A state for ineligible payments, clean terminology
 */

export function ProbabilityGauge({ probability, eligible }) {
  // Always show card, but handle N/A for ineligible
  const hasValue = probability != null && eligible !== false

  const pct    = hasValue ? Math.min(100, Math.round(probability * 100)) : 0
  const size   = 120
  const stroke = 10
  const r      = (size - stroke) / 2
  const circ   = 2 * Math.PI * r
  const offset = circ - (pct / 100) * circ

  const color = !hasValue
    ? 'var(--color-text-muted)'
    : pct >= 75 ? 'var(--color-success)'
    : pct >= 50 ? 'var(--color-warning)'
    :             'var(--color-danger)'

  return (
    <div className="card" aria-label="Recovery Probability">
      <div className="card-header">
        <div className="card-icon card-icon--purple" aria-hidden="true">◎</div>
        <span className="card-title">Recovery Probability</span>
      </div>

      {hasValue ? (
        <div className="prob-gauge-wrap">
          <div style={{ position: 'relative', width: size, height: size }}>
            <svg
              width={size}
              height={size}
              role="img"
              aria-label={`Recovery probability: ${pct}%`}
              style={{ transform: 'rotate(-90deg)' }}
            >
              {/* Track */}
              <circle
                cx={size / 2} cy={size / 2} r={r}
                fill="none"
                stroke="var(--color-border)"
                strokeWidth={stroke}
              />
              {/* Progress */}
              <circle
                cx={size / 2} cy={size / 2} r={r}
                fill="none"
                stroke={color}
                strokeWidth={stroke}
                strokeDasharray={circ}
                strokeDashoffset={offset}
                strokeLinecap="round"
                style={{
                  transition: 'stroke-dashoffset 0.9s ease',
                  filter: `drop-shadow(0 0 5px ${color}80)`,
                }}
              />
            </svg>
            {/* Center label */}
            <div
              style={{
                position: 'absolute',
                inset: 0,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <span style={{ fontSize: 20, fontWeight: 800, fontFamily: 'var(--font-mono)', color, lineHeight: 1 }}>
                {pct}%
              </span>
              <span style={{ fontSize: 9, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginTop: 4 }}>
                Prob.
              </span>
            </div>
          </div>

          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 28, fontWeight: 800, fontFamily: 'var(--font-mono)', color, lineHeight: 1 }}>
              {(probability * 100).toFixed(2)}%
            </div>
            <div style={{ fontSize: 11, color: 'var(--color-text-muted)', marginTop: 6, maxWidth: 180 }}>
              Estimated likelihood of successful recovery
            </div>
          </div>
        </div>
      ) : (
        <div className="prob-na" aria-label="Recovery probability not applicable">
          <div className="prob-na-value">N/A</div>
          <div style={{ fontSize: 12, color: 'var(--color-text-muted)', textAlign: 'center' }}>
            {eligible === false
              ? 'Not calculated — payment is ineligible for recovery'
              : 'Probability not available'}
          </div>
        </div>
      )}
    </div>
  )
}
