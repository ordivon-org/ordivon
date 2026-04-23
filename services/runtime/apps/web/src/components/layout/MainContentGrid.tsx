import type { CSSProperties, ReactNode } from 'react';

export function MainContentGrid({
  columns = 'two-up',
  children,
}: {
  columns?: 'two-up' | 'three-up' | 'sidebar-main' | 'main-detail';
  children: ReactNode;
}) {
  const styles: Record<typeof columns, CSSProperties> = {
    'two-up': {
      gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))',
    },
    'three-up': {
      gridTemplateColumns: '280px minmax(0, 1fr) 320px',
    },
    'sidebar-main': {
      gridTemplateColumns: '320px minmax(0, 1fr)',
    },
    'main-detail': {
      gridTemplateColumns: 'minmax(0, 1fr) 320px',
    },
  };

  return (
    <div className="main-content-grid" style={styles[columns]}>
      {children}
    </div>
  );
}

export function RightDetailPanel({ children }: { children: ReactNode }) {
  return <div className="right-detail-panel">{children}</div>;
}
