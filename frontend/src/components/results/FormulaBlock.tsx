// src/components/results/FormulaBlock.tsx
import 'katex/dist/katex.min.css'
import { InlineMath, BlockMath } from 'react-katex'
import { memo } from 'react'
import { Info } from '@phosphor-icons/react'

interface FormulaBlockProps {
  formula: string
  block?: boolean
  description?: string
}

export const FormulaBlock = memo(function FormulaBlock({
  formula,
  block = true,
  description,
}: FormulaBlockProps) {
  return (
    <div className="formula-block" style={{ position: 'relative' }}>
      {description && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--sp-2)',
            fontSize: '0.875rem',
            color: 'var(--text-secondary)',
            marginBottom: 'var(--sp-2)',
            fontWeight: 500,
          }}
        >
          <Info size={16} style={{ color: 'var(--accent)' }} />
          {description}
        </div>
      )}
      <div style={{ color: 'var(--text-primary)' }}>
        {block ? <BlockMath math={formula} /> : <InlineMath math={formula} />}
      </div>
    </div>
  )
})
