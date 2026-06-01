// src/components/results/StepExplainer.tsx
// =========================================
// Hiển thị phần giải thích từng bước bằng Markdown + KaTeX.

import { memo } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import 'katex/dist/katex.min.css'

interface StepExplainerProps {
  phase: string
  title: string
  markdown: string
  presentationMode: boolean
}

export const StepExplainer = memo(function StepExplainer({
  phase,
  title,
  markdown,
  presentationMode,
}: StepExplainerProps) {
  return (
    <div style={{ 
      display: 'flex', 
      flexDirection: 'column',
      height: '100%',
      overflow: 'auto',
    }}>
      {/* Header */}
      <div style={{ 
        padding: 'var(--sp-4) var(--sp-6)', 
        borderBottom: '1px solid var(--border-subtle)',
        background: 'var(--bg-inset)',
        display: 'flex',
        alignItems: 'center',
        gap: 'var(--sp-3)',
        position: 'sticky',
        top: 0,
        zIndex: 10,
      }}>
        <div className="badge badge-accent" style={{ textTransform: 'uppercase', fontSize: '0.75rem', fontWeight: 700 }}>
          {phase.replace('_', ' ')}
        </div>
        <h3 style={{ margin: 0, fontSize: presentationMode ? '1.25rem' : '1.125rem' }}>
          {title}
        </h3>
      </div>
      
      {/* Content */}
      <div 
        className="markdown-body" 
        style={{ 
          padding: 'var(--sp-5) var(--sp-6)', 
          fontSize: presentationMode ? '1.125rem' : '1rem',
          lineHeight: 1.6,
          color: 'var(--text-primary)',
        }}
      >
        <ReactMarkdown
          remarkPlugins={[remarkMath]}
          rehypePlugins={[rehypeKatex]}
        >
          {markdown}
        </ReactMarkdown>
      </div>
    </div>
  )
})
