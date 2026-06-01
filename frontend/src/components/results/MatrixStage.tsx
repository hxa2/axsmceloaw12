// src/components/results/MatrixStage.tsx
// =====================================
// Component hiển thị ma trận phục vụ giảng dạy thuật toán
// Hỗ trợ hiển thị cước phí, luồng phân bổ, thế vị, reduced cost, và cycle

import { memo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { clsx } from 'clsx'

export interface MatrixStageProps {
  costMatrix: (number | string)[][]
  allocationMatrix?: number[][]
  supply: (number | string)[]
  demand: (number | string)[]
  sourceNames?: string[]
  destNames?: string[]
  
  // States cho algorithm walkthrough
  basisCells?: [number, number][]
  u?: (number | null)[]
  v?: (number | null)[]
  reducedCosts?: (number | null)[][]
  enteringCell?: [number, number] | null
  leavingCell?: [number, number] | null
  cycle?: [number, number][] | null
  
  // Tùy chọn hiển thị
  showPotentials?: boolean
  showReducedCosts?: boolean
  showCycle?: boolean
  presentationMode?: boolean
  
  // Tùy chọn Edit
  editable?: boolean
  onCostChange?: (i: number, j: number, val: string) => void
  onSupplyChange?: (i: number, val: string) => void
  onDemandChange?: (j: number, val: string) => void
  onKeyDown?: (e: React.KeyboardEvent<HTMLInputElement>, r: number | 'demand' | 'supply', c: number | 'supply') => void
}

export const MatrixStage = memo(function MatrixStage({
  costMatrix,
  allocationMatrix,
  supply,
  demand,
  sourceNames,
  destNames,
  basisCells = [],
  u,
  v,
  reducedCosts,
  enteringCell,
  leavingCell,
  cycle,
  showPotentials = false,
  showReducedCosts = false,
  showCycle = false,
  presentationMode = false,
  editable = false,
  onCostChange,
  onSupplyChange,
  onDemandChange,
  onKeyDown,
}: MatrixStageProps) {
  const m = supply.length
  const n = demand.length
  const sources = sourceNames ?? Array.from({ length: m }, (_, i) => `S${i + 1}`)
  const dests = destNames ?? Array.from({ length: n }, (_, j) => `D${j + 1}`)

  // Helpers tính tổng (hỗ trợ cả string khi edit)
  const totalSupply = supply.reduce<number>((sum, v) => sum + (typeof v === 'string' ? parseFloat(v) || 0 : v), 0)
  const totalDemand = demand.reduce<number>((sum, v) => sum + (typeof v === 'string' ? parseFloat(v) || 0 : v), 0)

  // Kiểm tra cell có nằm trong tập cơ sở không
  const isBasis = (i: number, j: number) => {
    return basisCells.some(([bi, bj]) => bi === i && bj === j)
  }

  // Lấy dấu chu trình (+1 hoặc -1) của một ô nếu nó thuộc chu trình
  const getCycleSign = (i: number, j: number) => {
    if (!showCycle || !cycle) return null
    const idx = cycle.findIndex(([ci, cj]) => ci === i && cj === j)
    if (idx === -1) return null
    return idx % 2 === 0 ? '+' : '−' // + cho chẵn (bắt đầu bằng entering cell), - cho lẻ
  }

  // Lấy index của ô trong chu trình để vẽ animation
  const getCycleIndex = (i: number, j: number) => {
    if (!showCycle || !cycle) return -1
    return cycle.findIndex(([ci, cj]) => ci === i && cj === j)
  }

  // Determine the cell style classes
  const getCellClasses = (i: number, j: number) => {
    const isEnt = enteringCell?.[0] === i && enteringCell?.[1] === j
    const isLeav = leavingCell?.[0] === i && leavingCell?.[1] === j
    const isBas = isBasis(i, j)
    const sign = getCycleSign(i, j)
    
    return clsx(
      'result-matrix-cell',
      {
        'cell-entering': isEnt,
        'cell-leaving': isLeav,
        'cell-basis': isBas && !isEnt && !isLeav,
      }
    )
  }

  return (
    <div id="matrix-stage-container" className="result-matrix-container" style={{ position: 'relative' }}>
      
      {/* ── Header Row (Destinations & v_j) ── */}
      <div className="result-matrix-row">
        <div className="result-matrix-cell header" style={{ background: 'transparent' }} />
        {dests.map((name, j) => (
          <div key={`col-${j}`} className="result-matrix-cell header" style={{ flexDirection: 'column', gap: 2 }}>
            <span style={{ fontWeight: 600 }}>{name}</span>
            {showPotentials && v && v[j] !== null && v[j] !== undefined && (
              <motion.span 
                initial={{ opacity: 0, y: -5 }} 
                animate={{ opacity: 1, y: 0 }} 
                style={{ fontSize: '0.75rem', color: 'var(--accent)', fontWeight: 700 }}
              >
                v={v[j]}
              </motion.span>
            )}
          </div>
        ))}
        <div className="result-matrix-cell header" style={{ color: 'var(--text-tertiary)' }}>
          Phát (a)
        </div>
      </div>

      {/* ── Main Grid ── */}
      {sources.map((name, i) => (
        <div key={`row-${i}`} className="result-matrix-row">
          
          {/* Row Header (Sources & u_i) */}
          <div className="result-matrix-cell header" style={{ flexDirection: 'column', gap: 2 }}>
            <span style={{ fontWeight: 600 }}>{name}</span>
            {showPotentials && u && u[i] !== null && u[i] !== undefined && (
              <motion.span 
                initial={{ opacity: 0, x: -5 }} 
                animate={{ opacity: 1, x: 0 }} 
                style={{ fontSize: '0.75rem', color: 'var(--accent)', fontWeight: 700 }}
              >
                u={u[i]}
              </motion.span>
            )}
          </div>

          {/* Data Cells */}
          {dests.map((_, j) => {
            const cost = costMatrix[i]?.[j]
            const alloc = allocationMatrix?.[i]?.[j]
            const rCost = reducedCosts?.[i]?.[j]
            const sign = getCycleSign(i, j)
            const cIdx = getCycleIndex(i, j)
            
            return (
              <div key={`cell-${i}-${j}`} className={getCellClasses(i, j)}>
                
                {/* Cost (Top Left) */}
                {editable ? (
                  <input
                    id={`cell-${i}-${j}`}
                    type="number"
                    className="cell-input cost-input nodrag"
                    value={cost ?? ''}
                    placeholder="0"
                    min={0}
                    onChange={(e) => onCostChange?.(i, j, e.target.value)}
                    onKeyDown={(e) => onKeyDown?.(e, i, j)}
                    onFocus={(e) => e.target.select()}
                  />
                ) : (
                  <span style={{
                    position: 'absolute', top: 4, left: 6,
                    fontSize: '0.75rem', fontWeight: 500, color: 'var(--text-secondary)'
                  }}>
                    {cost}
                  </span>
                )}

                {/* Allocation (Center) */}
                <AnimatePresence mode="wait">
                  {!editable && alloc !== undefined && alloc > 0 && (
                    <motion.div
                      key={`alloc-${alloc}`}
                      initial={{ scale: 0.8, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      transition={{ type: 'spring', stiffness: 300, damping: 20 }}
                      style={{
                        fontFamily: 'var(--font-mono)',
                        fontSize: presentationMode ? '1.25rem' : '1.125rem',
                        fontWeight: 700,
                        color: 'var(--text-primary)',
                      }}
                    >
                      {alloc}
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Reduced Cost (Bottom Right) */}
                {showReducedCosts && rCost !== null && rCost !== undefined && (
                  <motion.div
                    initial={{ scale: 0, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    style={{
                      position: 'absolute', bottom: 4, right: 6,
                      fontSize: '0.75rem', fontWeight: 600,
                      color: rCost < 0 ? 'var(--rc-negative)' : (rCost === 0 ? 'var(--rc-zero)' : 'var(--rc-positive)')
                    }}
                  >
                    Δ={rCost}
                  </motion.div>
                )}

                {/* Cycle Sign Badge (Top Right) */}
                {showCycle && sign && (
                  <motion.div
                    initial={{ scale: 0, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    transition={{ delay: cIdx * 0.15 }}
                    style={{
                      position: 'absolute', top: -6, right: -6,
                      width: 20, height: 20,
                      borderRadius: '50%',
                      background: sign === '+' ? 'var(--positive-sign)' : 'var(--negative-sign)',
                      color: 'white',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: '0.875rem', fontWeight: 700,
                      boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
                      zIndex: 10
                    }}
                  >
                    {sign}
                  </motion.div>
                )}
                
              </div>
            )
          })}

          {/* Supply Column */}
          <div className="result-matrix-cell header" style={{ background: 'var(--bg-inset)', color: 'var(--text-secondary)' }}>
            {editable ? (
              <input
                id={`cell-${i}-supply`}
                type="number"
                className="cell-input nodrag"
                value={supply[i] ?? ''}
                placeholder="0"
                min={0}
                style={{ color: 'var(--success)', fontWeight: 600 }}
                onChange={(e) => onSupplyChange?.(i, e.target.value)}
                onKeyDown={(e) => onKeyDown?.(e, i, 'supply')}
                onFocus={(e) => e.target.select()}
              />
            ) : (
              supply[i]
            )}
          </div>
        </div>
      ))}

      {/* ── Footer Row (Demand) ── */}
      <div className="result-matrix-row">
        <div className="result-matrix-cell header" style={{ color: 'var(--text-tertiary)' }}>
          Thu (b)
        </div>
        {demand.map((d, j) => (
          <div key={`dem-${j}`} className="result-matrix-cell header" style={{ background: 'var(--bg-inset)', color: 'var(--text-secondary)' }}>
            {editable ? (
              <input
                id={`cell-demand-${j}`}
                type="number"
                className="cell-input nodrag"
                value={d ?? ''}
                placeholder="0"
                min={0}
                style={{ color: 'var(--accent)', fontWeight: 600 }}
                onChange={(e) => onDemandChange?.(j, e.target.value)}
                onKeyDown={(e) => onKeyDown?.(e, 'demand', j)}
                onFocus={(e) => e.target.select()}
              />
            ) : (
              d
            )}
          </div>
        ))}
        {/* Total sum */}
        <div className="result-matrix-cell header" style={{ background: 'var(--bg-active)', fontWeight: 700, color: 'var(--text-primary)', flexDirection: 'column' }}>
          <span style={{ fontSize: '0.625rem', color: 'var(--text-tertiary)' }}>Tổng</span>
          {editable ? `${totalSupply} / ${totalDemand}` : totalSupply}
        </div>
      </div>
      
    </div>
  )
})
