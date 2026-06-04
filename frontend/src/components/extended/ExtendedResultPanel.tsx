// src/components/extended/ExtendedResultPanel.tsx
// ==================================================
// Panel kết quả chung cho các bài toán mở rộng.

import { useState } from 'react'
import type { ExtendedSolveResponse } from '@/types/extended'
import { CheckCircle, Warning, ArrowsClockwise, Info } from '@phosphor-icons/react'

interface ExtendedResultPanelProps {
  response: ExtendedSolveResponse | null
  loading: boolean
  error: string | null
  children?: React.ReactNode  // slot cho custom solution display
}

export function ExtendedResultPanel({
  response,
  loading,
  error,
  children,
}: ExtendedResultPanelProps) {
  if (loading) {
    return (
      <div className="ext-result-loading">
        <div className="spinner" style={{ width: 28, height: 28, borderWidth: 3 }} />
        <p style={{ color: 'var(--text-secondary)', marginTop: 12 }}>Đang giải bài toán...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="error-banner fade-in" style={{ maxWidth: 560 }}>
        <Warning size={18} weight="fill" style={{ flexShrink: 0, marginTop: 1 }} />
        <div>
          <div style={{ fontWeight: 600, marginBottom: 4 }}>Lỗi khi giải bài toán</div>
          <div style={{ lineHeight: 1.5 }}>{error}</div>
        </div>
      </div>
    )
  }

  if (!response) return null

  const warnings = response.warnings ?? []

  return (
    <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-5)' }}>
      {/* Warnings */}
      {warnings.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-2)' }}>
          {warnings.map((w, i) => (
            <div key={i} className="error-banner" style={{ background: 'var(--warning-muted)', borderColor: 'var(--warning)' }}>
              <Warning size={16} weight="fill" style={{ flexShrink: 0, color: 'var(--warning)' }} />
              <span style={{ color: 'var(--warning)', fontSize: '0.875rem' }}>{w}</span>
            </div>
          ))}
        </div>
      )}

      {/* Transformations */}
      {response.transformations.length > 0 && (
        <TransformationSection transformations={response.transformations} />
      )}

      {/* Custom solution content */}
      {children}
    </div>
  )
}

// ── Transformation Panel ──────────────────────────────────────────────────────

function TransformationSection({ transformations }: { transformations: ExtendedSolveResponse['transformations'] }) {
  return (
    <div className="card" style={{ padding: 0 }}>
      <div className="card-header">
        <ArrowsClockwise size={14} style={{ color: 'var(--accent)' }} />
        <span style={{ fontWeight: 600, fontSize: '0.875rem' }}>Các bước biến đổi bài toán</span>
      </div>
      <div style={{ padding: 'var(--sp-4)', display: 'flex', flexDirection: 'column', gap: 'var(--sp-3)' }}>
        {transformations.map((t, i) => (
          <div key={i} style={{
            padding: 'var(--sp-3)',
            background: 'var(--bg-inset)',
            borderRadius: 'var(--radius)',
            borderLeft: '3px solid var(--accent)',
          }}>
            <div style={{ fontWeight: 600, fontSize: '0.875rem', color: 'var(--text-primary)', marginBottom: 4 }}>
              {t.description}
            </div>
            {t.formula && (
              <code style={{
                display: 'block',
                fontSize: '0.875rem',
                color: 'var(--accent)',
                marginTop: 4,
                fontFamily: 'var(--font-mono)',
              }}>
                {t.formula}
              </code>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

// ── Matrix Display ────────────────────────────────────────────────────────────

interface MatrixTableProps {
  matrix: number[][]
  rowHeaders?: string[]
  colHeaders?: string[]
  highlightCells?: Set<string>   // "row,col" format
  forbiddenCells?: Set<string>
  bigMValue?: number
  label?: string
  colSuffix?: string[]           // e.g. supply values
  rowSuffix?: string[]           // e.g. demand values
}

export function MatrixTable({
  matrix,
  rowHeaders,
  colHeaders,
  highlightCells,
  forbiddenCells,
  bigMValue,
  label,
  colSuffix,
  rowSuffix,
}: MatrixTableProps) {
  const m = matrix.length
  const n = matrix[0]?.length ?? 0

  return (
    <div>
      {label && (
        <div style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-tertiary)', marginBottom: 'var(--sp-2)' }}>
          {label}
        </div>
      )}
      <div className="matrix-grid-wrapper">
        <table style={{ borderCollapse: 'collapse', fontSize: '0.875rem' }}>
          <thead>
            <tr>
              <th style={thStyle}></th>
              {colHeaders?.map((h, j) => (
                <th key={j} style={{ ...thStyle, color: 'var(--accent)', minWidth: 70 }}>{h}</th>
              )) ?? Array.from({ length: n }, (_, j) => (
                <th key={j} style={{ ...thStyle, color: 'var(--accent)', minWidth: 70 }}>D{j+1}</th>
              ))}
              {colSuffix && <th style={{ ...thStyle, color: 'var(--success)' }}>Phát (a)</th>}
            </tr>
          </thead>
          <tbody>
            {matrix.map((row, i) => (
              <tr key={i}>
                <td style={{ ...thStyle, color: 'var(--accent)' }}>
                  {rowHeaders?.[i] ?? `S${i+1}`}
                </td>
                {row.map((val, j) => {
                  const key = `${i},${j}`
                  const isForbidden = forbiddenCells?.has(key)
                  const isHighlighted = highlightCells?.has(key)
                  const isBigM = bigMValue && Math.abs(val - bigMValue) < 1
                  return (
                    <td key={j} style={{
                      ...tdStyle,
                      background: isForbidden
                        ? 'var(--danger-muted)'
                        : isHighlighted
                        ? 'var(--accent-muted)'
                        : 'var(--bg-surface)',
                      fontWeight: isHighlighted ? 700 : 400,
                      color: isForbidden ? 'var(--danger)' : 'var(--text-primary)',
                      border: isHighlighted ? '2px solid var(--accent)' : '1px solid var(--border-subtle)',
                      fontFamily: 'var(--font-mono)',
                    }}>
                      {isForbidden ? '🔒' : isBigM ? 'M' : val}
                    </td>
                  )
                })}
                {colSuffix && (
                  <td style={{ ...tdStyle, color: 'var(--success)', fontWeight: 600, fontFamily: 'var(--font-mono)' }}>
                    {colSuffix[i]}
                  </td>
                )}
              </tr>
            ))}
            {rowSuffix && (
              <tr>
                <td style={{ ...thStyle, color: 'var(--text-tertiary)' }}>Thu (b)</td>
                {rowSuffix.map((v, j) => (
                  <td key={j} style={{ ...tdStyle, color: 'var(--warning)', fontWeight: 600, fontFamily: 'var(--font-mono)' }}>{v}</td>
                ))}
                <td style={tdStyle} />
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

const thStyle: React.CSSProperties = {
  padding: '6px 12px',
  background: 'var(--bg-inset)',
  border: '1px solid var(--border-subtle)',
  textAlign: 'center',
  fontWeight: 600,
  fontSize: '0.8125rem',
  color: 'var(--text-secondary)',
}

const tdStyle: React.CSSProperties = {
  padding: '6px 12px',
  border: '1px solid var(--border-subtle)',
  textAlign: 'center',
  minWidth: 60,
}

// ── Solution Summary Card ─────────────────────────────────────────────────────

interface SummaryCardProps {
  label: string
  value: string | number
  color?: string
  icon?: React.ReactNode
  subtitle?: string
}

export function SummaryCard({ label, value, color = 'var(--accent)', icon, subtitle }: SummaryCardProps) {
  return (
    <div style={{
      padding: 'var(--sp-4)',
      background: 'var(--bg-surface)',
      border: '1px solid var(--border-subtle)',
      borderRadius: 'var(--radius-lg)',
      borderTop: `3px solid ${color}`,
      boxShadow: 'var(--shadow-sm)',
    }}>
      <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 6 }}>
        {label}
      </div>
      <div style={{ fontSize: '1.75rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color, lineHeight: 1 }}>
        {value}
      </div>
      {subtitle && (
        <div style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', marginTop: 4 }}>{subtitle}</div>
      )}
    </div>
  )
}

// ── Feasibility Badge ─────────────────────────────────────────────────────────

export function FeasibilityBadge({ isFeasible, label }: { isFeasible: boolean; label?: string }) {
  return (
    <span className={`badge ${isFeasible ? 'badge-success' : 'badge-danger'}`}>
      {isFeasible ? '✓' : '✗'} {label ?? (isFeasible ? 'Khả thi' : 'Không khả thi')}
    </span>
  )
}
