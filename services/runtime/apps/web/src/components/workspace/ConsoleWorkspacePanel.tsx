'use client';

import { useEffect, useState } from 'react';

import { apiGet } from '@/lib/api';
import { LoadingState, UnavailableState } from '@/components/state/SurfaceStates';
import { TraceDetailPanel } from '@/components/state/TraceDetailPanel';
import { ReviewOutcomePanel } from '@/components/features/reviews/ReviewOutcomePanel';
import { ReviewKnowledgePanel } from '@/components/features/reviews/ReviewKnowledgePanel';
import { RecommendationWorkspacePanel } from '@/components/features/reviews/RecommendationWorkspacePanel';
import { useWorkspaceContext } from '@/components/workspace/WorkspaceProvider';
import type { ReviewDetailResponse } from '@/types/api';

export function ConsoleWorkspacePanel() {
  const workspace = useWorkspaceContext();
  const [reviewDetail, setReviewDetail] = useState<ReviewDetailResponse | null>(null);
  const [status, setStatus] = useState<'idle' | 'loading' | 'ready' | 'unavailable'>('idle');

  useEffect(() => {
    const activeTab = workspace.activeTab;
    if (!activeTab || activeTab.type !== 'review_detail') {
      setReviewDetail(null);
      setStatus('idle');
      return;
    }
    let cancelled = false;
    const reviewId = activeTab.refId;
    async function loadReviewDetail() {
      setStatus('loading');
      try {
        const response = await apiGet<ReviewDetailResponse>(`/api/v1/reviews/${reviewId}`);
        if (!cancelled) {
          setReviewDetail(response);
          setStatus('ready');
        }
      } catch {
        if (!cancelled) {
          setReviewDetail(null);
          setStatus('unavailable');
        }
      }
    }
    void loadReviewDetail();
    return () => {
      cancelled = true;
    };
  }, [workspace.activeTab]);

  if (!workspace.activeTab) {
    return null;
  }

  return (
    <div className="glass" style={{ padding: '1rem', borderRadius: '14px', marginBottom: '1rem' }}>
      {workspace.activeTab.type === 'review_detail' && status === 'loading' ? (
        <LoadingState message="Loading review workspace detail..." />
      ) : null}
      {workspace.activeTab.type === 'review_detail' && status === 'unavailable' ? (
        <UnavailableState
          message="Review workspace detail is unavailable."
          detail="The current review detail API could not confirm the selected review."
        />
      ) : null}
      {workspace.activeTab.type === 'review_detail' && reviewDetail ? (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1rem' }}>
          <ReviewOutcomePanel detail={reviewDetail} />
          <ReviewKnowledgePanel detail={reviewDetail} />
        </div>
      ) : null}
      {workspace.activeTab.type === 'trace_detail' ? (
        <TraceDetailPanel
          path={
            workspace.activeTab.refId.startsWith('reco_')
              ? `/api/v1/traces/recommendations/${workspace.activeTab.refId}`
              : `/api/v1/traces/reviews/${workspace.activeTab.refId}`
          }
          buttonLabel="Show active trace detail"
        />
      ) : null}
      {workspace.activeTab.type === 'recommendation_detail' ? (
        <RecommendationWorkspacePanel recommendationId={workspace.activeTab.refId} />
      ) : null}
    </div>
  );
}
