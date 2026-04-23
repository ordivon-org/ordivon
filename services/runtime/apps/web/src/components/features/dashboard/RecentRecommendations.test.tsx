import type { ReactNode } from 'react';

import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';

import RecentRecommendations from '@/components/features/dashboard/RecentRecommendations';
import { useWorkspaceContext, WorkspaceProvider } from '@/components/workspace/WorkspaceProvider';

const { apiGet } = vi.hoisted(() => ({
  apiGet: vi.fn(),
}));

vi.mock('@/lib/api', () => ({
  apiGet,
}));

vi.mock('next/link', () => ({
  default: ({ children, href, ...props }: { children: ReactNode; href: string }) => (
    <a href={href} {...props}>
      {children}
    </a>
  ),
}));

function WorkspaceInspector() {
  const workspace = useWorkspaceContext();
  return <div data-testid="workspace-tab-count">{workspace.tabs.length}</div>;
}

describe('RecentRecommendations', () => {
  test('stays preview-oriented while opening supporting workspace tabs', async () => {
    apiGet.mockResolvedValueOnce({
      recommendations: [
        {
          id: 'reco_test_1',
          status: 'review_pending',
          created_at: '2026-04-23T10:00:00Z',
          analysis_id: 'analysis_1',
          symbol: 'BTC/USDT',
          action_summary: 'Track continuation',
          confidence: 0.82,
          decision: 'execute',
          decision_reason: 'Passed validation.',
          adopted: false,
          review_status: 'pending',
          outcome_status: null,
          metadata: {},
        },
      ],
    });

    render(
      <WorkspaceProvider>
        <RecentRecommendations />
        <WorkspaceInspector />
      </WorkspaceProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText(/Command-center preview of recommendation objects\./i)).toBeVisible();
    });
    expect(screen.getByRole('link', { name: 'Continue in review workbench' })).toHaveAttribute(
      'href',
      '/reviews?recommendation_id=reco_test_1',
    );

    fireEvent.click(screen.getByRole('button', { name: 'Open supporting recommendation tab' }));

    expect(screen.getByTestId('workspace-tab-count')).toHaveTextContent('1');
  });
});
