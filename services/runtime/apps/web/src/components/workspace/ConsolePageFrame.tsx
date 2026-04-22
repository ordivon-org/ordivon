'use client';

import { Suspense, type ReactNode } from 'react';

import Sidebar from '@/components/layout/Sidebar';
import { ConsoleWorkspaceSeed } from '@/components/workspace/ConsoleWorkspaceSeed';
import { WorkspaceTabs } from '@/components/workspace/WorkspaceTabs';
import { ConsoleWorkspacePanel } from '@/components/workspace/ConsoleWorkspacePanel';
import { useWorkspaceContext } from '@/components/workspace/WorkspaceProvider';

export function ConsolePageFrame({ children }: { children: ReactNode }) {
  const workspace = useWorkspaceContext();

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <Sidebar />
      <main style={{ flex: 1, padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <Suspense fallback={null}>
          <ConsoleWorkspaceSeed />
        </Suspense>
        {workspace.tabs.length > 0 ? (
          <WorkspaceTabs
            tabs={workspace.tabs}
            activeTabId={workspace.activeTabId}
            onSelect={workspace.setActiveTabId}
            onClose={workspace.closeTab}
          />
        ) : null}
        <ConsoleWorkspacePanel />
        {children}
      </main>
    </div>
  );
}
