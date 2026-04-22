'use client';

import { createContext, useContext, type ReactNode } from 'react';

import { useWorkspaceTabs } from '@/components/workspace/useWorkspaceTabs';


type WorkspaceContextValue = ReturnType<typeof useWorkspaceTabs>;

const WorkspaceContext = createContext<WorkspaceContextValue | null>(null);

export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const workspace = useWorkspaceTabs();
  return <WorkspaceContext.Provider value={workspace}>{children}</WorkspaceContext.Provider>;
}

export function useWorkspaceContext() {
  const value = useContext(WorkspaceContext);
  if (!value) {
    throw new Error('useWorkspaceContext must be used within WorkspaceProvider');
  }
  return value;
}
