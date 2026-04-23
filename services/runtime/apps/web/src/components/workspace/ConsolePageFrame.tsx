'use client';

import { Suspense, type ReactNode } from 'react';

import { AppShell } from '@/components/layout/AppShell';
import { ConsoleWorkspaceSeed } from '@/components/workspace/ConsoleWorkspaceSeed';
import { WorkspaceTabs } from '@/components/workspace/WorkspaceTabs';
import { ConsoleWorkspacePanel } from '@/components/workspace/ConsoleWorkspacePanel';
import { useWorkspaceContext } from '@/components/workspace/WorkspaceProvider';

export function ConsolePageFrame({ children }: { children: ReactNode }) {
  const workspace = useWorkspaceContext();

  return (
    <AppShell>
      <div className="console-frame">
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
      </div>
    </AppShell>
  );
}
