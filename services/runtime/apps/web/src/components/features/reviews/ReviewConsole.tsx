'use client';

import { useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';

import { apiGet } from '@/lib/api';
import { ReviewQueue } from '@/components/features/reviews/ReviewQueue';
import { ReviewOutcomePanel } from '@/components/features/reviews/ReviewOutcomePanel';
import { ReviewKnowledgePanel } from '@/components/features/reviews/ReviewKnowledgePanel';
import { RecommendationWorkspacePanel } from '@/components/features/reviews/RecommendationWorkspacePanel';
import { TraceDetailPanel } from '@/components/state/TraceDetailPanel';
import { LoadingState, UnavailableState } from '@/components/state/SurfaceStates';
import { WorkspaceShell } from '@/components/workspace/WorkspaceShell';
import { WorkspaceTabs } from '@/components/workspace/WorkspaceTabs';
import { useWorkspaceTabs } from '@/components/workspace/useWorkspaceTabs';
import type { PendingReviewItem, PendingReviewListResponse, ReviewDetailResponse } from '@/types/api';

export function ReviewConsole() {
  const searchParams = useSearchParams();
  const [reviews, setReviews] = useState<PendingReviewItem[]>([]);
  const [selectedReviewId, setSelectedReviewId] = useState<string | null>(null);
  const [detail, setDetail] = useState<ReviewDetailResponse | null>(null);
  const [status, setStatus] = useState<'loading' | 'ready' | 'unavailable'>('loading');
  const workspace = useWorkspaceTabs();

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
        const first = requestedReviewId && response.reviews?.some((item) => item.id === requestedReviewId)
          ? requestedReviewId
          : response.reviews?.[0]?.id ?? null;
        setSelectedReviewId(first);
        if (first) {
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
          workspace.replaceTabs(initialTabs);
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
  }, [searchParams]);

  useEffect(() => {
    if (!selectedReviewId) {
      setDetail(null);
      return;
    }
    let cancelled = false;
    async function loadDetail() {
      try {
        const response = await apiGet<ReviewDetailResponse>(`/api/v1/reviews/${selectedReviewId}`);
        if (!cancelled) {
          setDetail(response);
        }
      } catch {
        if (!cancelled) {
          setDetail(null);
        }
      }
    }
    void loadDetail();
    return () => {
      cancelled = true;
    };
  }, [selectedReviewId]);

  if (status === 'loading') {
    return <LoadingState message="Loading review console..." />;
  }

  if (status === 'unavailable') {
    return (
      <UnavailableState
        message="Review console is unavailable."
        detail="The review and trace APIs could not be confirmed."
      />
    );
  }

  return (
    <WorkspaceShell
      title="Review Console"
      tabs={
        <WorkspaceTabs
          tabs={workspace.tabs}
          activeTabId={workspace.activeTabId}
          onSelect={workspace.setActiveTabId}
          onClose={workspace.closeTab}
        />
      }
    >
      <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '1rem' }}>
        <ReviewQueue
          reviews={reviews}
          selectedReviewId={selectedReviewId}
          onSelect={(reviewId) => {
            setSelectedReviewId(reviewId);
            workspace.openTab({
              id: `review:${reviewId}`,
              type: 'review_detail',
              title: `Review ${reviewId}`,
              refId: reviewId,
            });
            workspace.openTab({
              id: `trace:${reviewId}`,
              type: 'trace_detail',
              title: `Trace ${reviewId}`,
              refId: reviewId,
            });
            const selected = reviews.find((item) => item.id === reviewId);
            if (selected?.recommendation_id) {
              workspace.openTab({
                id: `recommendation:${selected.recommendation_id}`,
                type: 'recommendation_detail',
                title: `Recommendation ${selected.recommendation_id}`,
                refId: selected.recommendation_id,
              });
            }
          }}
        />
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {workspace.activeTab?.type === 'review_detail' && detail ? (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1rem' }}>
              <ReviewOutcomePanel detail={detail} />
              <ReviewKnowledgePanel detail={detail} />
            </div>
          ) : null}
          {workspace.activeTab?.type === 'trace_detail' && detail ? (
            <TraceDetailPanel path={`/api/v1/traces/reviews/${detail.id}`} buttonLabel="Show review trace" />
          ) : null}
          {workspace.activeTab?.type === 'recommendation_detail' ? (
            <RecommendationWorkspacePanel recommendationId={workspace.activeTab.refId} />
          ) : null}
          {!workspace.activeTab && !detail ? (
            <UnavailableState
              message="No review detail is selected."
              detail="Choose a review from the queue to inspect outcome, knowledge feedback, and trace refs."
            />
          ) : null}
        </div>
      </div>
    </WorkspaceShell>
  );
}
