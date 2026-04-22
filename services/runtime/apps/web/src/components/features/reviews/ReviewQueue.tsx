'use client';

import type { PendingReviewItem } from '@/types/api';

export function ReviewQueue({
  reviews,
  selectedReviewId,
  onSelect,
}: {
  reviews: PendingReviewItem[];
  selectedReviewId: string | null;
  onSelect: (reviewId: string) => void;
}) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
      {reviews.map((review) => (
        <button
          key={review.id}
          type="button"
          onClick={() => onSelect(review.id)}
          style={{
            textAlign: 'left',
            padding: '0.8rem',
            borderRadius: '10px',
            border: `1px solid ${selectedReviewId === review.id ? 'var(--primary)' : 'var(--border-color)'}`,
            background: selectedReviewId === review.id ? 'rgba(255,255,255,0.04)' : 'transparent',
            color: 'var(--foreground)',
            cursor: 'pointer',
          }}
        >
          <div style={{ fontWeight: 600 }}>{review.review_type}</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Recommendation: {review.recommendation_id ?? 'not linked yet'}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Status: {review.status}</div>
        </button>
      ))}
    </div>
  );
}
