// src/components/extended/ProblemTabBar.tsx
// ==========================================
// Tab bar ngang chọn loại bài toán.

import type { ProblemTab } from '@/types/extended'

interface TabDef {
  id: ProblemTab
  label: string
  shortLabel: string
  icon: string
  color: string
}

const TABS: TabDef[] = [
  { id: 'basic',       label: 'Vận tải cơ bản',        shortLabel: 'Cơ bản',      icon: '📦', color: '#4f46e5' },
  { id: 'max',         label: 'Vận tải dạng Max',       shortLabel: 'Max',         icon: '📈', color: '#16a34a' },
  { id: 'forbidden',   label: 'Vận tải có ô cấm',       shortLabel: 'Ô cấm',       icon: '🔒', color: '#dc2626' },
  { id: 'inequality',  label: 'Ràng buộc bất đẳng thức', shortLabel: 'Bất đẳng thức', icon: '⩽', color: '#d97706' },
  { id: 'warehouse',   label: 'Lập kho nhận hàng',       shortLabel: 'Kho',         icon: '🏭', color: '#7c3aed' },
  { id: 'assignment',  label: 'Bài toán phân việc',      shortLabel: 'Phân việc',   icon: '👥', color: '#0891b2' },
]

interface ProblemTabBarProps {
  activeTab: ProblemTab
  onChange: (tab: ProblemTab) => void
}

export function ProblemTabBar({ activeTab, onChange }: ProblemTabBarProps) {
  return (
    <nav
      style={{
        display: 'flex',
        gap: 2,
        overflowX: 'auto',
        padding: '0 4px',
        scrollbarWidth: 'none',
        msOverflowStyle: 'none',
      }}
      aria-label="Chọn loại bài toán"
    >
      {TABS.map((tab) => {
        const isActive = activeTab === tab.id
        return (
          <button
            key={tab.id}
            type="button"
            id={`problem-tab-${tab.id}`}
            onClick={() => onChange(tab.id)}
            aria-selected={isActive}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              padding: '6px 14px',
              fontSize: '0.8125rem',
              fontWeight: isActive ? 600 : 500,
              fontFamily: 'var(--font-sans)',
              color: isActive ? tab.color : 'var(--text-tertiary)',
              background: isActive ? `${tab.color}12` : 'transparent',
              border: 'none',
              borderBottom: isActive ? `2px solid ${tab.color}` : '2px solid transparent',
              borderRadius: '4px 4px 0 0',
              cursor: 'pointer',
              whiteSpace: 'nowrap',
              transition: 'all 150ms ease',
              marginBottom: -1,
            }}
            onMouseEnter={(e) => {
              if (!isActive) {
                (e.currentTarget as HTMLButtonElement).style.color = tab.color
                ;(e.currentTarget as HTMLButtonElement).style.background = `${tab.color}08`
              }
            }}
            onMouseLeave={(e) => {
              if (!isActive) {
                (e.currentTarget as HTMLButtonElement).style.color = 'var(--text-tertiary)'
                ;(e.currentTarget as HTMLButtonElement).style.background = 'transparent'
              }
            }}
          >
            <span>{tab.icon}</span>
            <span className="tab-label-full">{tab.label}</span>
          </button>
        )
      })}
    </nav>
  )
}
