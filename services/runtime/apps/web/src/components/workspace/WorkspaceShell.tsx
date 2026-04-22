'use client';

import type { ReactNode } from 'react';

export function WorkspaceShell({
  title,
  tabs,
  children,
}: {
  title: string;
  tabs: ReactNode;
  children: ReactNode;
}) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <header>
        <h1 style={{ fontSize: '1.6rem', fontWeight: 700 }}>{title}</h1>
      </header>
      {tabs}
      <div className="glass" style={{ padding: '1rem', borderRadius: '14px' }}>
        {children}
      </div>
    </div>
  );
}
