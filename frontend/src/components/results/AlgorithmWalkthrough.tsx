// src/components/results/AlgorithmWalkthrough.tsx
// ================================================
// Quản lý state machine cho trình diễn giải bài toán.

import { useState, useMemo, useCallback, useEffect } from 'react'
import { CaretLeft, CaretRight, PresentationChart, CheckCircle, Presentation } from '@phosphor-icons/react'
import { clsx } from 'clsx'
import { MatrixStage } from './MatrixStage'
import { StepExplainer } from './StepExplainer'
import { NetworkFlowView } from './NetworkFlowView'
import { CostProgressChart } from './CostProgressChart'
import { SolveRequest, SolveResponse, IterationResult } from '@/types/transportation'
import { TransformWrapper, TransformComponent } from 'react-zoom-pan-pinch'
import { MagnifyingGlassPlus, MagnifyingGlassMinus, CornersOut, PlayCircle, PauseCircle, Table, Article, Graph, ChartLineUp, Eye, EyeSlash } from '@phosphor-icons/react'

interface AlgorithmWalkthroughProps {
  request: SolveRequest
  response: SolveResponse
  presentationMode: boolean
  togglePresentationMode: () => void
}

type Phase = 'setup' | 'initial' | 'potentials' | 'reduced_costs' | 'cycle' | 'update' | 'optimal' | 'final'

interface MicroStep {
  id: string
  phase: Phase
  title: string
  markdown: string

  // Matrix data
  allocationMatrix: number[][]
  basisCells?: [number, number][]
  u?: (number | null)[]
  v?: (number | null)[]
  reducedCosts?: (number | null)[][]
  enteringCell?: [number, number] | null
  leavingCell?: [number, number] | null
  cycle?: [number, number][] | null

  // View toggles
  showPotentials?: boolean
  showReducedCosts?: boolean
  showCycle?: boolean
}

export function AlgorithmWalkthrough({
  request,
  response,
  presentationMode,
  togglePresentationMode
}: AlgorithmWalkthroughProps) {

  // Ưu tiên dùng dữ liệu đã cân bằng từ response, fallback sang request nếu thiếu
  const effectiveCostMatrix = response.costMatrix ?? request.costMatrix
  const effectiveSupply = response.supply ?? request.supply
  const effectiveDemand = response.demand ?? request.demand
  const effectiveSourceNames = response.sourceNames ?? request.sourceNames
  const effectiveDestNames = response.destinationNames ?? request.destinationNames

  const m = effectiveSupply.length
  const n = effectiveDemand.length

  // Dummy index từ metadata response
  const dummyRowIndex = response.dummySourceIndex ?? null
  const dummyColIndex = response.dummyDestinationIndex ?? null

  // Sinh các MicroStep dựa trên SolveResponse
  const steps = useMemo(() => {
    const list: MicroStep[] = []

    // 1. Setup Phase
    // Dùng tổng gốc (trước cân bằng) nếu có
    const origSupplyTotal = response.originalSupplyTotal ?? effectiveSupply.reduce((a, b) => a + b, 0)
    const origDemandTotal = response.originalDemandTotal ?? effectiveDemand.reduce((a, b) => a + b, 0)
    const isBalancedOrig = response.isBalancedOriginal ?? (origSupplyTotal === origDemandTotal)

    // Thông tin về dummy
    const balanceType = response.balanceType ?? 'none'
    const dummyNote = balanceType === 'dummy_destination'
      ? `\n\n> ⚠️ **Bài toán không cân bằng.** Hệ thống đã tự động thêm **cột trạm thu ảo (Dummy)** với nhu cầu **${origSupplyTotal - origDemandTotal}** (cước phí = 0) để cân bằng.`
      : balanceType === 'dummy_source'
      ? `\n\n> ⚠️ **Bài toán không cân bằng.** Hệ thống đã tự động thêm **hàng trạm phát ảo (Dummy)** với lượng **${origDemandTotal - origSupplyTotal}** (cước phí = 0) để cân bằng.`
      : ''

    list.push({
      id: 'setup',
      phase: 'setup',
      title: 'Dữ liệu đầu vào',
      markdown: `
Bài toán vận tải gồm **${request.supply.length}** trạm phát và **${request.demand.length}** trạm thu (dữ liệu gốc).
- Tổng lượng phát (gốc): **${origSupplyTotal}**
- Tổng lượng thu (gốc): **${origDemandTotal}**
${isBalancedOrig ? '\n✓ Bài toán đã cân bằng (Tổng phát = Tổng thu).' : dummyNote}

**Điều kiện cân bằng:**
$$ \\sum_{i=1}^{m} a_i = \\sum_{j=1}^{n} b_j $$
      `,
      allocationMatrix: Array(m).fill(0).map(() => Array(n).fill(0)),
    })

    if (response.iterations.length === 0) return list

    // 2. Initial Solution
    const iter0 = response.iterations[0]
    list.push({
      id: 'initial',
      phase: 'initial',
      title: 'Phương án khởi tạo',
      markdown: `
Sử dụng phương pháp: **${request.initialMethod === 'least_cost' ? 'Cực tiểu chi phí' : 'Góc Tây Bắc'}**.
- Chi phí ban đầu: **${iter0.totalCost}**
- Các ô có lượng phân bổ > 0 tạo thành tập cơ sở ban đầu.
      `,
      allocationMatrix: iter0.allocationMatrix,
      basisCells: iter0.allocationMatrix.flatMap((row, i) =>
        row.map((val, j) => val > 0 ? [i, j] as [number, number] : null)
      ).filter(Boolean) as [number, number][],
    })

    // 3. Optimization Iterations
    let lastAlloc = iter0.allocationMatrix
    let lastBasis = iter0.allocationMatrix.flatMap((row, i) =>
      row.map((val, j) => val > 0 ? [i, j] as [number, number] : null)
    ).filter(Boolean) as [number, number][]

    for (let k = 1; k < response.iterations.length; k++) {
      const iter = response.iterations[k]
      const isLast = k === response.iterations.length - 1
      const loopStr = `Vòng ${k}`

      // Phase C: Potentials
      if (iter.potentialsU && iter.potentialsV) {
        list.push({
          id: `potentials-${k}`,
          phase: 'potentials',
          title: `[${loopStr}] Tính hệ số thế vị`,
          markdown: `
Dựa trên tập cơ sở hiện tại, ta tính các hệ số thế vị $u_i$ và $v_j$.
Gán $u_1 = 0$, các giá trị còn lại được tính sao cho đối với mọi ô cơ sở $(i,j)$:
$$ u_i + v_j = c_{i,j} \\quad \\text{(với } x_{i,j} \\in \\text{Cơ sở)} $$
          `,
          allocationMatrix: lastAlloc,
          basisCells: lastBasis,
          u: iter.potentialsU,
          v: iter.potentialsV,
          showPotentials: true,
        })
      }

      // Phase D: Reduced Costs
      if (iter.reducedCosts) {
        let bestVal = Infinity
        let hasNegative = false
        iter.reducedCosts.forEach(row => row.forEach(val => {
          if (val !== null && val < 0) hasNegative = true
          if (val !== null && val < bestVal) bestVal = val
        }))

        if (iter.isOptimal) {
          list.push({
            id: `optimal-check-${k}`,
            phase: 'optimal',
            title: `[${loopStr}] Kiểm tra tối ưu`,
            markdown: `
Ta tính ma trận chi phí giảm $\\Delta_{ij} = u_i + v_j - c_{ij}$.

Nếu tất cả $\\Delta_{ij} <= 0$, nghiệm là tối ưu.
$$ \\Delta_{ij} \\le 0 \\implies \\text{Tối ưu} $$
**✓ Tất cả các ô ngoài cơ sở đều thỏa điều kiện tối ưu.**
            `,
            allocationMatrix: lastAlloc,
            basisCells: lastBasis,
            u: iter.potentialsU,
            v: iter.potentialsV,
            reducedCosts: iter.reducedCosts,
            showPotentials: true,
            showReducedCosts: true,
          })
        } else {
          list.push({
            id: `rc-${k}`,
            phase: 'reduced_costs',
            title: `[${loopStr}] Tìm ô vào`,
            markdown: `
Vì còn tồn tại ô có $\\Delta_{ij}$ vi phạm điều kiện tối ưu, phương án hiện tại chưa tối ưu.

Chọn ô có $\\Delta_{ij}$ vi phạm lớn nhất (ở đây là **${bestVal}**) làm **Ô vào cơ sở**.
$$ \\text{Chọn ô có } \\Delta_{ij} \\text{ âm nhất} $$
Ô được chọn: **Dòng ${iter.enteringCell?.[0] !== undefined ? iter.enteringCell[0] + 1 : '?'}, Cột ${iter.enteringCell?.[1] !== undefined ? iter.enteringCell[1] + 2 : '?'}**.
            `,
            allocationMatrix: lastAlloc,
            basisCells: lastBasis,
            u: iter.potentialsU,
            v: iter.potentialsV,
            reducedCosts: iter.reducedCosts,
            enteringCell: iter.enteringCell,
            showPotentials: true,
            showReducedCosts: true,
          })

          // Phase F & G: Cycle & Theta
          if (iter.cycle && iter.theta !== undefined && iter.leavingCell) {
            list.push({
              id: `cycle-${k}`,
              phase: 'cycle',
              title: `[${loopStr}] Chu trình điều chỉnh`,
              markdown: `
Từ ô vào cơ sở, ta tìm được một chu trình khép kín duy nhất đi qua các ô cơ sở hiện tại (chỉ đi theo chiều ngang và dọc).

Đánh dấu **(+)** tại ô vào, sau đó xen kẽ **(-)** và **(+)** tại các đỉnh của chu trình.
Lượng điều chỉnh tối đa $\\theta$ là giá trị phân bổ nhỏ nhất tại các ô mang dấu (-). 

$$ \\theta = \\min \\{ x_{i,j} \\mid (i,j) \\in \\text{Chu trình (-)} \\} $$

**$\\theta = ${iter.theta}$**. Ô đạt giá trị này trở thành **Ô ra**: Dòng ${iter.leavingCell[0] + 1}, Cột ${iter.leavingCell[1] + 1}.
              `,
              allocationMatrix: lastAlloc,
              basisCells: lastBasis,
              enteringCell: iter.enteringCell,
              leavingCell: iter.leavingCell,
              cycle: iter.cycle,
              showCycle: true,
            })

            // Cập nhật lastBasis và lastAlloc cho bước update
            lastAlloc = iter.allocationMatrix

            // Xây dựng basis mới một cách tường minh từ thuật toán: basis_new = basis_old + entering - leaving
            // (Mặc dù có thể dùng allocationMatrix > 0, nhưng suy biến có thể làm ô = 0 vẫn thuộc basis)
            const nextBasisSet = new Set(lastBasis.map(b => `${b[0]},${b[1]}`))
            nextBasisSet.add(`${iter.enteringCell[0]},${iter.enteringCell[1]}`)
            nextBasisSet.delete(`${iter.leavingCell[0]},${iter.leavingCell[1]}`)
            lastBasis = Array.from(nextBasisSet).map(s => {
              const parts = s.split(',')
              return [parseInt(parts[0], 10), parseInt(parts[1], 10)] as [number, number]
            })

            list.push({
              id: `update-${k}`,
              phase: 'update',
              title: `[${loopStr}] Cập nhật phân bổ`,
              markdown: `
Điều chỉnh luồng dọc theo chu trình:
- Cộng $\\theta = ${iter.theta}$ vào các ô mang dấu (+)
- Trừ $\\theta = ${iter.theta}$ khỏi các ô mang dấu (-)

Tổng chi phí giảm được: **${iter.costDelta !== undefined ? Math.abs(iter.costDelta) : '?'}**.
Chi phí mới: **${iter.totalCost}**.
              `,
              allocationMatrix: lastAlloc,
              basisCells: lastBasis,
            })
          }
        }
      }
    }

    // Final Solution
    if (response.isOptimal) {
      list.push({
        id: 'final',
        phase: 'final',
        title: 'Kết quả cuối cùng',
        markdown: `
Thuật toán đã hội tụ. Phương án phân bổ hiện tại là tối ưu toàn cục.

$$ f(X^*) = \\min \\sum c_{i,j} x_{i,j} $$

Tổng chi phí nhỏ nhất có thể đạt được: **${response.totalCost}**

Bạn có thể xem biểu đồ mạng lưới hoặc biểu đồ chi phí ở các tab bên dưới.
        `,
        allocationMatrix: response.allocationMatrix,
        basisCells: response.basisCells,
      })
    }

    return list
  }, [request, response])

  const [stepIndex, setStepIndex] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)
  const [playbackSpeed, setPlaybackSpeed] = useState(1500)

  const [visiblePanels, setVisiblePanels] = useState({
    explainer: true,
    matrix: true,
    network: false,
    chart: false
  })

  const togglePanel = (panel: keyof typeof visiblePanels) => {
    setVisiblePanels(prev => ({ ...prev, [panel]: !prev[panel] }))
  }

  const step = steps[stepIndex]

  const nextStep = useCallback(() => {
    setStepIndex(prev => {
      if (prev >= steps.length - 1) {
        setIsPlaying(false)
        return prev
      }
      return prev + 1
    })
  }, [steps.length])

  const prevStep = useCallback(() => {
    setStepIndex(prev => Math.max(prev - 1, 0))
    setIsPlaying(false)
  }, [])

  // Auto-run logic
  useEffect(() => {
    if (!isPlaying) return
    const timer = setInterval(() => {
      setStepIndex(prev => {
        if (prev >= steps.length - 1) {
          setIsPlaying(false)
          return prev
        }
        return prev + 1
      })
    }, playbackSpeed)
    return () => clearInterval(timer)
  }, [isPlaying, steps.length, playbackSpeed])

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'ArrowRight' || e.key === 'j') {
        nextStep()
      } else if (e.key === 'ArrowLeft' || e.key === 'k') {
        prevStep()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [nextStep, prevStep])

  if (!step) return null

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: 'var(--sp-4)' }}>

      {/* Top Controls */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 'var(--sp-4)' }}>
        <h3 style={{ margin: 0, fontSize: '1.25rem' }}>Các bước giải ({stepIndex + 1}/{steps.length})</h3>

        <div style={{ display: 'flex', gap: 'var(--sp-4)', alignItems: 'center', flexWrap: 'wrap' }}>
          {/* View Toggles */}
          <div style={{ display: 'flex', gap: 'var(--sp-2)', padding: 'var(--sp-1)', background: 'var(--bg-inset)', borderRadius: 'var(--radius)', border: '1px solid var(--border-subtle)' }}>
            <button className={clsx("btn btn-sm btn-ghost", visiblePanels.explainer && "btn-primary")} onClick={() => togglePanel('explainer')} title="Bật/tắt Giải thích">
              <Article size={16} /> Giải thích
            </button>
            <button className={clsx("btn btn-sm btn-ghost", visiblePanels.matrix && "btn-primary")} onClick={() => togglePanel('matrix')} title="Bật/tắt Ma trận">
              <Table size={16} /> Ma trận
            </button>
            <button className={clsx("btn btn-sm btn-ghost", visiblePanels.network && "btn-primary")} onClick={() => togglePanel('network')} title="Bật/tắt Mạng lưới">
              <Graph size={16} /> Mạng lưới
            </button>
            <button className={clsx("btn btn-sm btn-ghost", visiblePanels.chart && "btn-primary")} onClick={() => togglePanel('chart')} title="Bật/tắt Biểu đồ">
              <ChartLineUp size={16} /> Biểu đồ
            </button>
          </div>

          <div style={{ display: 'flex', gap: 'var(--sp-2)' }}>
            <button type="button" className="btn btn-secondary btn-icon" onClick={prevStep} disabled={stepIndex === 0}>
              <CaretLeft size={20} />
            </button>
            <button type="button" className={clsx('btn', isPlaying ? 'btn-danger' : 'btn-primary')} onClick={() => setIsPlaying(!isPlaying)}>
              {isPlaying ? <PauseCircle size={20} /> : <PlayCircle size={20} />}
            </button>
            <button type="button" className="btn btn-secondary btn-icon" onClick={nextStep} disabled={stepIndex === steps.length - 1}>
              <CaretRight size={20} />
            </button>
            <button className={clsx("btn", presentationMode ? "btn-primary" : "btn-secondary")} onClick={togglePresentationMode} title={presentationMode ? "Thoát trình chiếu" : "Trình chiếu"}>
              <Presentation size={20} />
            </button>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div style={{ display: 'flex', flex: 1, gap: 'var(--sp-6)', minHeight: 0, flexDirection: presentationMode ? 'column' : 'row' }}>

        {/* Visualizations Container (flex: 1 or flex: 2 depending on layout) */}
        {(visiblePanels.matrix || visiblePanels.network || visiblePanels.chart) && (
          <div style={{
            flex: visiblePanels.explainer && !presentationMode ? 2 : 1,
            display: 'flex',
            flexDirection: presentationMode ? 'row' : 'column',
            gap: 'var(--sp-4)',
            minHeight: 0
          }}>

            {visiblePanels.matrix && (
              <div style={{
                flex: 1,
                display: 'flex',
                flexDirection: 'column',
                background: 'var(--bg-surface)',
                borderRadius: 'var(--radius-lg)',
                border: '1px solid var(--border-subtle)',
                overflow: 'hidden',
                minHeight: 0
              }}>
                <TransformWrapper initialScale={1} minScale={0.5} maxScale={3} centerOnInit wheel={{ step: 0.1 }}>
                  {({ zoomIn, zoomOut, resetTransform, zoomToElement }) => (
                    <>
                      <div style={{ display: 'flex', gap: 'var(--sp-2)', padding: 'var(--sp-2)', background: 'var(--bg-inset)', borderBottom: '1px solid var(--border-subtle)' }}>
                        <button className="btn btn-secondary btn-icon btn-sm" onClick={() => zoomIn()} title="Phóng to">
                          <MagnifyingGlassPlus size={16} />
                        </button>
                        <button className="btn btn-secondary btn-icon btn-sm" onClick={() => zoomOut()} title="Thu nhỏ">
                          <MagnifyingGlassMinus size={16} />
                        </button>
                        <button className="btn btn-secondary btn-icon btn-sm" onClick={() => zoomToElement('matrix-stage-zoom-target')} title="Mặc định">
                          <CornersOut size={16} />
                        </button>
                      </div>

                      <TransformComponent
                        wrapperStyle={{ width: '100%', height: '100%', minHeight: 0, flex: 1 }}
                        contentStyle={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 'var(--sp-6)' }}
                      >
                        <div id="matrix-stage-zoom-target" style={{ padding: '3rem', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                          <MatrixStage
                            costMatrix={effectiveCostMatrix}
                            allocationMatrix={step.allocationMatrix}
                            supply={effectiveSupply}
                            demand={effectiveDemand}
                            sourceNames={effectiveSourceNames ?? undefined}
                            destNames={effectiveDestNames ?? undefined}
                            basisCells={step.basisCells}
                            u={step.u}
                            v={step.v}
                            reducedCosts={step.reducedCosts}
                            enteringCell={step.enteringCell}
                            leavingCell={step.leavingCell}
                            cycle={step.cycle}
                            showPotentials={step.showPotentials}
                            showReducedCosts={step.showReducedCosts}
                            showCycle={step.showCycle}
                            presentationMode={presentationMode}
                            dummyRowIndex={dummyRowIndex}
                            dummyColIndex={dummyColIndex}
                            editable={false}
                          />
                        </div>
                      </TransformComponent>
                    </>
                  )}
                </TransformWrapper>
              </div>
            )}

            {visiblePanels.network && (
              <div style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
                <NetworkFlowView
                  allocationMatrix={step.allocationMatrix}
                  costMatrix={effectiveCostMatrix}
                  supply={effectiveSupply}
                  demand={effectiveDemand}
                  sourceNames={effectiveSourceNames ?? undefined}
                  destNames={effectiveDestNames ?? undefined}
                />
              </div>
            )}

            {visiblePanels.chart && (
              <div style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
                <CostProgressChart
                  initialCost={response.initialCost ?? 0}
                  iterations={response.iterations}
                  optimalCost={response.totalCost}
                />
              </div>
            )}
          </div>
        )}

        {/* Explainer Container */}
        {visiblePanels.explainer && (
          <div style={{
            flex: (!visiblePanels.matrix && !visiblePanels.network && !visiblePanels.chart) ? 1 : (presentationMode ? 'none' : 1),
            background: 'var(--bg-surface)',
            borderRadius: 'var(--radius-lg)',
            border: '1px solid var(--border-subtle)',
            boxShadow: 'var(--shadow-sm)',
            flexShrink: 0,
            minHeight: presentationMode ? '250px' : '200px'
          }}>
            <StepExplainer
              phase={step.phase}
              title={step.title}
              markdown={step.markdown}
              presentationMode={presentationMode}
            />
          </div>
        )}
      </div>
    </div>
  )
}
