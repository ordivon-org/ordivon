'use client';

import type { WorkspaceTab } from '@/components/workspace/types';

export function WorkspaceTabs({
  tabs,
  activeTabId,
  onSelect,
  onClose,
}: {
  tabs: WorkspaceTab[];
  activeTabId: string | null;
  onSelect: (tabId: string) => void;
  onClose: (tabId: string) => void;
}) {
  return (
    <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '1rem' }}>
      {tabs.map((tab) => (
        <div
          key={tab.id}
          style={{
            display: 'inline-flex',
            gap: '0.45rem',
            alignItems: 'center',
            padding: '0.4rem 0.65rem',
            borderRadius: '999px',
            border: `1px solid ${activeTabId === tab.id ? 'var(--primary)' : 'var(--border-color)'}`,
            background: activeTabId === tab.id ? 'rgba(255,255,255,0.05)' : 'transparent',
          }}
        >
          <button
            type="button"
            onClick={() => onSelect(tab.id)}
            style={{ background: 'transparent', border: 'none', color: 'var(--foreground)', cursor: 'pointer' }}
          >
            {tab.title}
          </button>
          <button
            type="button"
            aria-label={`Close ${tab.title} tab`}
            onClick={() => onClose(tab.id)}
            style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
          >
            ×
          </button>
        </div>
      ))}
    </div>
  );
}
