// src/pages/TransportationMaxPage.tsx
// =====================================
// Tab: Bài toán vận tải dạng Max (tối đa lợi nhuận)

import { useState, useCallback } from 'react'
import { Play, Info } from '@phosphor-icons/react'
import { api, ApiError } from '@/api/client'
import type { ExtendedSolveResponse, MaxTransportRequest } from '@/types/extended'
import {
  ExtendedResultPanel,
  MatrixTable,
  SummaryCard,
} from '@/components/extended/ExtendedResultPanel'

const DEFAULT_M = 3
const DEFAULT_N = 3

function makeMatrix(m: number, n: number, fill = 0): number[][] {
  return Array.from({ length: m }, () => Array(n).fill(fill))
}

export function TransportationMaxPage() {
  const [m, setM] = useState(DEFAULT_M)
  const [n, setN] = useState(DEFAULT_N)
  const [profitMatrix, setProfitMatrix] = useState<number[][]>(makeMatrix(DEFAULT_M, DEFAULT_N, 5))
  const [supply, setSupply] = useState<number[]>([30, 40, 30])
  const [demand, setDemand] = useState<number[]>([20, 30, 50])

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<ExtendedSolveResponse | null>(null)

  const handleResize = useCallback((newM: number, newN: number) => {
    setM(newM); setN(newN)
    setProfitMatrix(prev => {
      const next = makeMatrix(newM, newN, 0)
      for (let i = 0; i < Math.min(newM, prev.length); i++)
        for (let j = 0; j < Math.min(newN, prev[0]?.length ?? 0); j++)
          next[i][j] = prev[i][j]
      return next
    })
    setSupply(prev => Array.from({ length: newM }, (_, i) => prev[i] ?? 0))
    setDemand(prev => Array.from({ length: newN }, (_, j) => prev[j] ?? 0))
  }, [])

  const handleSolve = useCallback(async () => {
    setLoading(true); setError(null); setResult(null)
    try {
      const req: MaxTransportRequest = { profitMatrix, supply, demand }
      const res = await api.solveMax(req)
      setResult(res)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : String(err))
    } finally {
      setLoading(false)
    }
  }, [profitMatrix, supply, demand])

  const pMax = result
    ? (result.transformations[0]?.details?.pMax as number | undefined)
    : undefined
  const alloc = result?.solution?.allocationMatrix as number[][] | undefined
  const profitOrig = result?.originalProblem?.profitMatrix as number[][] | undefined
  const transformedCost = result?.transformedProblem?.costMatrix as number[][] | undefined
  const srcNames = (result?.solution?.sourceNames as string[] | undefined) ?? supply.map((_, i) => `S${i+1}`)
  const dstNames = (result?.solution?.destinationNames as string[] | undefined) ?? demand.map((_, j) => `D${j+1}`)
  const totalProfit = result?.solution?.totalProfit as number | undefined
  const transformedCostTotal = result?.solution?.transformedTotalCost as number | undefined

  // highlight allocated cells
  const highlightSet = new Set<string>()
  alloc?.forEach((row, i) => row.forEach((v, j) => { if (v > 0) highlightSet.add(`${i},${j}`) }))

  return (
    <div className="ext-page-layout">
      {/* ── Sidebar ── */}
      <aside className="ext-sidebar">
        <div className="editor-section">
          <div className="editor-section-title" style={{ color: '#16a34a' }}>
            📈 Vận tải dạng Max
          </div>
          <p style={{ fontSize: '0.8125rem', color: 'var(--text-tertiary)', lineHeight: 1.5 }}>
            Tối đa hoá lợi nhuận bằng cách quy đổi: <code>c'ᵢⱼ = P_max − pᵢⱼ</code>
          </p>
        </div>

        {/* Size */}
        <div className="editor-section">
          <label className="label">Kích thước ma trận</label>
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

        {/* Profit matrix */}
        <div className="editor-section">
          <label className="label">Ma trận lợi nhuận pᵢⱼ</label>
          <div style={{ overflowX: 'auto' }}>
            {profitMatrix.map((row, i) => (
              <div key={i} style={{ display: 'flex', gap: 4, marginBottom: 4 }}>
                {row.map((val, j) => (
                  <input key={j} type="number" className="input input-mono"
                    value={val} style={{ width: 56, padding: '4px 6px', fontSize: '0.875rem' }}
                    onChange={e => {
                      const v = parseFloat(e.target.value) || 0
                      setProfitMatrix(prev => prev.map((r, ri) => ri === i ? r.map((c, ci) => ci === j ? v : c) : r))
                    }} />
                ))}
              </div>
            ))}
          </div>
        </div>

        {/* Supply */}
        <div className="editor-section">
          <label className="label">Lượng phát aᵢ</label>
          <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
            {supply.map((v, i) => (
              <input key={i} type="number" className="input input-mono"
                value={v} style={{ width: 64, padding: '4px 6px', fontSize: '0.875rem' }}
                onChange={e => setSupply(prev => prev.map((x, xi) => xi === i ? parseFloat(e.target.value) || 0 : x))} />
            ))}
          </div>
        </div>

        {/* Demand */}
        <div className="editor-section">
          <label className="label">Lượng thu bⱼ</label>
          <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
            {demand.map((v, j) => (
              <input key={j} type="number" className="input input-mono"
                value={v} style={{ width: 64, padding: '4px 6px', fontSize: '0.875rem' }}
                onChange={e => setDemand(prev => prev.map((x, xi) => xi === j ? parseFloat(e.target.value) || 0 : x))} />
            ))}
          </div>
        </div>

        <button type="button" className="btn btn-primary solve-btn" onClick={handleSolve} disabled={loading}
          style={{ backgroundColor: '#16a34a', borderColor: '#16a34a' }}>
          {loading ? <><span className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} /> Đang giải...</> : <><Play size={16} weight="fill" /> Tối đa lợi nhuận</>}
        </button>
      </aside>

      {/* ── Result Panel ── */}
      <div className="ext-result-area">
        {!result && !loading && !error ? (
          <EmptyState icon="📈" title="Chưa có kết quả" description="Nhập ma trận lợi nhuận và nhấn Tối đa lợi nhuận." />
        ) : (
          <ExtendedResultPanel response={result} loading={loading} error={error}>
            {result && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-5)' }}>
                {/* KPIs */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 'var(--sp-3)' }}>
                  <SummaryCard label="Tổng lợi nhuận tối đa" value={totalProfit ?? '—'} color="#16a34a" />
                  {pMax !== undefined && <SummaryCard label="P_max" value={pMax} color="var(--accent)" subtitle="Lợi nhuận cao nhất trong ma trận" />}
                  {transformedCostTotal !== undefined && <SummaryCard label="Chi phí quy đổi" value={transformedCostTotal} color="var(--text-tertiary)" subtitle="Chỉ để tham khảo" />}
                </div>

                {/* Profit matrix original */}
                {profitOrig && (
                  <MatrixTable matrix={profitOrig} label="Ma trận lợi nhuận gốc pᵢⱼ"
                    rowHeaders={srcNames} colHeaders={dstNames}
                    highlightCells={highlightSet}
                    colSuffix={supply.map(String)} rowSuffix={demand.map(String)} />
                )}

                {/* Transformed cost matrix */}
                {transformedCost && pMax !== undefined && (
                  <MatrixTable matrix={transformedCost} label={`Ma trận chi phí quy đổi c'ᵢⱼ = ${pMax} − pᵢⱼ`}
                    rowHeaders={srcNames} colHeaders={dstNames}
                    colSuffix={supply.map(String)} rowSuffix={demand.map(String)} />
                )}

                {/* Allocation matrix */}
                {alloc && (
                  <MatrixTable matrix={alloc} label="Ma trận phân bổ tối ưu xᵢⱼ"
                    rowHeaders={srcNames} colHeaders={dstNames}
                    highlightCells={highlightSet} />
                )}
              </div>
            )}
          </ExtendedResultPanel>
        )}
      </div>
    </div>
  )
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
