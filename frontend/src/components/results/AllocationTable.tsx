// src/components/results/AllocationTable.tsx
// =============================================
// Bảng hiển thị ma trận phân phối X với:
//   - Chi phí cướp (góc trên trái ô)
//   - Luồng vận chuyển (giữa ô, bold)
//   - Δᵢⱼ reduced cost (góc dưới phải ô loại)
//   - Highlight ô cơ sở, ô vào, ô ra, chu trình

import { formatNumber } from '@/utils/matrix'
import type { IterationResult } from '@/types/transportation'

interface AllocationTableProps {
  iteration: IterationResult
  costMatrix: number[][]
  sourceNames: string[]
  destinationNames: string[]
  supply: number[]
  demand: number[]
}

const _EPS = 1e-9

export function AllocationTable({
  iteration,
  costMatrix,
  sourceNames,
  destinationNames,
  supply,
  demand,
}: AllocationTableProps) {
  const { allocationMatrix: X, potentialsU: u, potentialsV: v, reducedCosts } = iteration
  const m = X.length
  const n = X[0]?.length ?? 0

  const basisCells = new Set<string>()
  for (let i = 0; i < m; i++) {
    for (let j = 0; j < n; j++) {
      if (X[i][j] > _EPS) basisCells.add(`${i}-${j}`)
    }
  }
  // Also count zero-allocation basis cells from reduced costs (NaN = basis)
  if (reducedCosts) {
    for (let i = 0; i < m; i++) {
      for (let j = 0; j < n; j++) {
        if (reducedCosts[i]?.[j] === null) basisCells.add(`${i}-${j}`)
      }
    }
  }

  const enteringKey = iteration.enteringCell ? `${iteration.enteringCell[0]}-${iteration.enteringCell[1]}` : null
  const leavingKey = iteration.leavingCell ? `${iteration.leavingCell[0]}-${iteration.leavingCell[1]}` : null
  const cycleSet = new Set<string>(
    (iteration.cycle ?? []).map(([i, j]) => `${i}-${j}`),
  )

  return (
    <div style={{ overflowX: 'auto' }}>
      <table className="allocation-table">
        <thead>
          <tr>
            {/* Corner */}
            <th style={{ background: 'var(--bg-surface)', position: 'relative', minWidth: 72 }}>
              {u && v && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  <span style={{ fontSize: '0.5rem', color: 'var(--text-tertiary)', letterSpacing: '0.05em', textTransform: 'uppercase' }}>u / v →</span>
                </div>
              )}
            </th>

            {/* Destination headers with v_j */}
            {Array.from({ length: n }, (_, j) => (
              <th key={j}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 1, alignItems: 'center' }}>
                  {v && v[j] !== null && (
                    <span style={{ color: 'var(--accent)', fontFamily: 'var(--font-mono)', fontStyle: 'italic', fontWeight: 700, fontSize: '0.8125rem', letterSpacing: 0 }}>
                      {formatNumber(v[j])}
                    </span>
                  )}
                  <span style={{ fontWeight: 500, fontSize: '0.6875rem' }}>{destinationNames[j]}</span>
                  <span style={{ color: 'var(--accent)', fontWeight: 700, fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}>
                    {formatNumber(demand[j])}
                  </span>
                </div>
              </th>
            ))}

            {/* Supply header */}
            <th style={{ color: 'var(--success)', background: 'var(--success-muted)' }}>aᵢ</th>
          </tr>
        </thead>

        <tbody>
          {Array.from({ length: m }, (_, i) => (
            <tr key={i}>
              {/* Source label with u_i */}
              <th style={{ textAlign: 'left', paddingLeft: 'var(--sp-3)' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  {u && u[i] !== null && (
                    <span style={{ color: 'var(--accent)', fontFamily: 'var(--font-mono)', fontStyle: 'italic', fontWeight: 700, fontSize: '0.8125rem' }}>
                      {formatNumber(u[i])}
                    </span>
                  )}
                  <span style={{ fontWeight: 500, fontSize: '0.6875rem' }}>{sourceNames[i]}</span>
                  <span style={{ color: 'var(--success)', fontWeight: 700, fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}>
                    {formatNumber(supply[i])}
                  </span>
                </div>
              </th>

              {/* Data cells */}
              {Array.from({ length: n }, (_, j) => {
                const key = `${i}-${j}`
                const isBasis = basisCells.has(key)
                const isEntering = key === enteringKey
                const isLeaving = key === leavingKey
                const inCycle = cycleSet.has(key)
                const flow = X[i][j]
                const cost = costMatrix[i]?.[j]
                const delta = reducedCosts?.[i]?.[j]
                const isPositiveDelta = !isBasis && delta !== null && delta !== undefined && delta > _EPS

                let cellClass = ''
                if (isEntering) cellClass = 'cell-entering'
                else if (isLeaving) cellClass = 'cell-leaving'
                else if (isBasis) cellClass = 'cell-basis'

                const cyclePos = iteration.cycle?.findIndex(([ci, cj]) => ci === i && cj === j) ?? -1
                const isPlus = cyclePos !== -1 && cyclePos % 2 === 0
                const isMinus = cyclePos !== -1 && cyclePos % 2 !== 0

                return (
                  <td
                    key={j}
                    className={cellClass}
                    style={{
                      outline: inCycle && !isEntering && !isLeaving
                        ? '1px dashed var(--accent)'
                        : undefined,
                    }}
                  >
                    {/* Cost corner */}
                    <span className="cost-corner">{formatNumber(cost ?? 0)}</span>

                    {/* Main value */}
                    {isBasis ? (
                      <span className="flow-value" style={{ color: flow > _EPS ? 'var(--text-primary)' : 'var(--text-tertiary)' }}>
                        {flow > _EPS ? formatNumber(flow) : '0*'}
                      </span>
                    ) : (
                      <span className={`delta-value ${isPositiveDelta ? 'cell-positive-delta' : ''}`}>
                        {delta !== null && delta !== undefined ? formatNumber(delta) : '—'}
                      </span>
                    )}

                    {/* Cycle sign indicator */}
                    {inCycle && (
                      <span style={{
                        position: 'absolute',
                        bottom: 2,
                        left: 4,
                        fontSize: '0.65rem',
                        fontWeight: 700,
                        fontFamily: 'var(--font-mono)',
                        color: isPlus ? 'var(--success)' : 'var(--warning)',
                      }}>
                        {isPlus ? '⊕' : '⊖'}
                      </span>
                    )}
                  </td>
                )
              })}

              {/* Supply total */}
              <td style={{ background: 'var(--success-muted)', color: 'var(--success)', fontWeight: 700 }}>
                {formatNumber(supply[i])}
              </td>
            </tr>
          ))}
        </tbody>

        <tfoot>
          <tr>
            <th style={{ textAlign: 'left', paddingLeft: 'var(--sp-3)', color: 'var(--accent)', background: 'var(--accent-subtle)' }}>
              bⱼ
            </th>
            {Array.from({ length: n }, (_, j) => (
              <td
                key={j}
                style={{ background: 'var(--accent-subtle)', color: 'var(--accent)', fontWeight: 700, fontFamily: 'var(--font-mono)' }}
              >
                {formatNumber(demand[j])}
              </td>
            ))}
            <td style={{ background: 'var(--bg-inset)', textAlign: 'center', fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)', fontSize: '0.75rem', fontWeight: 600 }}>
              {formatNumber(supply.reduce((a, b) => a + b, 0))}
            </td>
          </tr>
        </tfoot>
      </table>
    </div>
  )
}
