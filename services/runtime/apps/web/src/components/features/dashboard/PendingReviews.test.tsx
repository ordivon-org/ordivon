import type { ReactNode } from 'react';

import { render, screen, waitFor } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';

import PendingReviews from '@/components/features/dashboard/PendingReviews';

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

describe('PendingReviews', () => {
  test('routes previewed review work into the review workbench', async () => {
    apiGet.mockResolvedValueOnce({
      reviews: [
        {
          id: 'review_1',
          recommendation_id: 'reco_1',
          review_type: 'recommendation_postmortem',
          status: 'pending',
          expected_outcome: 'Track follow-through',
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

    render(<PendingReviews />);

    await waitFor(() => {
      expect(screen.getByText(/Command-center preview of supervision-needed review objects\./i)).toBeVisible();
    });
    expect(screen.getByRole('link', { name: 'Continue in review workbench' })).toHaveAttribute(
      'href',
      '/reviews?review_id=review_1&trace_ref=review_1',
    );
  });
});
