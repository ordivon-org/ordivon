'use client';

import type { ReactNode } from 'react';

import Sidebar from '@/components/layout/Sidebar';

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="app-shell">
      <Sidebar />
      <main className="app-shell__main">{children}</main>
    </div>
  );
}
