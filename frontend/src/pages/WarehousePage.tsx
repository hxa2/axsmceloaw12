// src/pages/WarehousePage.tsx
// =============================
// Tab: Bài toán lập kho nhận hàng

import { useState, useCallback } from 'react'
import { Play, Plus, Trash } from '@phosphor-icons/react'
import { api, ApiError } from '@/api/client'
import type { ExtendedSolveResponse, WarehouseRequest, WarehouseSpec } from '@/types/extended'
import {
  ExtendedResultPanel,
  MatrixTable,
  SummaryCard,
} from '@/components/extended/ExtendedResultPanel'

function makeMatrix(m: number, n: number): number[][] {
  return Array.from({ length: m }, (_, i) => Array.from({ length: n }, (_, j) => (i + j + 1) * 3))
}

interface WarehouseEditor {
  name: string
  demandMode: 'fixed'
  amount: number
  costsFromSources: number[]
  storageCostPerUnit: number
}

function defaultWarehouse(m: number): WarehouseEditor {
  return {
    name: 'Kho mới',
    demandMode: 'fixed',
    amount: 20,
    costsFromSources: Array(m).fill(5),
    storageCostPerUnit: 0,
  }
}

export function WarehousePage() {
  const [m, setM] = useState(3)
  const [n, setN] = useState(3)
  const [baseCostMatrix, setBaseCostMatrix] = useState<number[][]>(makeMatrix(3, 3))
  const [supply, setSupply] = useState<number[]>([40, 50, 30])
  const [demand, setDemand] = useState<number[]>([30, 40, 20])
  const [warehouses, setWarehouses] = useState<WarehouseEditor[]>([defaultWarehouse(3)])

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<ExtendedSolveResponse | null>(null)

  const handleAddWarehouse = useCallback(() => {
    setWarehouses(prev => [...prev, defaultWarehouse(m)])
  }, [m])

  const handleRemoveWarehouse = useCallback((idx: number) => {
    setWarehouses(prev => prev.filter((_, i) => i !== idx))
  }, [])

  const handleWarehouseChange = useCallback(<K extends keyof WarehouseEditor>(
    idx: number, field: K, value: WarehouseEditor[K]
  ) => {
    setWarehouses(prev => prev.map((w, i) => i === idx ? { ...w, [field]: value } : w))
  }, [])

  const handleResizeM = useCallback((newM: number) => {
    setM(newM)
    setBaseCostMatrix(prev => {
      const next = makeMatrix(newM, n)
      for (let i = 0; i < Math.min(newM, prev.length); i++)
        for (let j = 0; j < Math.min(n, prev[0]?.length ?? 0); j++)
          next[i][j] = prev[i][j]
      return next
    })
    setSupply(prev => Array.from({ length: newM }, (_, i) => prev[i] ?? 10))
    setWarehouses(prev => prev.map(w => ({
      ...w,
      costsFromSources: Array.from({ length: newM }, (_, i) => w.costsFromSources[i] ?? 5)
    })))
  }, [n])

  const handleSolve = useCallback(async () => {
    setLoading(true); setError(null); setResult(null)
    try {
      const req: WarehouseRequest = {
        baseCostMatrix,
        supply,
        demand,
        warehouses: warehouses.map(w => ({
          name: w.name,
          demandMode: w.demandMode,
          amount: w.amount,
          costsFromSources: w.costsFromSources,
          storageCostPerUnit: w.storageCostPerUnit,
        } as WarehouseSpec)),
      }
      const res = await api.solveWarehouse(req)
      setResult(res)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : String(err))
    } finally {
      setLoading(false)
    }
  }, [baseCostMatrix, supply, demand, warehouses])

  const alloc = result?.solution?.allocationMatrix as number[][] | undefined
  const srcNames = result?.solution?.sourceNames as string[] ?? supply.map((_, i) => `S${i+1}`)
  const dstNames = result?.solution?.destinationNames as string[] ?? demand.map((_, j) => `D${j+1}`)
  const totalCost = result?.solution?.totalCost as number | undefined
  const warehouseUsage = result?.interpretation?.warehouseUsage as Array<{
    name: string; receivedAmount: number; targetAmount: number; incomingBySource: Array<{ sourceName: string; amount: number; totalCost: number }>
  }> | undefined
  const whIndices = result?.interpretation?.warehouseDestinationIndices as number[] ?? []

  const highlightSet = new Set<string>()
  alloc?.forEach((row, i) => row.forEach((v, j) => { if (v > 0 && !whIndices.includes(j)) highlightSet.add(`${i},${j}`) }))

  return (
    <div className="ext-page-layout">
      <aside className="ext-sidebar">
        <div className="editor-section">
          <div className="editor-section-title" style={{ color: '#7c3aed' }}>
            🏭 Lập kho nhận hàng
          </div>
          <p style={{ fontSize: '0.8125rem', color: 'var(--text-tertiary)', lineHeight: 1.5 }}>
            Kho mới được xem như điểm thu bổ sung. Chi phí = vận chuyển + lưu kho.
          </p>
        </div>

        <div className="editor-section">
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <div style={{ flex: 1 }}>
              <label className="label">Nguồn (m)</label>
              <input type="number" className="input" min={2} max={8} value={m}
                onChange={e => handleResizeM(Math.max(2, +e.target.value))}
                style={{ textAlign: 'center' }} />
            </div>
            <div style={{ flex: 1 }}>
              <label className="label">Điểm thu (n)</label>
              <input type="number" className="input" min={2} max={8} value={n}
                onChange={e => {
                  const newN = Math.max(2, +e.target.value)
                  setN(newN)
                  setBaseCostMatrix(prev => {
                    const next = makeMatrix(m, newN)
                    for (let i = 0; i < m; i++)
                      for (let j = 0; j < Math.min(newN, prev[0]?.length ?? 0); j++)
                        next[i][j] = prev[i][j]
                    return next
                  })
                  setDemand(prev => Array.from({ length: newN }, (_, j) => prev[j] ?? 10))
                }}
                style={{ textAlign: 'center' }} />
            </div>
          </div>
        </div>

        <div className="editor-section">
          <label className="label">Ma trận chi phí cơ bản cᵢⱼ</label>
          {baseCostMatrix.map((row, i) => (
            <div key={i} style={{ display: 'flex', gap: 4, marginBottom: 4 }}>
              {row.map((val, j) => (
                <input key={j} type="number" className="input input-mono" value={val}
                  style={{ width: 52, padding: '4px 6px', fontSize: '0.875rem' }}
                  onChange={e => {
                    const v = parseFloat(e.target.value) || 0
                    setBaseCostMatrix(prev => prev.map((r, ri) => ri === i ? r.map((c, ci) => ci === j ? v : c) : r))
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
                style={{ width: 60, padding: '4px 6px', fontSize: '0.875rem' }}
                onChange={e => setSupply(prev => prev.map((x, xi) => xi === i ? parseFloat(e.target.value) || 0 : x))} />
            ))}
          </div>
        </div>

        <div className="editor-section">
          <label className="label">Lượng thu bⱼ</label>
          <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
            {demand.map((v, j) => (
              <input key={j} type="number" className="input input-mono" value={v}
                style={{ width: 60, padding: '4px 6px', fontSize: '0.875rem' }}
                onChange={e => setDemand(prev => prev.map((x, xi) => xi === j ? parseFloat(e.target.value) || 0 : x))} />
            ))}
          </div>
        </div>

        {/* Warehouses */}
        <div className="editor-section">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
            <label className="label" style={{ marginBottom: 0 }}>Kho nhận hàng ({warehouses.length})</label>
            <button type="button" className="btn btn-secondary btn-sm" onClick={handleAddWarehouse}>
              <Plus size={12} /> Thêm kho
            </button>
          </div>
          {warehouses.map((wh, idx) => (
            <div key={idx} style={{
              padding: 'var(--sp-3)', border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius)', marginBottom: 8, background: 'var(--bg-inset)',
              borderLeft: '3px solid #7c3aed',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                <input className="input" value={wh.name} placeholder="Tên kho"
                  style={{ fontSize: '0.875rem', fontWeight: 600 }}
                  onChange={e => handleWarehouseChange(idx, 'name', e.target.value)} />
                <button type="button" className="btn btn-ghost btn-sm" onClick={() => handleRemoveWarehouse(idx)}
                  style={{ color: 'var(--danger)', marginLeft: 4 }}>
                  <Trash size={14} />
                </button>
              </div>
              <div style={{ display: 'flex', gap: 8, marginBottom: 6 }}>
                <div style={{ flex: 1 }}>
                  <label style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)' }}>Nhu cầu</label>
                  <input type="number" className="input input-mono" value={wh.amount}
                    style={{ fontSize: '0.875rem' }}
                    onChange={e => handleWarehouseChange(idx, 'amount', parseFloat(e.target.value) || 0)} />
                </div>
                <div style={{ flex: 1 }}>
                  <label style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)' }}>Chi phí lưu kho/đv</label>
                  <input type="number" className="input input-mono" value={wh.storageCostPerUnit}
                    style={{ fontSize: '0.875rem' }}
                    onChange={e => handleWarehouseChange(idx, 'storageCostPerUnit', parseFloat(e.target.value) || 0)} />
                </div>
              </div>
              <div>
                <label style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', marginBottom: 4, display: 'block' }}>
                  Chi phí vận chuyển từ mỗi nguồn
                </label>
                <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                  {wh.costsFromSources.map((c, si) => (
                    <div key={si}>
                      <div style={{ fontSize: '0.6875rem', textAlign: 'center', color: 'var(--text-tertiary)' }}>S{si+1}</div>
                      <input type="number" className="input input-mono" value={c}
                        style={{ width: 52, padding: '3px 6px', fontSize: '0.8125rem' }}
                        onChange={e => {
                          const v = parseFloat(e.target.value) || 0
                          handleWarehouseChange(idx, 'costsFromSources',
                            wh.costsFromSources.map((x, xi) => xi === si ? v : x))
                        }} />
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>

        <button type="button" className="btn btn-primary solve-btn" onClick={handleSolve}
          disabled={loading || warehouses.length === 0}
          style={{ backgroundColor: '#7c3aed', borderColor: '#7c3aed' }}>
          {loading ? <><span className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} /> Đang giải...</> : <><Play size={16} weight="fill" /> Tính phương án tối ưu</>}
        </button>
      </aside>

      <div className="ext-result-area">
        {!result && !loading && !error ? (
          <EmptyState icon="🏭" title="Chưa có kết quả" description="Thêm kho, nhập dữ liệu và nhấn Tính phương án." />
        ) : (
          <ExtendedResultPanel response={result} loading={loading} error={error}>
            {result && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-5)' }}>
                <SummaryCard label="Tổng chi phí tối thiểu" value={totalCost ?? '—'} color="#7c3aed" />

                {alloc && (
                  <MatrixTable matrix={alloc} label="Ma trận phân bổ tối ưu"
                    rowHeaders={srcNames} colHeaders={dstNames} highlightCells={highlightSet} />
                )}

                {/* Warehouse usage */}
                {warehouseUsage && warehouseUsage.length > 0 && (
                  <div className="card">
                    <div className="card-header">
                      <span style={{ fontWeight: 600, fontSize: '0.875rem' }}>🏭 Chi tiết kho nhận hàng</span>
                    </div>
                    <div style={{ padding: 'var(--sp-4)', display: 'flex', flexDirection: 'column', gap: 'var(--sp-4)' }}>
                      {warehouseUsage.map((wh, i) => (
                        <div key={i} style={{
                          padding: 'var(--sp-3)', borderLeft: '3px solid #7c3aed',
                          background: 'var(--bg-inset)', borderRadius: 'var(--radius)',
                        }}>
                          <div style={{ fontWeight: 600, marginBottom: 6 }}>{wh.name}</div>
                          <div style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', marginBottom: 8 }}>
                            Nhận: <strong>{wh.receivedAmount}</strong> / {wh.targetAmount}
                          </div>
                          {wh.incomingBySource.map((src, si) => (
                            <div key={si} style={{
                              fontSize: '0.8125rem', display: 'flex', justifyContent: 'space-between',
                              padding: '4px 8px', background: 'var(--bg-surface)',
                              borderRadius: 'var(--radius-sm)', marginBottom: 4,
                            }}>
                              <span>{src.sourceName} → {wh.name}: {src.amount}</span>
                              <span style={{ color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)' }}>
                                Chi phí: {src.totalCost}
                              </span>
                            </div>
                          ))}
                        </div>
                      ))}
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
