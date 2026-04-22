import Link from 'next/link';

import { ConsolePageFrame } from '@/components/workspace/ConsolePageFrame';

export default function HistoryPage() {
  return (
    <ConsolePageFrame>
      <div className="history-page glass" style={{ padding: '2rem', borderRadius: '12px' }}>
        <header style={{ marginBottom: '2rem' }}>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 'bold' }}>Intelligence History</h1>
          <p style={{ color: 'var(--text-muted)' }}>
            Historical navigation is not exposed as a standalone product page yet.
          </p>
        </header>

        <div
          style={{
            padding: '2rem',
            border: '1px dashed var(--border-color)',
            borderRadius: '8px',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.85rem',
          }}
        >
          <div style={{ fontSize: '1rem', fontWeight: '600' }}>Not Exposed Yet</div>
          <p style={{ color: 'var(--text-muted)', lineHeight: '1.6', margin: 0 }}>
            This route does not have a dedicated history API or page-level data source in the current product surface.
          </p>
          <p style={{ color: 'var(--text-muted)', lineHeight: '1.6', margin: 0 }}>
            Use the real, currently exposed entry points below to inspect recent system activity.
          </p>

          <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', marginTop: '0.5rem' }}>
            <Link
              href="/audits"
              style={{
                padding: '0.65rem 0.9rem',
                borderRadius: '6px',
                border: '1px solid var(--border-color)',
                color: 'var(--foreground)',
                textDecoration: 'none',
                background: 'rgba(255,255,255,0.04)',
              }}
            >
              Open Audits
            </Link>
            <Link
              href="/reports"
              style={{
                padding: '0.65rem 0.9rem',
                borderRadius: '6px',
                border: '1px solid var(--border-color)',
                color: 'var(--foreground)',
                textDecoration: 'none',
                background: 'rgba(255,255,255,0.04)',
              }}
            >
              Open Reports
            </Link>
          </div>
        </div>
      </div>
    </ConsolePageFrame>
  );
}
