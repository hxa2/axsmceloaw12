// src/components/results/SolutionSummary.tsx
// =============================================
// Tóm tắt kết quả tối ưu: chi phí, số vòng lặp, cải thiện %.

import {
  CheckCircle,
  Warning,
  ArrowsClockwise,
  TrendDown,
} from '@phosphor-icons/react'
import { formatNumber } from '@/utils/matrix'
import type { SolveResponse } from '@/types/transportation'

interface SolutionSummaryProps {
  result: SolveResponse
}

export function SolutionSummary({ result }: SolutionSummaryProps) {
  const improvement =
    result.initialCost && result.initialCost > 0
      ? ((result.initialCost - result.totalCost) / result.initialCost) * 100
      : null

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-4)' }}>
      {/* Status row */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-3)', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-2)' }}>
          {result.isOptimal ? (
            <CheckCircle size={20} weight="fill" style={{ color: 'var(--success)' }} />
          ) : (
            <Warning size={20} weight="fill" style={{ color: 'var(--warning)' }} />
          )}
          <span
            style={{
              fontSize: '0.9375rem',
              fontWeight: 700,
              color: result.isOptimal ? 'var(--success)' : 'var(--warning)',
            }}
          >
            {result.isOptimal ? 'Tối ưu toàn cục' : 'Chưa tối ưu'}
          </span>
        </div>

        <span className="badge badge-neutral" style={{ fontFamily: 'var(--font-mono)', fontSize: '0.6875rem' }}>
          {result.numIterations} vòng lặp
        </span>
      </div>

      {/* Metrics row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 'var(--sp-3)' }}>
        {/* Optimal cost */}
        <div className="result-cost-display">
          <span className="cost-label">Chi phí tối ưu</span>
          <span className="cost-value">{formatNumber(result.totalCost)}</span>
          {result.isOptimal && (
            <span className="badge badge-success" style={{ alignSelf: 'flex-start', marginTop: '2px' }}>
              f(X*)
            </span>
          )}
        </div>

        {/* Initial cost */}
        {result.initialCost !== null && result.initialCost !== undefined && (
          <div className="result-cost-display">
            <span className="cost-label">Chi phí ban đầu</span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '1.5rem', fontWeight: 600, color: 'var(--text-secondary)', letterSpacing: '-0.02em' }}>
              {formatNumber(result.initialCost)}
            </span>
            <span className="badge badge-neutral" style={{ alignSelf: 'flex-start', marginTop: '2px' }}>
              f(X⁰)
            </span>
          </div>
        )}

        {/* Improvement */}
        {improvement !== null && improvement > 0.001 && (
          <div className="result-cost-display" style={{ background: 'var(--success-muted)', borderColor: 'rgba(63,185,80,0.2)' }}>
            <span className="cost-label">Cải thiện</span>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 'var(--sp-1)' }}>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '1.5rem', fontWeight: 700, color: 'var(--success)', letterSpacing: '-0.02em' }}>
                {improvement.toFixed(1)}
              </span>
              <span style={{ fontSize: '0.875rem', color: 'var(--success)', fontWeight: 500 }}>%</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-1)', marginTop: 2 }}>
              <TrendDown size={12} weight="bold" style={{ color: 'var(--success)' }} />
              <span style={{ fontSize: '0.75rem', color: 'var(--success)' }}>
                −{formatNumber(result.initialCost! - result.totalCost)}
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Message */}
      {result.message && (
        <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
          {result.message}
        </p>
      )}

      {/* Warnings */}
      {result.warnings.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-2)' }}>
          {result.warnings.map((w, i) => (
            <div key={i} className="warning-banner">
              <Warning size={16} weight="fill" style={{ flexShrink: 0, marginTop: 1 }} />
              <span style={{ lineHeight: 1.5 }}>{w}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
