'use client';

import { useMemo, useState } from 'react';

import type { WorkspaceTab } from '@/components/workspace/types';

export function useWorkspaceTabs(initialTabs: WorkspaceTab[] = []) {
  const [tabs, setTabs] = useState<WorkspaceTab[]>(initialTabs);
  const [activeTabId, setActiveTabId] = useState<string | null>(initialTabs[0]?.id ?? null);

  const activeTab = useMemo(
    () => tabs.find((tab) => tab.id === activeTabId) ?? null,
    [activeTabId, tabs],
  );

  function openTab(tab: WorkspaceTab) {
    setTabs((existing) => (existing.some((item) => item.id === tab.id) ? existing : [...existing, tab]));
    setActiveTabId(tab.id);
  }

  function replaceTabs(nextTabs: WorkspaceTab[]) {
    setTabs(nextTabs);
    setActiveTabId(nextTabs[0]?.id ?? null);
  }

  function closeTab(tabId: string) {
    setTabs((existing) => {
      const next = existing.filter((tab) => tab.id !== tabId);
      if (activeTabId === tabId) {
        setActiveTabId(next[0]?.id ?? null);
      }
      return next;
    });
  }

  return {
    tabs,
    activeTab,
    activeTabId,
    openTab,
    replaceTabs,
    closeTab,
    setActiveTabId,
  };
}
