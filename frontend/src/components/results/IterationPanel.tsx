// src/components/results/IterationPanel.tsx
// ============================================
// Panel hiển thị từng bước lặp của quá trình tối ưu.

import { useState } from 'react'
import {
  CaretDown,
  CaretRight,
  CheckCircle,
  ArrowsClockwise,
  Sparkle,
  ArrowRight,
} from '@phosphor-icons/react'
import { AllocationTable } from './AllocationTable'
import { formatNumber } from '@/utils/matrix'
import type { SolveResponse } from '@/types/transportation'

interface IterationPanelProps {
  result: SolveResponse
}

export function IterationPanel({ result }: IterationPanelProps) {
  const [expandedStep, setExpandedStep] = useState<number | null>(
    result.iterations.length > 0 ? result.iterations.length - 1 : null,
  )

  const sourceNames = result.sourceNames ?? result.allocationMatrix.map((_, i) => `S${i + 1}`)
  const destNames = result.destinationNames ?? (result.allocationMatrix[0] ?? []).map((_, j) => `D${j + 1}`)

  // Reconstruct supply/demand from last allocation + basis
  const m = result.allocationMatrix.length
  const n = (result.allocationMatrix[0] ?? []).length

  // We derive supply/demand from the last allocation matrix row/col sums
  const supply = Array.from({ length: m }, (_, i) =>
    result.allocationMatrix[i].reduce((a, b) => a + b, 0),
  )
  const demand = Array.from({ length: n }, (_, j) =>
    result.allocationMatrix.reduce((sum, row) => sum + (row[j] ?? 0), 0),
  )

  const costMatrix: number[][] = Array.from({ length: m }, () => Array(n).fill(0))
  // Reconstruct cost from initial iteration's reduced costs + u,v
  // (simplified: just use dummy cost matrix since it's just for display)

  const toggleStep = (step: number) => {
    setExpandedStep(expandedStep === step ? null : step)
  }

  if (result.iterations.length === 0) {
    return (
      <div style={{ padding: 'var(--sp-5)' }}>
        <p style={{ fontSize: '0.875rem', color: 'var(--text-tertiary)' }}>
          Không có dữ liệu chi tiết từng bước.
        </p>
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-3)' }}>
      {result.iterations.map((iter) => {
        const isExpanded = expandedStep === iter.step
        const isInitial = iter.step === 0
        const isOptimal = result.isOptimal && iter.step === result.iterations.length - 1 && iter.step > 0

        // Derive supply/demand from this iteration's allocation sums
        const iterSupply = iter.allocationMatrix.map((row) => row.reduce((a, b) => a + b, 0))
        const iterDemand = Array.from({ length: iter.allocationMatrix[0]?.length ?? 0 }, (_, j) =>
          iter.allocationMatrix.reduce((sum, row) => sum + (row[j] ?? 0), 0),
        )

        return (
          <div
            key={iter.step}
            className={`iteration-card ${isExpanded ? 'is-active' : ''}`}
          >
            {/* Header */}
            <div
              className="iteration-header"
              onClick={() => toggleStep(iter.step)}
              role="button"
              aria-expanded={isExpanded}
            >
              {/* Step badge */}
              <div className={`iteration-step-badge ${isInitial ? 'is-initial' : isOptimal ? 'is-optimal' : ''}`}>
                {isInitial ? (
                  <Sparkle size={14} weight="fill" />
                ) : isOptimal ? (
                  <CheckCircle size={14} weight="fill" />
                ) : (
                  iter.step
                )}
              </div>

              {/* Step label */}
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                  {isInitial
                    ? 'Phương án ban đầu'
                    : isOptimal
                      ? 'Phương án tối ưu ✓'
                      : `Vòng lặp ${iter.step}`}
                </div>
                {iter.totalCost !== null && (
                  <div style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: isOptimal ? 'var(--success)' : 'var(--text-tertiary)' }}>
                    f(X) = {formatNumber(iter.totalCost, 2)}
                  </div>
                )}
              </div>

              {/* Pivot info */}
              {iter.enteringCell && iter.leavingCell && (
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-2)', fontSize: '0.6875rem', fontFamily: 'var(--font-mono)' }}>
                  <span className="badge badge-success" style={{ padding: '0.1rem 0.35rem' }}>
                    +({iter.enteringCell[0]+1},{iter.enteringCell[1]+1})
                  </span>
                  <ArrowRight size={10} />
                  <span className="badge badge-warning" style={{ padding: '0.1rem 0.35rem' }}>
                    −({iter.leavingCell[0]+1},{iter.leavingCell[1]+1})
                  </span>
                </div>
              )}

              {/* Chevron */}
              <div style={{ color: 'var(--text-tertiary)', flexShrink: 0 }}>
                {isExpanded ? <CaretDown size={14} /> : <CaretRight size={14} />}
              </div>
            </div>

            {/* Body (expanded) */}
            {isExpanded && (
              <div className="iteration-body fade-in">
                {/* Description */}
                {iter.description && (
                  <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', marginBottom: 'var(--sp-4)', lineHeight: 1.5 }}>
                    {iter.description}
                  </p>
                )}

                {/* Cycle visualization */}
                {iter.cycle && iter.cycle.length > 0 && (
                  <div style={{ marginBottom: 'var(--sp-4)' }}>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', marginBottom: 'var(--sp-2)', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                      Chu trình điều chỉnh
                    </div>
                    <div className="cycle-indicator">
                      {iter.cycle.map(([ci, cj], idx) => (
                        <span key={idx} className={`cycle-cell ${idx % 2 === 0 ? 'cycle-cell-plus' : 'cycle-cell-minus'}`}>
                          ({ci+1},{cj+1}) {idx % 2 === 0 ? '+' : '−'}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Allocation table */}
                <AllocationTable
                  iteration={iter}
                  costMatrix={iter.allocationMatrix.map((row, i) =>
                    row.map((_, j) => {
                      // Reconstruct cost: c_ij = u_i + v_j - delta_ij (for non-basis)
                      // For basis: c_ij = u_i + v_j (by definition)
                      const ui = iter.potentialsU?.[i]
                      const vj = iter.potentialsV?.[j]
                      const delta = iter.reducedCosts?.[i]?.[j]
                      if (ui !== undefined && ui !== null && vj !== undefined && vj !== null) {
                        if (delta !== null && delta !== undefined) {
                          return ui + vj - delta  // c_ij = u_i + v_j - Δ_ij
                        }
                        return ui + vj  // basis cell: c_ij = u_i + v_j
                      }
                      return 0
                    }),
                  )}
                  sourceNames={sourceNames}
                  destinationNames={destNames}
                  supply={iterSupply}
                  demand={iterDemand}
                />
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
