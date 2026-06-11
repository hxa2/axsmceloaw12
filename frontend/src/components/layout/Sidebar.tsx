// src/components/layout/Sidebar.tsx
// ====================================
// Left panel: Problem editor + algorithm settings + samples.

import { useCallback, useEffect, useState, memo } from 'react'
import {
  Play,
  Shuffle,
  Upload,
  Table,
  Gear,
  FileCsv,
  Flask,
  X,
  ArrowCounterClockwise,
} from '@phosphor-icons/react'
import { api } from '@/api/client'
import {
  matrixToStrings,
  parseMatrix,
  parseVector,
  vectorToStrings,
} from '@/utils/matrix'
import type {
  ProblemEditorState,
  SampleProblem,
  SolveRequest,
} from '@/types/transportation'

interface SidebarProps {
  editorState: ProblemEditorState
  setEditorState: React.Dispatch<React.SetStateAction<ProblemEditorState>>
  onSolve: (request: SolveRequest) => void
  onReset: () => void
  loading: boolean
}

type ActiveTab = 'settings' | 'samples'

export const Sidebar = memo(function Sidebar({
  editorState,
  setEditorState,
  onSolve,
  onReset,
  loading
}: SidebarProps) {
  const [activeTab, setActiveTab] = useState<ActiveTab>('settings')
  const [samples, setSamples] = useState<SampleProblem[]>([])
  const [validationError, setValidationError] = useState<string | null>(null)
  const [fileError, setFileError] = useState<string | null>(null)

  // Load samples on mount
  useEffect(() => {
    api.getSamples().then(setSamples).catch(() => { })
  }, [])

  // Client-side validation
  const validate = useCallback((): SolveRequest | null => {
    setValidationError(null)
    const costMatrix = parseMatrix(editorState.costMatrix)
    if (!costMatrix) {
      setValidationError('Ma trận cước phí chứa giá trị không hợp lệ.')
      return null
    }
    const supply = parseVector(editorState.supply)
    if (!supply) {
      setValidationError('Vectơ lượng phát (aᵢ) chứa giá trị không hợp lệ.')
      return null
    }
    const demand = parseVector(editorState.demand)
    if (!demand) {
      setValidationError('Vectơ lượng thu (bⱼ) chứa giá trị không hợp lệ.')
      return null
    }

    const hasNeg = costMatrix.some((row) => row.some((v) => v < 0))
    if (hasNeg) {
      setValidationError('Ma trận cước phí không được có giá trị âm.')
      return null
    }

    return {
      costMatrix,
      supply,
      demand,
      sourceNames: editorState.sourceNames,
      destinationNames: editorState.destinationNames,
      initialMethod: editorState.initialMethod,
      optimizationMethod: editorState.optimizationMethod,
      includeIterations: editorState.includeIterations,
    }
  }, [editorState])

  const handleSolve = useCallback(() => {
    const request = validate()
    if (request) onSolve(request)
  }, [validate, onSolve])

  const handleLoadSample = useCallback(
    (sample: SampleProblem) => {
      setEditorState((prev) => ({
        ...prev,
        costMatrix: matrixToStrings(sample.costMatrix),
        supply: vectorToStrings(sample.supply),
        demand: vectorToStrings(sample.demand),
        sourceNames:
          sample.sourceNames ??
          Array.from({ length: sample.supply.length }, (_, i) => `S${i + 1}`),
        destinationNames:
          sample.destinationNames ??
          Array.from({ length: sample.demand.length }, (_, j) => `D${j + 1}`),
      }))
      setValidationError(null)
    },
    [setEditorState],
  )

  const handleRandomize = useCallback(async () => {
    const m = editorState.supply.length
    const n = editorState.demand.length
    try {
      const sample = await api.getRandomSample(m, n)
      handleLoadSample(sample)
    } catch {
      // Silent fail
    }
  }, [editorState.supply.length, editorState.demand.length, handleLoadSample])

  const handleFileUpload = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0]
      if (!file) return
      setFileError(null)
      try {
        const sample = await api.parseFile(file)
        handleLoadSample(sample)
      } catch (err: any) {
        setValidationError(err.message || 'Lỗi khi đọc file')
      }
      e.target.value = ''  // Reset input
    },
    [handleLoadSample],
  )

  return (
    <div className="panel-left">
      {/* Tabs */}
      <div className="tabs-bar" style={{ padding: '0 var(--sp-5)' }}>
        <TabBtn active={activeTab === 'settings'} onClick={() => setActiveTab('settings')} icon={<Gear size={14} />} label="Thuật toán" />
        <TabBtn active={activeTab === 'samples'} onClick={() => setActiveTab('samples')} icon={<Flask size={14} />} label="Mẫu" />
      </div>

      <div className="panel-left-inner">
        {/* Validation error (always show if exists) */}
        {validationError && (
          <div className="error-banner" style={{ fontSize: '0.8125rem', marginBottom: 'var(--sp-4)' }}>
            <X size={14} weight="bold" style={{ flexShrink: 0, marginTop: 1 }} />
            {validationError}
          </div>
        )}

        {/* ── Settings tab ────────────────────────────────────────── */}
        {activeTab === 'settings' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-5)' }}>
            <div className="editor-section">
              <div className="editor-section-title">
                <Gear size={14} style={{ color: 'var(--accent)' }} />
                Phương pháp khởi tạo
              </div>
              <MethodRadio
                value={editorState.initialMethod}
                onChange={(v) =>
                  setEditorState((s) => ({
                    ...s,
                    initialMethod: v as ProblemEditorState['initialMethod'],
                  }))
                }
                options={[
                  { id: 'vogel', label: 'Xấp xỉ Vogel (VAM)', description: 'Dựa trên chênh lệch cước phí' },
                  { id: 'least_cost', label: 'Cực tiểu chi phí', description: 'Chọn ô có cước phí nhỏ nhất' },
                  { id: 'northwest_corner', label: 'Góc Tây Bắc', description: 'Bắt đầu từ góc trên trái' },
                ]}
              />
            </div>

            <div className="divider" style={{ margin: 0 }} />

            <div className="editor-section">
              <div className="editor-section-title">
                <Gear size={14} style={{ color: 'var(--accent)' }} />
                Phương pháp tối ưu
              </div>
              <MethodRadio
                value={editorState.optimizationMethod}
                onChange={(v) =>
                  setEditorState((s) => ({
                    ...s,
                    optimizationMethod: v as ProblemEditorState['optimizationMethod'],
                  }))
                }
                options={[
                  { id: 'potential', label: 'Phương pháp Thế vị', description: 'Tối ưu bằng thế vị u, v' },
                  { id: 'none', label: 'Chỉ khởi tạo (không tối ưu)', description: 'Trả ngay phương án ban đầu' },
                ]}
              />
            </div>

            <div className="divider" style={{ margin: 0 }} />

            <div className="editor-section">
              <div className="editor-section-title">
                Tùy chọn
              </div>
              <label style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-3)', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={editorState.includeIterations}
                  onChange={(e) => setEditorState((s) => ({ ...s, includeIterations: e.target.checked }))}
                  style={{ accentColor: 'var(--accent)', width: 14, height: 14 }}
                />
                <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                  Hiển thị chi tiết từng bước lặp
                </span>
              </label>
            </div>
          </div>
        )}

        {/* ── Samples tab ─────────────────────────────────────────── */}
        {activeTab === 'samples' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-3)' }}>
            <div className="editor-section-title">
              <Flask size={14} style={{ color: 'var(--accent)' }} />
              Bài toán mẫu có sẵn
            </div>

            {samples.length === 0 ? (
              <div style={{ fontSize: '0.8125rem', color: 'var(--text-tertiary)', padding: 'var(--sp-4)', textAlign: 'center' }}>
                Đang tải danh sách mẫu...
              </div>
            ) : (
              samples.map((sample, idx) => (
                <button
                  key={idx}
                  type="button"
                  className="sample-card"
                  onClick={() => handleLoadSample(sample)}
                  style={{ textAlign: 'left', width: '100%', border: 'none', cursor: 'pointer' }}
                >
                  <div style={{ fontWeight: 600, fontSize: '0.875rem', color: 'var(--text-primary)', marginBottom: 'var(--sp-1)' }}>
                    {sample.name}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', marginBottom: 'var(--sp-2)' }}>
                    {sample.description}
                  </div>
                  <div style={{ display: 'flex', gap: 'var(--sp-2)', flexWrap: 'wrap' }}>
                    <span className="badge badge-neutral">
                      {sample.supply.length}×{sample.demand.length}
                    </span>
                    {sample.optimalCost && (
                      <span className="badge badge-success">
                        f* = {sample.optimalCost}
                      </span>
                    )}
                  </div>
                </button>
              ))
            )}

            <div className="divider" style={{ margin: 'var(--sp-1) 0' }} />

            <button
              type="button"
              className="btn btn-secondary"
              onClick={handleRandomize}
              style={{ width: '100%', justifyContent: 'center' }}
            >
              <Shuffle size={15} weight="bold" />
              Sinh ngẫu nhiên ({editorState.supply.length}×{editorState.demand.length})
            </button>
          </div>
        )}

        {/* ── Bottom actions (always visible) ─────────────────────── */}
        <div style={{ marginTop: 'auto', display: 'flex', flexDirection: 'column', gap: 'var(--sp-3)', paddingTop: 'var(--sp-2)' }}>
          <div className="divider" style={{ margin: 0 }} />

          <div style={{ display: 'flex', gap: 'var(--sp-2)' }}>
            {/* Reset button */}
            <button
              type="button"
              className="btn btn-secondary"
              onClick={onReset}
              style={{ flex: 1, justifyContent: 'center' }}
            >
              <ArrowCounterClockwise size={15} weight="bold" />
            </button>

            {/* File upload */}
            <label style={{ cursor: 'pointer', flex: 3 }}>
              <div className="btn btn-secondary" style={{ width: '100%', justifyContent: 'center' }}>
                <Upload size={15} weight="bold" />
                Tải lên...
              </div>
              <input
                type="file"
                accept=".xlsx,.xls,.csv,.json"
                onChange={handleFileUpload}
                style={{ display: 'none' }}
              />
            </label>
          </div>

          {/* Main solve button */}
          <button
            type="button"
            className="btn btn-primary solve-btn"
            onClick={handleSolve}
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} />
                Đang giải...
              </>
            ) : (
              <>
                <Play size={16} weight="fill" />
                Giải bài toán
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
})

// ── Sub-components ──────────────────────────────────────────────────────────

function TabBtn({ active, onClick, icon, label }: { active: boolean; onClick: () => void; icon: React.ReactNode; label: string }) {
  return (
    <button
      type="button"
      className={`tab-btn ${active ? 'active' : ''}`}
      onClick={onClick}
    >
      {icon}
      {label}
    </button>
  )
}

function MethodRadio({
  value,
  onChange,
  options,
}: {
  value: string
  onChange: (v: string) => void
  options: { id: string; label: string; description: string }[]
}) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-2)' }}>
      {options.map((opt) => (
        <label
          key={opt.id}
          style={{
            display: 'flex',
            gap: 'var(--sp-3)',
            padding: 'var(--sp-3)',
            background: value === opt.id ? 'var(--accent-muted)' : 'var(--bg-inset)',
            border: `1px solid ${value === opt.id ? 'var(--basis-border)' : 'var(--border-subtle)'}`,
            borderRadius: 'var(--radius)',
            cursor: 'pointer',
            transition: 'background var(--transition-fast), border-color var(--transition-fast)',
          }}
        >
          <input
            type="radio"
            name={`method-${opt.id.includes('_') ? 'initial' : 'opt'}`}
            value={opt.id}
            checked={value === opt.id}
            onChange={() => onChange(opt.id)}
            style={{ accentColor: 'var(--accent)', marginTop: 2, flexShrink: 0 }}
          />
          <div>
            <div style={{ fontSize: '0.875rem', fontWeight: 500, color: value === opt.id ? 'var(--accent)' : 'var(--text-primary)', marginBottom: 2 }}>
              {opt.label}
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)' }}>
              {opt.description}
            </div>
          </div>
        </label>
      ))}
    </div>
  )
}
