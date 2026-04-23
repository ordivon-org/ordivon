import type { ReactElement, ReactNode } from 'react';

import { render } from '@testing-library/react';

import { WorkspaceProvider } from '@/components/workspace/WorkspaceProvider';

export function renderWithWorkspace(ui: ReactElement) {
  return render(<WorkspaceProvider>{ui}</WorkspaceProvider>);
}

export function WorkspaceHarness({ children }: { children: ReactNode }) {
  return <WorkspaceProvider>{children}</WorkspaceProvider>;
}
