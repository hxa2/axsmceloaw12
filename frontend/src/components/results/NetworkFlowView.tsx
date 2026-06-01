// src/components/results/NetworkFlowView.tsx
// ===========================================
// Hiển thị đồ thị luồng mạng lưới sử dụng React Flow (@xyflow/react)

import { useMemo, memo } from 'react'
import {
  ReactFlow,
  Controls,
  Background,
  MarkerType,
  Node,
  Edge,
  BaseEdge,
  EdgeLabelRenderer,
  EdgeProps,
  getBezierPath,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'

interface NetworkFlowViewProps {
  allocationMatrix: number[][]
  costMatrix: number[][]
  supply: number[]
  demand: number[]
  sourceNames?: string[]
  destNames?: string[]
}

const SOURCE_COLORS = [
  '#4f46e5', // indigo
  '#ea580c', // orange
  '#059669', // emerald
  '#dc2626', // red
  '#7c3aed', // violet
  '#0284c7', // light blue
  '#d97706', // amber
  '#db2777', // pink
  '#65a30d', // lime
  '#0d9488', // teal
]

// Custom Edge để xê dịch label, tránh việc label đè lên nhau ở chính giữa
const BipartiteEdge = ({
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  style = {},
  markerEnd,
  data,
}: EdgeProps) => {
  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  })

  const t = (data?.labelOffsetRatio as number) ?? 0.5
  const dist = Math.abs(targetX - sourceX)
  const cx1 = sourceX + dist * 0.25
  const cx2 = targetX - dist * 0.25

  const mt = 1 - t
  const customLabelX = mt * mt * mt * sourceX + 3 * mt * mt * t * cx1 + 3 * mt * t * t * cx2 + t * t * t * targetX
  const customLabelY = mt * mt * mt * sourceY + 3 * mt * mt * t * sourceY + 3 * mt * t * t * targetY + t * t * t * targetY

  return (
    <>
      <BaseEdge path={edgePath} markerEnd={markerEnd} style={style} />
      <EdgeLabelRenderer>
        <div
          style={{
            position: 'absolute',
            transform: `translate(-50%, -50%) translate(${customLabelX}px,${customLabelY}px)`,
            background: 'var(--bg-surface)',
            padding: '4px 8px',
            borderRadius: 4,
            fontSize: 12,
            fontWeight: 700,
            color: style.stroke,
            border: '1px solid var(--border-muted)',
            boxShadow: 'var(--shadow-sm)',
            pointerEvents: 'all',
          }}
          className="nodrag nopan"
        >
          {data?.label as string}
        </div>
      </EdgeLabelRenderer>
    </>
  )
}

const edgeTypes = {
  bipartite: BipartiteEdge,
}

export const NetworkFlowView = memo(function NetworkFlowView({
  allocationMatrix,
  costMatrix,
  supply,
  demand,
  sourceNames,
  destNames,
}: NetworkFlowViewProps) {
  const m = supply.length
  const n = demand.length
  const sources = sourceNames ?? Array.from({ length: m }, (_, i) => `S${i + 1}`)
  const dests = destNames ?? Array.from({ length: n }, (_, j) => `D${j + 1}`)

  // Tính layout động
  const nodes = useMemo(() => {
    const newNodes: Node[] = []
    
    // Nút phát (Source Nodes) - Trái
    const sourceSpacing = Math.max(120, 500 / m)
    sources.forEach((name, i) => {
      const color = SOURCE_COLORS[i % SOURCE_COLORS.length]
      newNodes.push({
        id: `s${i}`,
        position: { x: 50, y: i * sourceSpacing + 50 },
        data: { label: `${name}\n(Phát: ${supply[i]})` },
        style: {
          background: 'var(--bg-surface)',
          color: 'var(--text-primary)',
          border: `2px solid ${color}`,
          borderRadius: 'var(--radius)',
          fontWeight: 600,
          textAlign: 'center',
          padding: '10px',
          boxShadow: 'var(--shadow-sm)',
        },
        sourcePosition: 'right' as any,
        targetPosition: 'left' as any,
      })
    })

    // Nút thu (Dest Nodes) - Phải
    const destSpacing = Math.max(120, 500 / n)
    dests.forEach((name, j) => {
      newNodes.push({
        id: `d${j}`,
        position: { x: 550, y: j * destSpacing + 50 },
        data: { label: `${name}\n(Thu: ${demand[j]})` },
        style: {
          background: 'var(--bg-surface)',
          color: 'var(--text-primary)',
          border: '2px solid var(--border-muted)',
          borderRadius: 'var(--radius)',
          fontWeight: 600,
          textAlign: 'center',
          padding: '10px',
          boxShadow: 'var(--shadow-sm)',
        },
        sourcePosition: 'right' as any,
        targetPosition: 'left' as any,
      })
    })

    return newNodes
  }, [m, n, sources, dests, supply, demand])

  const edges = useMemo(() => {
    const newEdges: Edge[] = []
    
    // Map to keep track of overlapping midpoints
    const midpoints = new Map<string, number>()

    for (let i = 0; i < m; i++) {
      for (let j = 0; j < n; j++) {
        const alloc = allocationMatrix[i]?.[j]
        const cost = costMatrix[i]?.[j]
        
        // Chỉ hiện những luồng > 0
        if (alloc && alloc > 0) {
          const color = SOURCE_COLORS[i % SOURCE_COLORS.length]
          
          const uniqueIdx = i * n + j
          const t = 0.2 + (uniqueIdx / Math.max(1, m * n - 1)) * 0.6

          newEdges.push({
            id: `e-${i}-${j}`,
            source: `s${i}`,
            target: `d${j}`,
            type: 'bipartite', // Sử dụng Custom Edge
            data: {
              label: `x=${alloc} (c=${cost})`,
              labelOffsetRatio: t,
            },
            style: { 
              stroke: color, 
              strokeWidth: 2.5,
              opacity: 0.85
            },
            markerEnd: {
              type: MarkerType.ArrowClosed,
              color: color,
            },
            animated: true,
          })
        }
      }
    }
    return newEdges
  }, [allocationMatrix, costMatrix, m, n])

  return (
    <div style={{ width: '100%', height: '100%', minHeight: 0, display: 'flex', flexDirection: 'column', background: 'var(--bg-inset)', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-subtle)', overflow: 'hidden' }}>
      <ReactFlow 
        nodes={nodes} 
        edges={edges} 
        edgeTypes={edgeTypes}
        fitView 
        minZoom={0.2}
      >
        <Background color="var(--border-muted)" gap={16} />
        <Controls />
      </ReactFlow>
    </div>
  )
})
