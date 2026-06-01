// src/components/layout/ResultsPanel.tsx
// =========================================
// Right panel: hiển thị kết quả giải toán.

import {
  CheckCircle,
  Warning,
  ArrowsClockwise,
  Table,
  ListNumbers,
  Info,
  House,
} from '@phosphor-icons/react'
import { useState } from 'react'
import { SolutionSummary } from '@/components/results/SolutionSummary'
import { IterationPanel } from '@/components/results/IterationPanel'
import { AllocationTable } from '@/components/results/AllocationTable'
import type { SolverState, IterationResult } from '@/types/transportation'

interface ResultsPanelProps {
  state: SolverState
}

type ResultTab = 'summary' | 'table' | 'iterations'

export function ResultsPanel({ state }: ResultsPanelProps) {
  const [activeTab, setActiveTab] = useState<ResultTab>('summary')

  if (state.status === 'idle') {
    return (
      <div className="panel-right">
        <div className="panel-right-inner" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div className="empty-state">
            <div className="empty-icon">
              <Table size={22} style={{ color: 'var(--text-disabled)' }} />
            </div>
            <div>
              <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 'var(--sp-2)' }}>
                Chưa có kết quả
              </h3>
              <p style={{ fontSize: '0.875rem', color: 'var(--text-tertiary)', maxWidth: '32ch', margin: '0 auto' }}>
                Nhập dữ liệu bài toán ở panel bên trái và nhấn{' '}
                <strong style={{ color: 'var(--accent)' }}>Giải bài toán</strong>.
              </p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (state.status === 'loading') {
    return (
      <div className="panel-right">
        <div className="panel-right-inner" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div className="empty-state">
            <div className="spinner" style={{ width: 32, height: 32, borderWidth: 3 }} />
            <div>
              <p style={{ fontSize: '0.9375rem', color: 'var(--text-secondary)', fontWeight: 500 }}>
                Đang giải bài toán...
              </p>
              <p style={{ fontSize: '0.8125rem', color: 'var(--text-tertiary)' }}>
                Đang chạy thuật toán thế vị
              </p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (state.status === 'error') {
    return (
      <div className="panel-right">
        <div className="panel-right-inner">
          <div className="error-banner fade-in" style={{ maxWidth: 520 }}>
            <Warning size={18} weight="fill" style={{ flexShrink: 0, marginTop: 1 }} />
            <div>
              <div style={{ fontWeight: 600, marginBottom: 4 }}>Lỗi khi giải bài toán</div>
              <div style={{ lineHeight: 1.5 }}>{state.message}</div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Success state
  const result = state.data
  const m = result.allocationMatrix.length
  const n = (result.allocationMatrix[0] ?? []).length
  const sourceNames = result.sourceNames ?? Array.from({ length: m }, (_, i) => `S${i + 1}`)
  const destNames = result.destinationNames ?? Array.from({ length: n }, (_, j) => `D${j + 1}`)

  // Derive supply/demand from allocation
  const supply = result.allocationMatrix.map((row) => row.reduce((a, b) => a + b, 0))
  const demand = Array.from({ length: n }, (_, j) =>
    result.allocationMatrix.reduce((sum, row) => sum + (row[j] ?? 0), 0),
  )

  // Build a synthetic last iteration for the final table display
  const finalIteration: IterationResult = {
    step: -1,
    allocationMatrix: result.allocationMatrix,
    totalCost: result.totalCost,
    potentialsU: null,
    potentialsV: null,
    reducedCosts: null,
    enteringCell: null,
    leavingCell: null,
    cycle: null,
    description: '',
  }

  // If there's an optimal iteration with potentials, use it
  if (result.iterations.length > 0) {
    const lastIter = result.iterations[result.iterations.length - 1]
    if (lastIter.potentialsU) {
      Object.assign(finalIteration, lastIter, { allocationMatrix: result.allocationMatrix })
    }
  }

  // Reconstruct cost matrix from potentials (best effort)
  const costMatrix = Array.from({ length: m }, (_, i) =>
    Array.from({ length: n }, (_, j) => {
      const u = finalIteration.potentialsU?.[i]
      const vj = finalIteration.potentialsV?.[j]
      const delta = finalIteration.reducedCosts?.[i]?.[j]
      if (u !== undefined && u !== null && vj !== undefined && vj !== null) {
        if (delta !== null && delta !== undefined) return u + vj - delta
        return u + vj
      }
      return 0
    }),
  )

  return (
    <div className="panel-right" style={{ display: 'flex', flexDirection: 'column' }}>
      {/* Tab bar */}
      <div className="tabs-bar">
        <button
          type="button"
          className={`tab-btn ${activeTab === 'summary' ? 'active' : ''}`}
          onClick={() => setActiveTab('summary')}
        >
          <CheckCircle size={14} />
          Tóm tắt
        </button>
        <button
          type="button"
          className={`tab-btn ${activeTab === 'table' ? 'active' : ''}`}
          onClick={() => setActiveTab('table')}
        >
          <Table size={14} />
          Bảng phân phối
        </button>
        {result.iterations.length > 0 && (
          <button
            type="button"
            className={`tab-btn ${activeTab === 'iterations' ? 'active' : ''}`}
            onClick={() => setActiveTab('iterations')}
          >
            <ListNumbers size={14} />
            Từng bước ({result.iterations.length})
          </button>
        )}
      </div>

      {/* Panel body */}
      <div className="panel-right-inner fade-in">
        {activeTab === 'summary' && (
          <div style={{ maxWidth: 700 }}>
            <SolutionSummary result={result} />
          </div>
        )}

        {activeTab === 'table' && (
          <div>
            <div style={{ marginBottom: 'var(--sp-4)' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: 'var(--sp-1)' }}>
                Bảng phân phối tối ưu X*
              </h3>
              <p style={{ fontSize: '0.8125rem', color: 'var(--text-tertiary)' }}>
                Góc trên trái: cước phí cᵢⱼ · Giữa: luồng xᵢⱼ · Góc dưới phải: Δᵢⱼ (ô loại)
              </p>
            </div>
            <AllocationTable
              iteration={finalIteration}
              costMatrix={costMatrix}
              sourceNames={sourceNames}
              destinationNames={destNames}
              supply={supply}
              demand={demand}
            />
          </div>
        )}

        {activeTab === 'iterations' && result.iterations.length > 0 && (
          <div>
            <div style={{ marginBottom: 'var(--sp-4)' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: 'var(--sp-1)' }}>
                Chi tiết từng bước tối ưu hóa
              </h3>
              <p style={{ fontSize: '0.8125rem', color: 'var(--text-tertiary)' }}>
                Nhấn vào từng bước để xem bảng phân phối, thế vị và ma trận ước lượng Δ.
              </p>
            </div>
            <IterationPanel result={result} />
          </div>
        )}
      </div>
    </div>
  )
}
