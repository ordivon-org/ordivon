'use client';

import { useCallback, useMemo, useState } from 'react';

import type { WorkspaceTab } from '@/components/workspace/types';

export function useWorkspaceTabs(initialTabs: WorkspaceTab[] = []) {
  const [tabs, setTabs] = useState<WorkspaceTab[]>(initialTabs);
  const [activeTabId, setActiveTabId] = useState<string | null>(initialTabs[0]?.id ?? null);

  const activeTab = useMemo(
    () => tabs.find((tab) => tab.id === activeTabId) ?? null,
    [activeTabId, tabs],
  );

  const openTab = useCallback((tab: WorkspaceTab) => {
    setTabs((existing) => (existing.some((item) => item.id === tab.id) ? existing : [...existing, tab]));
    setActiveTabId((current) => (current === tab.id ? current : tab.id));
  }, []);

  const replaceTabs = useCallback((nextTabs: WorkspaceTab[]) => {
    setTabs(nextTabs);
    setActiveTabId(nextTabs[0]?.id ?? null);
  }, []);

  const closeTab = useCallback((tabId: string) => {
    setTabs((existing) => {
      const next = existing.filter((tab) => tab.id !== tabId);
      setActiveTabId((current) => (current === tabId ? next[0]?.id ?? null : current));
      return next;
    });
  }, []);

  return useMemo(
    () => ({
      tabs,
      activeTab,
      activeTabId,
      openTab,
      replaceTabs,
      closeTab,
      setActiveTabId,
    }),
    [activeTab, activeTabId, closeTab, openTab, replaceTabs, tabs],
  );
}
