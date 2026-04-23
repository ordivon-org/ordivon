'use client';

import { useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';

import { apiGet } from '@/lib/api';
import { ReviewQueue } from '@/components/features/reviews/ReviewQueue';
import { LoadingState, UnavailableState } from '@/components/state/SurfaceStates';
import { useWorkspaceContext } from '@/components/workspace/WorkspaceProvider';
import type { PendingReviewItem, PendingReviewListResponse } from '@/types/api';

export function ReviewConsole() {
  const searchParams = useSearchParams();
  const [reviews, setReviews] = useState<PendingReviewItem[]>([]);
  const [selectedReviewId, setSelectedReviewId] = useState<string | null>(null);
  const [status, setStatus] = useState<'loading' | 'ready' | 'unavailable'>('loading');
  const { activeTab, openTab, replaceTabs } = useWorkspaceContext();

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const response = await apiGet<PendingReviewListResponse>('/api/v1/reviews/pending?limit=20');
        if (cancelled) {
          return;
        }
        setReviews(response.reviews ?? []);
        const requestedReviewId = searchParams.get('review_id');
        const requestedRecommendationId = searchParams.get('recommendation_id');
        const requestedTraceRef = searchParams.get('trace_ref');
        const reviewForRecommendation =
          requestedRecommendationId
            ? response.reviews?.find((item) => item.recommendation_id === requestedRecommendationId)?.id ?? null
            : null;
        const first =
          requestedReviewId && response.reviews?.some((item) => item.id === requestedReviewId)
            ? requestedReviewId
            : reviewForRecommendation ?? response.reviews?.[0]?.id ?? null;
        setSelectedReviewId(first);
        if (first && !requestedRecommendationId && !requestedTraceRef) {
          const initialTabs = [
            {
              id: `review:${first}`,
              type: 'review_detail' as const,
              title: `Review ${first}`,
              refId: first,
            },
            {
              id: `trace:${first}`,
              type: 'trace_detail' as const,
              title: `Trace ${first}`,
              refId: first,
            },
          ];
          replaceTabs(initialTabs);
        }
        setStatus('ready');
      } catch {
        if (!cancelled) {
          setStatus('unavailable');
        }
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, [replaceTabs, searchParams]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <header>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '0.4rem' }}>Review Workbench</h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
          Primary supervision workspace for pending reviews, linked recommendation follow-through, and trace or outcome inspection.
        </p>
      </header>
      <div
        className="glass"
        style={{
          padding: '0.85rem 1rem',
          borderRadius: '10px',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.35rem',
          color: 'var(--text-muted)',
          fontSize: '0.8rem',
        }}
      >
        <div style={{ color: 'var(--foreground)', fontWeight: 600 }}>Queue-first supervision</div>
        <div>
          Use the review queue as the primary entrypoint here. Recommendation and trace tabs are supporting views for supervision work, not separate ownership surfaces.
        </div>
      </div>
      {status === 'loading' ? (
        <LoadingState message="Loading review console..." />
      ) : null}
      {status === 'unavailable' ? (
        <UnavailableState
          message="Review console is unavailable."
          detail="The review and trace APIs could not be confirmed."
        />
      ) : null}
      {status === 'ready' ? (
      <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '1rem' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
            Pending Review Queue
          </div>
          <ReviewQueue
            reviews={reviews}
            selectedReviewId={selectedReviewId}
            onSelect={(reviewId) => {
              setSelectedReviewId(reviewId);
              openTab({
                id: `review:${reviewId}`,
                type: 'review_detail',
                title: `Review ${reviewId}`,
                refId: reviewId,
              });
              openTab({
                id: `trace:${reviewId}`,
                type: 'trace_detail',
                title: `Trace ${reviewId}`,
                refId: reviewId,
              });
              const selected = reviews.find((item) => item.id === reviewId);
              if (selected?.recommendation_id) {
                openTab({
                  id: `recommendation:${selected.recommendation_id}`,
                  type: 'recommendation_detail',
                  title: `Recommendation ${selected.recommendation_id}`,
                  refId: selected.recommendation_id,
                });
              }
            }}
          />
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
            Supporting Views
          </div>
          {!activeTab ? (
            <UnavailableState
              message="No review detail is selected."
              detail="Choose a review from the queue to inspect outcome, knowledge feedback, and trace refs in supporting tabs."
            />
          ) : null}
        </div>
      </div>
      ) : null}
    </div>
  );
}
