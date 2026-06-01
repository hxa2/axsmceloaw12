import { useState, useCallback } from 'react'
import { Sidebar } from './components/layout/Sidebar'
import { ResultsPanel } from './components/results/ResultsPanel'
import { useSolver } from './hooks/useSolver'
import { createDefaultEditorState } from './utils/matrix'
import type { ProblemEditorState } from './types/transportation'
import { Calculator } from '@phosphor-icons/react'
import { clsx } from 'clsx'
import './App.css'

function App() {
  const { state, solve, solveFromFile, reset } = useSolver()
  
  // Hoist editorState to top level so it can be shown in main panel when idle
  const [editorState, setEditorState] = useState<ProblemEditorState>(
    () => createDefaultEditorState(3, 4)
  )
  
  // State quản lý chế độ trình chiếu
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

  return (
    <div className={clsx("app", { "presentation-mode": presentationMode })}>
      {/* Topbar */}
      <header className="topbar">
        <div className="topbar-brand">
          <div className="topbar-brand-icon">
            <Calculator size={16} weight="bold" />
          </div>
          Bài Toán Vận Tải
        </div>
        <div className="topbar-sep" />
        <div className="topbar-subtitle">Teaching-Grade Walkthrough UI</div>
        
        <div className="topbar-actions">
          {state.status === 'loading' && (
            <div className="status-indicator">
              <div className="dot dot-info" style={{ animation: 'pulse 1.5s infinite' }} />
              Đang tính toán...
            </div>
          )}
          {state.status === 'success' && state.data.isOptimal && (
            <div className="status-indicator">
              <div className="dot dot-success" />
              Đã tìm được phương án tối ưu
            </div>
          )}
        </div>
      </header>

      {/* Main Layout */}
      <main className="main-layout">
        {/* Left Panel (Input Form) */}
        <aside className="panel-left">
          <div className="panel-left-inner">
            <Sidebar 
              editorState={editorState}
              setEditorState={setEditorState}
              onSolve={solve} 
              onSolveFromFile={solveFromFile}
              onReset={reset}
              loading={state.status === 'loading'}
            />
          </div>
        </aside>

        {/* Right Panel (Results & Walkthrough) */}
        <section className="panel-right">
          <ResultsPanel 
            state={state} 
            editorState={editorState}
            setEditorState={setEditorState}
            presentationMode={presentationMode}
            togglePresentationMode={togglePresentationMode}
          />
        </section>
      </main>
    </div>
  )
}

export default App
