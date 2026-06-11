// src/App.tsx
// ============
// Root component với tab system cho 6 loại bài toán.

import { useState, useCallback } from 'react'
import { Sidebar } from './components/layout/Sidebar'
import { ResultsPanel } from './components/results/ResultsPanel'
import { ProblemTabBar } from './components/extended/ProblemTabBar'
import { TransportationMaxPage } from './pages/TransportationMaxPage'
import { ForbiddenCellsPage } from './pages/ForbiddenCellsPage'
import { InequalityPage } from './pages/InequalityPage'
import { WarehousePage } from './pages/WarehousePage'
import { AssignmentPage } from './pages/AssignmentPage'
import { useSolver } from './hooks/useSolver'
import { createDefaultEditorState } from './utils/matrix'
import type { ProblemEditorState } from './types/transportation'
import type { ProblemTab } from './types/extended'
import { Calculator } from '@phosphor-icons/react'
import { clsx } from 'clsx'
import './App.css'

function App() {
  const { state, solve, reset } = useSolver()
  const [problemTab, setProblemTab] = useState<ProblemTab>('basic')

  // Hoist editorState so it persists across tab switches back to basic
  const [editorState, setEditorState] = useState<ProblemEditorState>(
    () => createDefaultEditorState(3, 4)
  )

  // Presentation mode chỉ dùng cho tab basic
  const [presentationMode, setPresentationMode] = useState(false)

  const togglePresentationMode = useCallback(() => {
    setPresentationMode(prev => {
      const next = !prev
      if (next) {
        document.body.classList.add('presentation-mode')
      } else {
        document.body.classList.remove('presentation-mode')
      }
      return next
    })
  }, [])

  const handleTabChange = useCallback((tab: ProblemTab) => {
    // Khi chuyển tab, thoát presentation mode
    if (tab !== 'basic' && presentationMode) {
      setPresentationMode(false)
      document.body.classList.remove('presentation-mode')
    }
    setProblemTab(tab)
  }, [presentationMode])

  const isBasicTab = problemTab === 'basic'

  return (
    <div className={clsx('app', { 'presentation-mode': presentationMode })}>
      {/* Topbar */}
      <header className="topbar">
        <div className="topbar-brand">
          <div className="topbar-brand-icon">
            <Calculator size={16} weight="bold" />
          </div>
          Bài Toán Vận Tải
        </div>
        <div className="topbar-sep" />

        {/* Problem Tab Bar */}
        <div style={{ flex: 1, display: 'flex', alignItems: 'flex-end', paddingBottom: 0 }}>
          <ProblemTabBar activeTab={problemTab} onChange={handleTabChange} />
        </div>

        <div className="topbar-actions">
          {isBasicTab && state.status === 'loading' && (
            <div className="status-indicator">
              <div className="dot dot-info" style={{ animation: 'pulse 1.5s infinite' }} />
              Đang tính toán...
            </div>
          )}
          {isBasicTab && state.status === 'success' && state.data.isOptimal && (
            <div className="status-indicator">
              <div className="dot dot-success" />
              Đã tìm được phương án tối ưu
            </div>
          )}
        </div>
      </header>

      {/* Main Layout */}
      <main className="main-layout">
        {isBasicTab ? (
          // ── Tab Vận tải cơ bản: layout 2 panel hiện tại ──────────────────
          <>
            <aside className="panel-left">
              <div className="panel-left-inner">
                <Sidebar
                  editorState={editorState}
                  setEditorState={setEditorState}
                  onSolve={solve}
                  onReset={reset}
                  loading={state.status === 'loading'}
                />
              </div>
            </aside>
            <section className="panel-right">
              <ResultsPanel
                state={state}
                editorState={editorState}
                setEditorState={setEditorState}
                presentationMode={presentationMode}
                togglePresentationMode={togglePresentationMode}
              />
            </section>
          </>
        ) : (
          // ── Tabs mở rộng: full-width layout mỗi page tự quản lý ─────────
          <div className="ext-page-container">
            {problemTab === 'max'        && <TransportationMaxPage />}
            {problemTab === 'forbidden'  && <ForbiddenCellsPage />}
            {problemTab === 'inequality' && <InequalityPage />}
            {problemTab === 'warehouse'  && <WarehousePage />}
            {problemTab === 'assignment' && <AssignmentPage />}
          </div>
        )}
      </main>
    </div>
  )
}

export default App
