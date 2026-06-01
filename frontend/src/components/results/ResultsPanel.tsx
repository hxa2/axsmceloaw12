// src/components/results/ResultsPanel.tsx
// =======================================
// Panel hiển thị kết quả chính, bao gồm cả Walkthrough UI.

import { memo } from 'react'
import { CheckCircle, Warning, Table, Plus, Minus, ArrowsVertical, ArrowsHorizontal, PresentationChart } from '@phosphor-icons/react'
import type { SolverState, ProblemEditorState } from '@/types/transportation'
import { AlgorithmWalkthrough } from './AlgorithmWalkthrough'
import { MatrixStage } from './MatrixStage'
import { TransformWrapper, TransformComponent } from 'react-zoom-pan-pinch'
import { MagnifyingGlassPlus, MagnifyingGlassMinus, CornersOut } from '@phosphor-icons/react'
import { resizeMatrix, resizeVector } from '@/utils/matrix'

interface ResultsPanelProps {
  state: SolverState
  editorState: ProblemEditorState
  setEditorState: React.Dispatch<React.SetStateAction<ProblemEditorState>>
  presentationMode: boolean
  togglePresentationMode: () => void
}

export const ResultsPanel = memo(function ResultsPanel({
  state,
  editorState,
  setEditorState,
  presentationMode,
  togglePresentationMode,
}: ResultsPanelProps) {
  const handleCostChange = (i: number, j: number, val: string) => {
    const newMatrix = editorState.costMatrix.map((row, ri) => ri === i ? row.map((cell, ci) => (ci === j ? val : cell)) : row)
    setEditorState({ ...editorState, costMatrix: newMatrix })
  }

  const handleSupplyChange = (i: number, val: string) => {
    const newSupply = editorState.supply.map((v, idx) => (idx === i ? val : v))
    setEditorState({ ...editorState, supply: newSupply })
  }

  const handleDemandChange = (j: number, val: string) => {
    const newDemand = editorState.demand.map((v, idx) => (idx === j ? val : v))
    setEditorState({ ...editorState, demand: newDemand })
  }

  const setM = (newM: number) => {
    newM = Math.max(2, Math.min(10, newM))
    if (newM === editorState.supply.length) return
    setEditorState(s => ({
      ...s,
      costMatrix: resizeMatrix(s.costMatrix, newM, s.demand.length),
      supply: resizeVector(s.supply, newM),
      sourceNames: resizeVector(s.sourceNames, newM).map((v, i) => v || `S${i + 1}`),
    }))
  }

  const setN = (newN: number) => {
    newN = Math.max(2, Math.min(10, newN))
    if (newN === editorState.demand.length) return
    setEditorState(s => ({
      ...s,
      costMatrix: resizeMatrix(s.costMatrix, s.supply.length, newN),
      demand: resizeVector(s.demand, newN),
      destinationNames: resizeVector(s.destinationNames, newN).map((v, j) => v || `D${j + 1}`),
    }))
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>, rowIdx: number | 'demand' | 'supply', colIdx: number | 'supply') => {
    if (!['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Enter'].includes(e.key)) return
    e.preventDefault()
    const id = (r: number | 'demand' | 'supply', c: number | 'supply') => `cell-${r}-${c}`
    let nextId: string | null = null
    const isNumber = typeof rowIdx === 'number' && typeof colIdx === 'number'
    const m = editorState.supply.length
    if (isNumber) {
      const ri = rowIdx as number
      const ci = colIdx as number
      if (e.key === 'ArrowRight' || e.key === 'Enter') nextId = id(ri, ci + 1) ?? id(ri, 'supply')
      if (e.key === 'ArrowLeft') nextId = ci > 0 ? id(ri, ci - 1) : null
      if (e.key === 'ArrowDown') nextId = ri < m - 1 ? id(ri + 1, ci) : id('demand', ci)
      if (e.key === 'ArrowUp') nextId = ri > 0 ? id(ri - 1, ci) : null
    }
    if (nextId) {
      const el = document.getElementById(nextId)
      if (el) { (el as HTMLInputElement).focus(); (el as HTMLInputElement).select() }
    }
  }

  if (state.status === 'idle') {
    const m = editorState.supply.length
    const n = editorState.demand.length
    return (
      <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
        {/* Topbar Dummy (To match Walkthrough UI) */}
        <div style={{ padding: 'var(--sp-4) var(--sp-6)', borderBottom: '1px solid var(--border-subtle)', background: 'var(--bg-surface)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-3)' }}>
            <Table size={20} weight="fill" style={{ color: 'var(--accent)' }} />
            <h3 style={{ margin: 0, fontSize: '1.125rem' }}>Ma trận cước phí & ràng buộc</h3>
          </div>
        </div>

        {/* Main Content Area */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-4)', flex: 1, minHeight: 0, padding: presentationMode ? 'var(--sp-6)' : 'var(--sp-4)' }}>
          {/* Top: Matrix View with Zoom/Pan */}
          <div style={{ 
            background: 'var(--bg-surface)', 
            borderRadius: 'var(--radius-lg)', 
            border: '1px solid var(--border-subtle)',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
            flex: 1
          }}>
            <TransformWrapper initialScale={1} minScale={0.5} maxScale={3} centerOnInit wheel={{ step: 0.1 }} panning={{ excluded: ['input', '.nodrag', 'button'] }}>
              {({ zoomIn, zoomOut, resetTransform, zoomToElement }) => (
                <>
                  <div style={{ display: 'flex', gap: 'var(--sp-2)', padding: 'var(--sp-2)', background: 'var(--bg-inset)', borderBottom: '1px solid var(--border-subtle)' }}>
                    <button type="button" className="btn btn-secondary btn-icon" onClick={() => zoomIn()} title="Phóng to">
                      <MagnifyingGlassPlus size={16} />
                    </button>
                    <button type="button" className="btn btn-secondary btn-icon" onClick={() => zoomOut()} title="Thu nhỏ">
                      <MagnifyingGlassMinus size={16} />
                    </button>
                    <button type="button" className="btn btn-secondary btn-icon" onClick={() => zoomToElement('matrix-stage-zoom-target')} title="Mặc định">
                      <CornersOut size={16} />
                    </button>
                    <div style={{ marginLeft: 'auto', fontSize: '0.75rem', color: 'var(--text-tertiary)', alignSelf: 'center', paddingRight: 'var(--sp-2)' }}>
                      Cuộn chuột để zoom, kéo thả để di chuyển
                    </div>
                  </div>
                  
                  <TransformComponent 
                    wrapperStyle={{ width: '100%', height: '100%' }}
                    contentStyle={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 'var(--sp-6)' }}
                  >
                    <div id="matrix-stage-zoom-target" style={{ padding: '3rem', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <MatrixStage
                        costMatrix={editorState.costMatrix}
                        supply={editorState.supply}
                        demand={editorState.demand}
                        sourceNames={editorState.sourceNames}
                        destNames={editorState.destinationNames}
                        presentationMode={presentationMode}
                        editable={true}
                        onCostChange={handleCostChange}
                        onSupplyChange={handleSupplyChange}
                        onDemandChange={handleDemandChange}
                        onKeyDown={handleKeyDown}
                      />
                    </div>
                  </TransformComponent>
                </>
              )}
            </TransformWrapper>
          </div>
          
          {/* Bottom: Idle Explainer / Controls */}
          <div style={{ 
            background: 'var(--bg-surface)', 
            borderRadius: 'var(--radius-lg)', 
            border: '1px solid var(--border-subtle)',
            boxShadow: 'var(--shadow-sm)',
            flexShrink: 0,
            minHeight: presentationMode ? '250px' : '200px',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'auto'
          }}>
            <div style={{ padding: 'var(--sp-4) var(--sp-6)', borderBottom: '1px solid var(--border-subtle)', background: 'var(--bg-inset)', display: 'flex', alignItems: 'center', gap: 'var(--sp-3)', position: 'sticky', top: 0, zIndex: 10 }}>
              <div className="badge badge-accent" style={{ textTransform: 'uppercase', fontSize: '0.75rem', fontWeight: 700 }}>
                SETUP
              </div>
              <h3 style={{ margin: 0, fontSize: presentationMode ? '1.25rem' : '1.125rem' }}>
                Khởi tạo dữ liệu
              </h3>
            </div>
            <div style={{ padding: 'var(--sp-5) var(--sp-6)', display: 'flex', flexDirection: 'column', gap: 'var(--sp-4)' }}>
              <p style={{ margin: 0, color: 'var(--text-secondary)' }}>Nhập cước phí, lượng phát và lượng thu vào bảng phía trên. Sử dụng mũi tên để di chuyển giữa các ô.</p>
              
              <div style={{ display: 'flex', gap: 'var(--sp-6)', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-2)' }}>
                  <span style={{ fontSize: '0.875rem', color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)' }}>m (hàng)</span>
                  <div style={{ display: 'flex', alignItems: 'center', background: 'var(--bg-inset)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius)' }}>
                    <button className="btn btn-ghost btn-sm btn-icon" onClick={() => setM(m - 1)} disabled={m <= 2}><Minus size={12} /></button>
                    <span style={{ fontSize: '0.875rem', fontWeight: 600, width: 20, textAlign: 'center' }}>{m}</span>
                    <button className="btn btn-ghost btn-sm btn-icon" onClick={() => setM(m + 1)} disabled={m >= 10}><Plus size={12} /></button>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-2)' }}>
                  <span style={{ fontSize: '0.875rem', color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)' }}>n (cột)</span>
                  <div style={{ display: 'flex', alignItems: 'center', background: 'var(--bg-inset)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius)' }}>
                    <button className="btn btn-ghost btn-sm btn-icon" onClick={() => setN(n - 1)} disabled={n <= 2}><Minus size={12} /></button>
                    <span style={{ fontSize: '0.875rem', fontWeight: 600, width: 20, textAlign: 'center' }}>{n}</span>
                    <button className="btn btn-ghost btn-sm btn-icon" onClick={() => setN(n + 1)} disabled={n >= 10}><Plus size={12} /></button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (state.status === 'loading') {
    return (
      <div style={{ padding: 'var(--sp-8)', display: 'flex', flexDirection: 'column', gap: 'var(--sp-4)' }}>
        <div className="skeleton" style={{ height: 120 }} />
        <div className="skeleton" style={{ height: 400 }} />
      </div>
    )
  }

  if (state.status === 'error') {
    return (
      <div style={{ padding: 'var(--sp-8)' }}>
        <div className="error-banner" style={{ fontSize: '1rem', padding: 'var(--sp-4)' }}>
          <Warning size={24} weight="fill" style={{ flexShrink: 0, marginTop: 2 }} />
          <div>
            <h4 style={{ marginBottom: 'var(--sp-1)' }}>Lỗi giải bài toán</h4>
            <p style={{ margin: 0 }}>{state.message}</p>
          </div>
        </div>
      </div>
    )
  }

  // Success state
  const { data, request } = state

  // Trong trường hợp solveFromFile, request có thể chưa có đủ chi tiết hiển thị, nhưng hooks đã dummy
  if (!request) {
     return <div style={{ padding: 'var(--sp-8)' }}>Không có thông tin bài toán gốc.</div>
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Cảnh báo (nếu có) */}
      {data.warnings.length > 0 && (
        <div style={{ padding: 'var(--sp-4) var(--sp-4) 0' }}>
          <div className="warning-banner">
            <Warning size={20} weight="fill" />
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              {data.warnings.map((w, i) => (
                <span key={i}>{w}</span>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Main Walkthrough UI */}
      <div style={{ flex: 1, padding: presentationMode ? 'var(--sp-6)' : 'var(--sp-4)', minHeight: 0 }}>
        <AlgorithmWalkthrough 
          request={request}
          response={data}
          presentationMode={presentationMode}
          togglePresentationMode={togglePresentationMode}
        />
      </div>
    </div>
  )
})
