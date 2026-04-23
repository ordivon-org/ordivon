import { render, screen, waitFor } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';

import { ReviewConsole } from '@/components/features/reviews/ReviewConsole';
import { WorkspaceProvider } from '@/components/workspace/WorkspaceProvider';

const { apiGet, useSearchParams } = vi.hoisted(() => ({
  apiGet: vi.fn(),
  useSearchParams: vi.fn(),
}));

vi.mock('@/lib/api', () => ({
  apiGet,
}));

vi.mock('next/navigation', () => ({
  useSearchParams: () => useSearchParams(),
}));

describe('ReviewConsole', () => {
  test('keeps queue-first supervision and honors recommendation handoff params', async () => {
    useSearchParams.mockReturnValue(
      new URLSearchParams('recommendation_id=reco_seed_2'),
    );
    apiGet.mockResolvedValueOnce({
      reviews: [
        {
          id: 'review_seed_1',
          recommendation_id: 'reco_seed_1',
          review_type: 'recommendation_postmortem',
          status: 'pending',
          expected_outcome: 'Review first object',
          created_at: '2026-04-23T11:00:00Z',
          workflow_run_id: null,
          intelligence_run_id: null,
          recommendation_generate_receipt_id: null,
          latest_outcome_status: null,
          latest_outcome_reason: null,
          knowledge_hint_count: 0,
        },
        {
          id: 'review_seed_2',
          recommendation_id: 'reco_seed_2',
          review_type: 'trace_followup',
          status: 'pending',
          expected_outcome: 'Review handoff object',
          created_at: '2026-04-23T11:00:00Z',
          workflow_run_id: null,
          intelligence_run_id: null,
          recommendation_generate_receipt_id: null,
          latest_outcome_status: null,
          latest_outcome_reason: null,
          knowledge_hint_count: 0,
        },
      ],
    });

    render(
      <WorkspaceProvider>
        <ReviewConsole />
      </WorkspaceProvider>,
    );

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Review Workbench' })).toBeVisible();
    });
    expect(screen.getByText('Queue-first supervision')).toBeVisible();
    expect(screen.getByText('Pending Review Queue')).toBeVisible();
    expect(screen.getByText('Supporting Views')).toBeVisible();
    expect(screen.getByRole('button', { name: /trace_followup/i })).toBeVisible();
  });
});
