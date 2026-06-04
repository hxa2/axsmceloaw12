// src/pages/ForbiddenCellsPage.tsx
// ==================================
// Tab: Bài toán vận tải có ô cấm

import { useState, useCallback } from 'react'
import { Play, Lock, LockOpen } from '@phosphor-icons/react'
import { api, ApiError } from '@/api/client'
import type { ExtendedSolveResponse, ForbiddenCellsRequest, ForbiddenCell } from '@/types/extended'
import {
  ExtendedResultPanel,
  SummaryCard,
  FeasibilityBadge,
} from '@/components/extended/ExtendedResultPanel'

function makeMatrix(m: number, n: number, fill = 1): number[][] {
  return Array.from({ length: m }, (_, i) =>
    Array.from({ length: n }, (_, j) => fill + i + j)
  )
}

export function ForbiddenCellsPage() {
  const [m, setM] = useState(3)
  const [n, setN] = useState(3)
  const [costMatrix, setCostMatrix] = useState<number[][]>(makeMatrix(3, 3))
  const [supply, setSupply] = useState<number[]>([30, 40, 30])
  const [demand, setDemand] = useState<number[]>([25, 35, 40])
  const [forbidden, setForbidden] = useState<Set<string>>(new Set(['0,2', '1,0']))

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<ExtendedSolveResponse | null>(null)

  const toggleForbidden = useCallback((i: number, j: number) => {
    const key = `${i},${j}`
    setForbidden(prev => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })
  }, [])

  const handleResize = useCallback((newM: number, newN: number) => {
    setM(newM); setN(newN)
    setCostMatrix(prev => {
      const next = makeMatrix(newM, newN)
      for (let i = 0; i < Math.min(newM, prev.length); i++)
        for (let j = 0; j < Math.min(newN, prev[0]?.length ?? 0); j++)
          next[i][j] = prev[i][j]
      return next
    })
    setSupply(prev => Array.from({ length: newM }, (_, i) => prev[i] ?? 0))
    setDemand(prev => Array.from({ length: newN }, (_, j) => prev[j] ?? 0))
    // Remove forbidden cells outside new bounds
    setForbidden(prev => new Set([...prev].filter(k => {
      const [r, c] = k.split(',').map(Number)
      return r < newM && c < newN
    })))
  }, [])

  const handleSolve = useCallback(async () => {
    setLoading(true); setError(null); setResult(null)
    try {
      const forbiddenCells: ForbiddenCell[] = [...forbidden].map(k => {
        const [row, col] = k.split(',').map(Number)
        return { row, col }
      })
      const req: ForbiddenCellsRequest = { costMatrix, supply, demand, forbiddenCells }
      const res = await api.solveForbidden(req)
      setResult(res)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : String(err))
    } finally {
      setLoading(false)
    }
  }, [costMatrix, supply, demand, forbidden])

  const alloc = result?.solution?.allocationMatrix as number[][] | undefined
  const isFeasible = result?.interpretation?.isFeasibleRespectingForbiddenCells as boolean | undefined
  const bigM = result?.transformedProblem?.bigMValue as number | undefined
  const totalCost = result?.solution?.totalCost as number | undefined
  const srcNames = (result?.solution?.sourceNames as string[]) ?? supply.map((_, i) => `S${i+1}`)
  const dstNames = (result?.solution?.destinationNames as string[]) ?? demand.map((_, j) => `D${j+1}`)

  const highlightSet = new Set<string>()
  alloc?.forEach((row, i) => row.forEach((v, j) => { if (v > 0) highlightSet.add(`${i},${j}`) }))

  return (
    <div className="ext-page-layout">
      <aside className="ext-sidebar">
        <div className="editor-section">
          <div className="editor-section-title" style={{ color: '#dc2626' }}>
            🔒 Vận tải có ô cấm
          </div>
          <p style={{ fontSize: '0.8125rem', color: 'var(--text-tertiary)', lineHeight: 1.5 }}>
            Click vào ô trong ma trận để đánh dấu <strong>cấm</strong>. Ô cấm sẽ được thay bằng <strong>Big-M</strong>.
          </p>
        </div>

        <div className="editor-section">
          <label className="label">Kích thước</label>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <input type="number" className="input" min={2} max={8} value={m}
              onChange={e => handleResize(Math.max(2, +e.target.value), n)}
              style={{ width: 64, textAlign: 'center' }} />
            <span style={{ color: 'var(--text-tertiary)' }}>×</span>
            <input type="number" className="input" min={2} max={8} value={n}
              onChange={e => handleResize(m, Math.max(2, +e.target.value))}
              style={{ width: 64, textAlign: 'center' }} />
          </div>
        </div>

        {/* Interactive cost matrix with forbidden toggle */}
        <div className="editor-section">
          <label className="label">Ma trận chi phí (click ô để cấm/bỏ cấm)</label>
          {forbidden.size > 0 && (
            <div style={{ fontSize: '0.75rem', color: 'var(--danger)', marginBottom: 8 }}>
              🔒 {forbidden.size} ô bị cấm
            </div>
          )}
          <div style={{ overflowX: 'auto' }}>
            {costMatrix.map((row, i) => (
              <div key={i} style={{ display: 'flex', gap: 4, marginBottom: 4 }}>
                {row.map((val, j) => {
                  const key = `${i},${j}`
                  const isForb = forbidden.has(key)
                  return (
                    <div key={j} style={{ position: 'relative' }}>
                      {isForb ? (
                        <div
                          onClick={() => toggleForbidden(i, j)}
                          style={{
                            width: 52, height: 36,
                            background: 'var(--danger-muted)',
                            border: '2px solid var(--danger)',
                            borderRadius: 'var(--radius-sm)',
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                            cursor: 'pointer', fontSize: '1rem',
                          }}
                          title={`Ô (${i+1},${j+1}) bị cấm. Click để bỏ cấm.`}
                        >
                          🔒
                        </div>
                      ) : (
                        <div style={{ position: 'relative' }}>
                          <input type="number" className="input input-mono"
                            value={val} style={{ width: 52, padding: '4px 6px', fontSize: '0.875rem', paddingRight: 20 }}
                            onChange={e => {
                              const v = parseFloat(e.target.value) || 0
                              setCostMatrix(prev => prev.map((r, ri) => ri === i ? r.map((c, ci) => ci === j ? v : c) : r))
                            }} />
                          <button
                            type="button"
                            onClick={() => toggleForbidden(i, j)}
                            title="Đánh dấu ô cấm"
                            style={{
                              position: 'absolute', right: 2, top: '50%', transform: 'translateY(-50%)',
                              background: 'none', border: 'none', cursor: 'pointer',
                              padding: 2, color: 'var(--text-disabled)', fontSize: 10,
                            }}
                          >🔒</button>
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            ))}
          </div>
        </div>

        <div className="editor-section">
          <label className="label">Lượng phát aᵢ</label>
          <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
            {supply.map((v, i) => (
              <input key={i} type="number" className="input input-mono" value={v}
                style={{ width: 64, padding: '4px 6px', fontSize: '0.875rem' }}
                onChange={e => setSupply(prev => prev.map((x, xi) => xi === i ? parseFloat(e.target.value) || 0 : x))} />
            ))}
          </div>
        </div>

        <div className="editor-section">
          <label className="label">Lượng thu bⱼ</label>
          <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
            {demand.map((v, j) => (
              <input key={j} type="number" className="input input-mono" value={v}
                style={{ width: 64, padding: '4px 6px', fontSize: '0.875rem' }}
                onChange={e => setDemand(prev => prev.map((x, xi) => xi === j ? parseFloat(e.target.value) || 0 : x))} />
            ))}
          </div>
        </div>

        <button type="button" className="btn btn-primary solve-btn" onClick={handleSolve} disabled={loading}
          style={{ backgroundColor: '#dc2626', borderColor: '#dc2626' }}>
          {loading ? <><span className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} /> Đang giải...</> : <><Play size={16} weight="fill" /> Giải với ô cấm</>}
        </button>
      </aside>

      <div className="ext-result-area">
        {!result && !loading && !error ? (
          <EmptyState icon="🔒" title="Chưa có kết quả" description="Đánh dấu ô cấm và nhấn Giải." />
        ) : (
          <ExtendedResultPanel response={result} loading={loading} error={error}>
            {result && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-5)' }}>
                <div style={{ display: 'flex', gap: 'var(--sp-3)', flexWrap: 'wrap', alignItems: 'center' }}>
                  <SummaryCard label="Tổng chi phí tối thiểu" value={totalCost ?? '—'} color="#dc2626" />
                  {bigM && <SummaryCard label="Giá trị Big-M" value="M" color="var(--text-tertiary)" subtitle={`= ${bigM.toExponential(2)}`} />}
                  {isFeasible !== undefined && (
                    <div style={{ padding: 'var(--sp-4)' }}>
                      <FeasibilityBadge isFeasible={isFeasible} label={isFeasible ? 'Không sử dụng ô cấm' : 'Vi phạm ô cấm!'} />
                    </div>
                  )}
                </div>

                {/* Allocation matrix with forbidden highlights */}
                {alloc && (
                  <div>
                    <div style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-tertiary)', marginBottom: 'var(--sp-2)' }}>
                      Ma trận phân bổ tối ưu
                    </div>
                    <div className="matrix-grid-wrapper">
                      <table style={{ borderCollapse: 'collapse', fontSize: '0.875rem' }}>
                        <thead>
                          <tr>
                            <th style={thStyle}></th>
                            {dstNames.map((h, j) => <th key={j} style={{ ...thStyle, color: 'var(--accent)' }}>{h}</th>)}
                          </tr>
                        </thead>
                        <tbody>
                          {alloc.map((row, i) => (
                            <tr key={i}>
                              <td style={{ ...thStyle, color: 'var(--accent)' }}>{srcNames[i]}</td>
                              {row.map((val, j) => {
                                const key = `${i},${j}`
                                const isForbiddenCell = forbidden.has(key)
                                const isAllocated = val > 0
                                const hasForbiddenAlloc = isForbiddenCell && val > 0
                                return (
                                  <td key={j} style={{
                                    ...tdStyle,
                                    background: hasForbiddenAlloc ? '#fee2e2' : isForbiddenCell ? 'var(--bg-inset)' : isAllocated ? 'var(--accent-muted)' : 'var(--bg-surface)',
                                    border: hasForbiddenAlloc ? '2px solid var(--danger)' : isAllocated ? '2px solid var(--accent)' : '1px solid var(--border-subtle)',
                                    fontWeight: isAllocated ? 700 : 400,
                                    fontFamily: 'var(--font-mono)',
                                    color: hasForbiddenAlloc ? 'var(--danger)' : 'var(--text-primary)',
                                    position: 'relative',
                                  }}>
                                    {isForbiddenCell && !isAllocated ? '🔒' : val > 0 ? val : '–'}
                                    {hasForbiddenAlloc && (
                                      <span style={{ position: 'absolute', top: -4, right: -4, fontSize: 10 }}>⚠️</span>
                                    )}
                                  </td>
                                )
                              })}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            )}
          </ExtendedResultPanel>
        )}
      </div>
    </div>
  )
}

const thStyle: React.CSSProperties = {
  padding: '6px 12px', background: 'var(--bg-inset)', border: '1px solid var(--border-subtle)',
  textAlign: 'center', fontWeight: 600, fontSize: '0.8125rem', color: 'var(--text-secondary)',
}
const tdStyle: React.CSSProperties = {
  padding: '8px 14px', border: '1px solid var(--border-subtle)', textAlign: 'center', minWidth: 60,
}
function EmptyState({ icon, title, description }: { icon: string; title: string; description: string }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
      <div className="empty-state">
        <div className="empty-icon" style={{ fontSize: '2rem' }}>{icon}</div>
        <div>
          <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 8 }}>{title}</h3>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-tertiary)', maxWidth: '32ch', margin: '0 auto' }}>{description}</p>
        </div>
      </div>
    </div>
  )
}
