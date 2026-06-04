// src/pages/InequalityPage.tsx
// ==============================
// Tab: Bài toán vận tải với ràng buộc bất đẳng thức

import { useState, useCallback } from 'react'
import { Play, Warning } from '@phosphor-icons/react'
import { api, ApiError } from '@/api/client'
import type {
  ExtendedSolveResponse,
  InequalityRequest,
  SupplyConstraint,
  DemandConstraint,
} from '@/types/extended'
import {
  ExtendedResultPanel,
  MatrixTable,
  SummaryCard,
} from '@/components/extended/ExtendedResultPanel'

function makeMatrix(m: number, n: number): number[][] {
  return Array.from({ length: m }, (_, i) => Array.from({ length: n }, (_, j) => (i + 1) * 2 + j))
}

const SUPPLY_OPTIONS: { value: SupplyConstraint; label: string; symbol: string }[] = [
  { value: 'equal', label: 'Đúng bằng (=)', symbol: '=' },
  { value: 'less_or_equal', label: 'Không vượt quá (≤)', symbol: '≤' },
]
const DEMAND_OPTIONS: { value: DemandConstraint; label: string; symbol: string }[] = [
  { value: 'equal', label: 'Đúng bằng (=)', symbol: '=' },
]
const SUPPORTED = new Set(['less_or_equal|equal'])

export function InequalityPage() {
  const [m, setM] = useState(3)
  const [n, setN] = useState(3)
  const [costMatrix, setCostMatrix] = useState<number[][]>(makeMatrix(3, 3))
  const [supply, setSupply] = useState<number[]>([40, 50, 30])
  const [demand, setDemand] = useState<number[]>([30, 40, 35])
  const [supplyConstraint, setSupplyConstraint] = useState<SupplyConstraint>('less_or_equal')
  const [demandConstraint, setDemandConstraint] = useState<DemandConstraint>('equal')

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<ExtendedSolveResponse | null>(null)

  const totalSupply = supply.reduce((a, b) => a + b, 0)
  const totalDemand = demand.reduce((a, b) => a + b, 0)
  const isSupported = SUPPORTED.has(`${supplyConstraint}|${demandConstraint}`)
  const isInfeasible = supplyConstraint === 'less_or_equal' && totalSupply < totalDemand

  const handleResize = useCallback((newM: number, newN: number) => {
    setM(newM); setN(newN)
    setCostMatrix(prev => {
      const next = makeMatrix(newM, newN)
      for (let i = 0; i < Math.min(newM, prev.length); i++)
        for (let j = 0; j < Math.min(newN, prev[0]?.length ?? 0); j++)
          next[i][j] = prev[i][j]
      return next
    })
    setSupply(prev => Array.from({ length: newM }, (_, i) => prev[i] ?? 10))
    setDemand(prev => Array.from({ length: newN }, (_, j) => prev[j] ?? 10))
  }, [])

  const handleSolve = useCallback(async () => {
    if (!isSupported) return
    if (isInfeasible) return
    setLoading(true); setError(null); setResult(null)
    try {
      const req: InequalityRequest = {
        costMatrix, supply, demand,
        supplyConstraint, demandConstraint,
      }
      const res = await api.solveInequality(req)
      setResult(res)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : String(err))
    } finally {
      setLoading(false)
    }
  }, [costMatrix, supply, demand, supplyConstraint, demandConstraint, isSupported, isInfeasible])

  const alloc = result?.solution?.allocationMatrix as number[][] | undefined
  const dstNames = result?.solution?.destinationNames as string[] ?? demand.map((_, j) => `D${j+1}`)
  const srcNames = result?.solution?.sourceNames as string[] ?? supply.map((_, i) => `S${i+1}`)
  const totalCost = result?.solution?.totalCost as number | undefined
  const unusedSupply = result?.interpretation?.unusedSupplyBySource as Array<{ sourceName: string; unusedAmount: number }> | undefined
  const dummyIdx = result?.interpretation?.dummyDestinationIndex as number | null | undefined

  const highlightSet = new Set<string>()
  alloc?.forEach((row, i) => row.forEach((v, j) => { if (v > 0 && j !== dummyIdx) highlightSet.add(`${i},${j}`) }))

  return (
    <div className="ext-page-layout">
      <aside className="ext-sidebar">
        <div className="editor-section">
          <div className="editor-section-title" style={{ color: '#d97706' }}>
            ⩽ Ràng buộc bất đẳng thức
          </div>
          <p style={{ fontSize: '0.8125rem', color: 'var(--text-tertiary)', lineHeight: 1.5 }}>
            Khi nguồn không cần phát hết, tổng cung dư sẽ đưa về destination ảo "Không sử dụng".
          </p>
        </div>

        {/* Constraint selectors */}
        <div className="editor-section">
          <label className="label">Ràng buộc nguồn (supply)</label>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {SUPPLY_OPTIONS.map(opt => (
              <label key={opt.value} style={{
                display: 'flex', gap: 10, alignItems: 'center',
                padding: '8px 10px', borderRadius: 'var(--radius)',
                background: supplyConstraint === opt.value ? 'rgba(217,119,6,0.08)' : 'var(--bg-inset)',
                border: `1px solid ${supplyConstraint === opt.value ? '#d97706' : 'var(--border-subtle)'}`,
                cursor: 'pointer', fontSize: '0.875rem',
              }}>
                <input type="radio" name="supply-constraint" value={opt.value}
                  checked={supplyConstraint === opt.value}
                  onChange={() => setSupplyConstraint(opt.value)}
                  style={{ accentColor: '#d97706' }} />
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '1rem', color: '#d97706', fontWeight: 700 }}>{opt.symbol}</span>
                <span>{opt.label}</span>
              </label>
            ))}
          </div>
        </div>

        <div className="editor-section">
          <label className="label">Ràng buộc cầu (demand)</label>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {DEMAND_OPTIONS.map(opt => (
              <label key={opt.value} style={{
                display: 'flex', gap: 10, alignItems: 'center',
                padding: '8px 10px', borderRadius: 'var(--radius)',
                background: 'rgba(217,119,6,0.08)',
                border: '1px solid #d97706',
                cursor: 'pointer', fontSize: '0.875rem',
              }}>
                <input type="radio" name="demand-constraint" value={opt.value}
                  checked={demandConstraint === opt.value}
                  onChange={() => setDemandConstraint(opt.value as DemandConstraint)}
                  style={{ accentColor: '#d97706' }} />
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '1rem', color: '#d97706', fontWeight: 700 }}>{opt.symbol}</span>
                <span>{opt.label}</span>
              </label>
            ))}
          </div>
          {!isSupported && (
            <div style={{ marginTop: 8, padding: 10, background: 'var(--warning-muted)', borderRadius: 'var(--radius)', fontSize: '0.8125rem', color: 'var(--warning)' }}>
              ⚠️ Tổ hợp này chưa được hỗ trợ. Hiện chỉ hỗ trợ: nguồn ≤, cầu =.
            </div>
          )}
        </div>

        <div className="editor-section">
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8125rem' }}>
            <span style={{ color: 'var(--text-tertiary)' }}>Tổng cung: <strong>{totalSupply}</strong></span>
            <span style={{ color: 'var(--text-tertiary)' }}>Tổng cầu: <strong>{totalDemand}</strong></span>
          </div>
          {isInfeasible && (
            <div style={{ marginTop: 8, padding: 10, background: 'var(--danger-muted)', borderRadius: 'var(--radius)', fontSize: '0.8125rem', color: 'var(--danger)' }}>
              ✗ Không khả thi: tổng cung ({totalSupply}) &lt; tổng cầu ({totalDemand}).
            </div>
          )}
          {!isInfeasible && totalSupply > totalDemand && (
            <div style={{ marginTop: 8, padding: 10, background: 'var(--info-muted, rgba(37,99,235,0.06))', borderRadius: 'var(--radius)', fontSize: '0.8125rem', color: 'var(--info)' }}>
              ℹ️ Dư cung {totalSupply - totalDemand} — sẽ thêm destination ảo "Không sử dụng".
            </div>
          )}
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

        <div className="editor-section">
          <label className="label">Ma trận chi phí cᵢⱼ</label>
          {costMatrix.map((row, i) => (
            <div key={i} style={{ display: 'flex', gap: 4, marginBottom: 4 }}>
              {row.map((val, j) => (
                <input key={j} type="number" className="input input-mono" value={val}
                  style={{ width: 52, padding: '4px 6px', fontSize: '0.875rem' }}
                  onChange={e => {
                    const v = parseFloat(e.target.value) || 0
                    setCostMatrix(prev => prev.map((r, ri) => ri === i ? r.map((c, ci) => ci === j ? v : c) : r))
                  }} />
              ))}
            </div>
          ))}
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

        <button type="button" className="btn btn-primary solve-btn" onClick={handleSolve}
          disabled={loading || !isSupported || isInfeasible}
          style={{ backgroundColor: '#d97706', borderColor: '#d97706' }}>
          {loading ? <><span className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} /> Đang giải...</> : <><Play size={16} weight="fill" /> Giải bài toán</>}
        </button>
      </aside>

      <div className="ext-result-area">
        {!result && !loading && !error ? (
          <EmptyState icon="⩽" title="Chưa có kết quả" description="Chọn ràng buộc, nhập dữ liệu và nhấn Giải." />
        ) : (
          <ExtendedResultPanel response={result} loading={loading} error={error}>
            {result && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-5)' }}>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 'var(--sp-3)' }}>
                  <SummaryCard label="Tổng chi phí tối thiểu" value={totalCost ?? '—'} color="#d97706" />
                </div>

                {/* Allocation matrix */}
                {alloc && (
                  <MatrixTable
                    matrix={alloc}
                    label="Ma trận phân bổ tối ưu (cột cuối = không sử dụng nếu có)"
                    rowHeaders={srcNames}
                    colHeaders={dstNames}
                    highlightCells={highlightSet}
                  />
                )}

                {/* Unused supply by source */}
                {unusedSupply && unusedSupply.some(u => u.unusedAmount > 0) && (
                  <div className="card">
                    <div className="card-header">
                      <span style={{ fontWeight: 600, fontSize: '0.875rem' }}>📦 Lượng cung dư theo nguồn</span>
                    </div>
                    <div style={{ padding: 'var(--sp-4)' }}>
                      <table style={{ borderCollapse: 'collapse', width: '100%', fontSize: '0.875rem' }}>
                        <thead>
                          <tr>
                            <th style={thStyle}>Nguồn</th>
                            <th style={thStyle}>Lượng không sử dụng</th>
                          </tr>
                        </thead>
                        <tbody>
                          {unusedSupply.map((u, i) => (
                            <tr key={i}>
                              <td style={{ ...tdStyle, fontWeight: 600, color: 'var(--accent)' }}>{u.sourceName}</td>
                              <td style={{ ...tdStyle, fontFamily: 'var(--font-mono)', color: u.unusedAmount > 0 ? 'var(--warning)' : 'var(--text-tertiary)' }}>
                                {u.unusedAmount > 0 ? u.unusedAmount : '—'}
                              </td>
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
  padding: '8px 14px', border: '1px solid var(--border-subtle)', textAlign: 'center',
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
