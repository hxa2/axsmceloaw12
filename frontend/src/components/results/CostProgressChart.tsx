// src/components/results/CostProgressChart.tsx
// ============================================
// Biểu đồ theo dõi sự giảm chi phí qua từng bước lặp

import { memo, useMemo } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine
} from 'recharts'
import { IterationResult } from '@/types/transportation'

interface CostProgressChartProps {
  initialCost: number
  iterations: IterationResult[]
  optimalCost: number
}

export const CostProgressChart = memo(function CostProgressChart({
  initialCost,
  iterations,
  optimalCost,
}: CostProgressChartProps) {
  const data = useMemo(() => {
    const points = [
      { name: 'Khởi tạo', cost: initialCost },
    ]
    
    // Thu thập các chi phí giảm dần
    let lastCost = initialCost
    iterations.forEach((it) => {
      // Chỉ lấy các bước có thay đổi chi phí hoặc bước cuối cùng
      if (it.totalCost !== null && it.totalCost !== undefined) {
        if (it.totalCost < lastCost || it.isOptimal) {
          points.push({
            name: it.step === 0 ? 'Khởi tạo' : `Vòng ${it.step}`,
            cost: it.totalCost
          })
          lastCost = it.totalCost
        }
      }
    })
    
    return points
  }, [initialCost, iterations])

  return (
    <div style={{ width: '100%', height: '100%', minHeight: 0, display: 'flex', flexDirection: 'column', background: 'var(--bg-surface)', padding: 'var(--sp-4)', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-subtle)' }}>
      <h3 style={{ fontSize: '1rem', marginBottom: 'var(--sp-4)', textAlign: 'center' }}>
        Biểu đồ giảm chi phí
      </h3>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart
          data={data}
          margin={{ top: 5, right: 20, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" />
          <XAxis dataKey="name" stroke="var(--text-tertiary)" fontSize={12} tickMargin={10} />
          <YAxis domain={['auto', 'auto']} stroke="var(--text-tertiary)" fontSize={12} tickFormatter={(val) => val.toLocaleString()} />
          <Tooltip 
            contentStyle={{ background: 'var(--bg-surface)', border: '1px solid var(--border-muted)', borderRadius: '6px', boxShadow: 'var(--shadow-sm)' }}
            itemStyle={{ color: 'var(--accent)', fontWeight: 600 }}
            labelStyle={{ color: 'var(--text-secondary)', marginBottom: '4px' }}
          />
          <ReferenceLine y={optimalCost} label="Tối ưu" stroke="var(--success)" strokeDasharray="3 3" />
          <Line 
            type="monotone" 
            dataKey="cost" 
            name="Chi phí" 
            stroke="var(--accent)" 
            strokeWidth={3}
            activeDot={{ r: 6, fill: 'var(--accent)', stroke: 'white', strokeWidth: 2 }} 
            animationDuration={1500}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
})
