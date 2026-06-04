// src/pages/AssignmentPage.tsx
// ==============================
// Tab: Bài toán phân việc (Hungarian Algorithm)

import { useState, useCallback } from 'react'
import { Play, ArrowRight } from '@phosphor-icons/react'
import { api, ApiError } from '@/api/client'
import type { ExtendedSolveResponse, AssignmentRequest, AssignmentEntry, StepInfo } from '@/types/extended'
import { ExtendedResultPanel, SummaryCard } from '@/components/extended/ExtendedResultPanel'

function makeMatrix(n: number): number[][] {
  return Array.from({ length: n }, (_, i) => Array.from({ length: n }, (_, j) => (i * n + j + 1) * 2 % 13 + 1))
}

export function AssignmentPage() {
  const [nWorkers, setNWorkers] = useState(4)
  const [nJobs, setNJobs] = useState(4)
  const [matrix, setMatrix] = useState<number[][]>(makeMatrix(4))
  const [objective, setObjective] = useState<'minimize' | 'maximize'>('minimize')
  const [workerNames, setWorkerNames] = useState<string[]>(['', '', '', ''])
  const [jobNames, setJobNames] = useState<string[]>(['', '', '', ''])

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<ExtendedSolveResponse | null>(null)
  const [activeStep, setActiveStep] = useState<number | null>(null)

  const handleResizeWorkers = useCallback((newM: number) => {
    setNWorkers(newM)
    setMatrix(prev => Array.from({ length: newM }, (_, i) => prev[i] ?? Array(nJobs).fill(0)))
    setWorkerNames(prev => Array.from({ length: newM }, (_, i) => prev[i] ?? ''))
  }, [nJobs])

  const handleResizeJobs = useCallback((newN: number) => {
    setNJobs(newN)
    setMatrix(prev => prev.map(row => Array.from({ length: newN }, (_, j) => row[j] ?? 0)))
    setJobNames(prev => Array.from({ length: newN }, (_, j) => prev[j] ?? ''))
  }, [])

  const handleSolve = useCallback(async () => {
    setLoading(true); setError(null); setResult(null); setActiveStep(null)
    try {
      const req: AssignmentRequest = {
        matrix,
        objective,
        workerNames: workerNames.map((n, i) => n || `Người ${i + 1}`),
        jobNames: jobNames.map((n, j) => n || `Việc ${j + 1}`),
      }
      const res = await api.solveAssignment(req)
      setResult(res)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : String(err))
    } finally {
      setLoading(false)
    }
  }, [matrix, objective, workerNames, jobNames])

  const assignments = result?.solution?.assignments as AssignmentEntry[] | undefined
  const realAssignments = result?.interpretation?.realAssignments as AssignmentEntry[] | undefined
  const objValue = result?.solution?.objectiveValue as number | undefined
  const assignMatrix = result?.solution?.assignmentMatrix as number[][] | undefined
  const steps = result?.steps as StepInfo[] | undefined
  const wNames = realAssignments?.map(a => a.workerName) ?? []
  const jNames = realAssignments?.map(a => a.jobName) ?? []

  const isMaximize = objective === 'maximize'

  return (
    <div className="ext-page-layout">
      <aside className="ext-sidebar">
        <div className="editor-section">
          <div className="editor-section-title" style={{ color: '#0891b2' }}>
            👥 Bài toán phân việc
          </div>
          <p style={{ fontSize: '0.8125rem', color: 'var(--text-tertiary)', lineHeight: 1.5 }}>
            Giải bài toán phân công bằng <strong>Hungarian Algorithm</strong>. Hỗ trợ ma trận không vuông.
          </p>
        </div>

        {/* Objective */}
        <div className="editor-section">
          <label className="label">Mục tiêu</label>
          <div style={{ display: 'flex', gap: 8 }}>
            {(['minimize', 'maximize'] as const).map(obj => (
              <label key={obj} style={{
                flex: 1, display: 'flex', gap: 8, alignItems: 'center',
                padding: '8px 10px', borderRadius: 'var(--radius)',
                background: objective === obj ? 'rgba(8,145,178,0.08)' : 'var(--bg-inset)',
                border: `1px solid ${objective === obj ? '#0891b2' : 'var(--border-subtle)'}`,
                cursor: 'pointer', fontSize: '0.875rem',
              }}>
                <input type="radio" name="objective" value={obj}
                  checked={objective === obj} onChange={() => setObjective(obj)}
                  style={{ accentColor: '#0891b2' }} />
                {obj === 'minimize' ? '↓ Tối thiểu' : '↑ Tối đa'}
              </label>
            ))}
          </div>
        </div>

        {/* Size */}
        <div className="editor-section">
          <div style={{ display: 'flex', gap: 8 }}>
            <div style={{ flex: 1 }}>
              <label className="label">Người (m)</label>
              <input type="number" className="input" min={2} max={8} value={nWorkers}
                onChange={e => handleResizeWorkers(Math.max(2, Math.min(8, +e.target.value)))}
                style={{ textAlign: 'center' }} />
            </div>
            <div style={{ flex: 1 }}>
              <label className="label">Việc (n)</label>
              <input type="number" className="input" min={2} max={8} value={nJobs}
                onChange={e => handleResizeJobs(Math.max(2, Math.min(8, +e.target.value)))}
                style={{ textAlign: 'center' }} />
            </div>
          </div>
        </div>

        {/* Worker names */}
        <div className="editor-section">
          <label className="label">Tên người (tuỳ chọn)</label>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {workerNames.map((n, i) => (
              <input key={i} className="input" value={n} placeholder={`Người ${i+1}`}
                style={{ fontSize: '0.875rem' }}
                onChange={e => setWorkerNames(prev => prev.map((x, xi) => xi === i ? e.target.value : x))} />
            ))}
          </div>
        </div>

        {/* Job names */}
        <div className="editor-section">
          <label className="label">Tên việc (tuỳ chọn)</label>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {jobNames.map((n, j) => (
              <input key={j} className="input" value={n} placeholder={`Việc ${j+1}`}
                style={{ fontSize: '0.875rem' }}
                onChange={e => setJobNames(prev => prev.map((x, xi) => xi === j ? e.target.value : x))} />
            ))}
          </div>
        </div>

        {/* Matrix */}
        <div className="editor-section">
          <label className="label">Ma trận {isMaximize ? 'lợi nhuận' : 'chi phí'}</label>
          <div style={{ overflowX: 'auto' }}>
            {/* Column headers */}
            <div style={{ display: 'flex', gap: 4, marginBottom: 4 }}>
              <div style={{ width: 32 }} />
              {Array.from({ length: nJobs }, (_, j) => (
                <div key={j} style={{ width: 52, textAlign: 'center', fontSize: '0.75rem', color: '#0891b2', fontWeight: 600 }}>
                  {jobNames[j] || `V${j+1}`}
                </div>
              ))}
            </div>
            {matrix.slice(0, nWorkers).map((row, i) => (
              <div key={i} style={{ display: 'flex', gap: 4, marginBottom: 4, alignItems: 'center' }}>
                <div style={{ width: 32, fontSize: '0.75rem', color: '#0891b2', fontWeight: 600, textAlign: 'center' }}>
                  {workerNames[i] ? workerNames[i].slice(0, 3) : `N${i+1}`}
                </div>
                {row.slice(0, nJobs).map((val, j) => {
                  const isAssigned = assignMatrix?.[i]?.[j] === 1
                  return (
                    <input key={j} type="number" className="input input-mono" value={val}
                      style={{
                        width: 52, padding: '4px 6px', fontSize: '0.875rem',
                        background: isAssigned ? 'rgba(8,145,178,0.12)' : undefined,
                        borderColor: isAssigned ? '#0891b2' : undefined,
                        fontWeight: isAssigned ? 700 : undefined,
                      }}
                      onChange={e => {
                        const v = parseFloat(e.target.value) || 0
                        setMatrix(prev => prev.map((r, ri) => ri === i ? r.map((c, ci) => ci === j ? v : c) : r))
                      }} />
                  )
                })}
              </div>
            ))}
          </div>
        </div>

        <button type="button" className="btn btn-primary solve-btn" onClick={handleSolve} disabled={loading}
          style={{ backgroundColor: '#0891b2', borderColor: '#0891b2' }}>
          {loading ? <><span className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} /> Đang giải...</> : <><Play size={16} weight="fill" /> Giải phân việc</>}
        </button>
      </aside>

      <div className="ext-result-area">
        {!result && !loading && !error ? (
          <EmptyState icon="👥" title="Chưa có kết quả" description="Nhập ma trận và nhấn Giải phân việc." />
        ) : (
          <ExtendedResultPanel response={result} loading={loading} error={error}>
            {result && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-5)' }}>
                {/* KPI */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 'var(--sp-3)' }}>
                  <SummaryCard
                    label={isMaximize ? 'Tổng lợi nhuận tối đa' : 'Tổng chi phí tối thiểu'}
                    value={objValue ?? '—'}
                    color="#0891b2"
                  />
                  {realAssignments && (
                    <SummaryCard label="Số phân công" value={realAssignments.length} color="#7c3aed" />
                  )}
                </div>

                {/* Assignment list */}
                {realAssignments && realAssignments.length > 0 && (
                  <div className="card">
                    <div className="card-header">
                      <span style={{ fontWeight: 600, fontSize: '0.875rem' }}>📋 Phân công tối ưu</span>
                    </div>
                    <div style={{ padding: 'var(--sp-4)', display: 'flex', flexDirection: 'column', gap: 'var(--sp-2)' }}>
                      {realAssignments.map((a, i) => (
                        <div key={i} style={{
                          display: 'flex', alignItems: 'center', gap: 'var(--sp-3)',
                          padding: 'var(--sp-3)', background: 'var(--bg-inset)',
                          borderRadius: 'var(--radius)', border: '1px solid var(--border-subtle)',
                        }}>
                          <div style={{ fontWeight: 600, color: '#0891b2', flex: 1 }}>{a.workerName}</div>
                          <ArrowRight size={16} style={{ color: 'var(--text-tertiary)', flexShrink: 0 }} />
                          <div style={{ fontWeight: 600, color: 'var(--text-primary)', flex: 1 }}>{a.jobName}</div>
                          <div style={{
                            fontFamily: 'var(--font-mono)', fontWeight: 700,
                            color: isMaximize ? '#16a34a' : '#d97706',
                            background: isMaximize ? 'var(--success-muted)' : 'var(--warning-muted)',
                            padding: '2px 10px', borderRadius: 99, fontSize: '0.875rem',
                          }}>
                            {a.value}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Steps walkthrough */}
                {steps && steps.length > 0 && (
                  <div className="card">
                    <div className="card-header">
                      <span style={{ fontWeight: 600, fontSize: '0.875rem' }}>🔢 Chi tiết Hungarian Algorithm ({steps.length} bước)</span>
                    </div>
                    <div style={{ padding: 'var(--sp-4)', display: 'flex', flexDirection: 'column', gap: 'var(--sp-2)' }}>
                      {steps.map((step, i) => (
                        <div key={i}>
                          <button
                            type="button"
                            onClick={() => setActiveStep(activeStep === i ? null : i)}
                            style={{
                              width: '100%', textAlign: 'left', padding: 'var(--sp-3)',
                              background: activeStep === i ? 'rgba(8,145,178,0.08)' : 'var(--bg-inset)',
                              border: `1px solid ${activeStep === i ? '#0891b2' : 'var(--border-subtle)'}`,
                              borderRadius: 'var(--radius)', cursor: 'pointer',
                              display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start',
                              gap: 8,
                            }}
                          >
                            <div>
                              <div style={{ fontWeight: 600, fontSize: '0.8125rem', color: '#0891b2', marginBottom: 2 }}>
                                Bước {i + 1}: {STEP_LABELS[step.type] ?? step.type}
                              </div>
                              <div style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>{step.description}</div>
                            </div>
                            <span style={{ color: 'var(--text-tertiary)', flexShrink: 0 }}>
                              {activeStep === i ? '▲' : '▼'}
                            </span>
                          </button>

                          {activeStep === i && step.matrixAfter && (
                            <div style={{ marginTop: 8, overflowX: 'auto' }}>
                              <HungarianMatrix
                                matrix={step.matrixAfter as number[][]}
                                details={step.details}
                                stepType={step.type}
                                nWorkers={nWorkers}
                                nJobs={nJobs}
                              />
                            </div>
                          )}
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

const STEP_LABELS: Record<string, string> = {
  max_to_min: 'Chuyển Max → Min',
  pad_to_square: 'Bổ sung dummy',
  row_reduction: 'Trừ hàng (row reduction)',
  column_reduction: 'Trừ cột (column reduction)',
  cover_zeros: 'Che phủ số 0',
  adjust_matrix: 'Điều chỉnh ma trận',
  select_independent_zeros: 'Chọn số 0 độc lập',
}

function HungarianMatrix({
  matrix, details, stepType, nWorkers, nJobs
}: {
  matrix: number[][]
  details?: Record<string, unknown>
  stepType: string
  nWorkers: number
  nJobs: number
}) {
  const n = matrix.length
  const rowLines = new Set<number>((details?.rowLines as number[]) ?? [])
  const colLines = new Set<number>((details?.columnLines as number[]) ?? [])
  const selected = new Set<string>(
    ((details?.selectedCells as Array<{ row: number; col: number }>) ?? []).map(c => `${c.row},${c.col}`)
  )

  const EPS = 1e-9

  return (
    <table style={{ borderCollapse: 'collapse', fontSize: '0.8125rem' }}>
      <tbody>
        {matrix.map((row, i) => {
          const isRowLine = rowLines.has(i)
          return (
            <tr key={i}>
              {row.map((val, j) => {
                const isColLine = colLines.has(j)
                const isSelected = selected.has(`${i},${j}`)
                const isZero = Math.abs(val) < EPS
                const isDummy = i >= nWorkers || j >= nJobs
                return (
                  <td key={j} style={{
                    padding: '6px 10px', textAlign: 'center', minWidth: 48,
                    border: '1px solid var(--border-subtle)',
                    background: isSelected
                      ? 'rgba(8,145,178,0.2)'
                      : isDummy ? 'var(--bg-inset)'
                      : isZero && !isRowLine && !isColLine ? 'rgba(22,163,74,0.08)'
                      : isRowLine && isColLine ? 'rgba(220,38,38,0.12)'
                      : isRowLine || isColLine ? 'rgba(217,119,6,0.08)'
                      : 'var(--bg-surface)',
                    fontFamily: 'var(--font-mono)',
                    fontWeight: isSelected ? 700 : isZero ? 600 : 400,
                    color: isSelected ? '#0891b2'
                      : isDummy ? 'var(--text-disabled)'
                      : isZero ? '#16a34a' : 'var(--text-primary)',
                    borderTop: isRowLine ? '2px solid var(--warning)' : undefined,
                    borderBottom: isRowLine ? '2px solid var(--warning)' : undefined,
                    borderLeft: isColLine ? '2px solid var(--warning)' : undefined,
                    borderRight: isColLine ? '2px solid var(--warning)' : undefined,
                    outline: isSelected ? '2px solid #0891b2' : undefined,
                  }}>
                    {isSelected ? `★${val}` : val}
                  </td>
                )
              })}
            </tr>
          )
        })}
      </tbody>
    </table>
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
