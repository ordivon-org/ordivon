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
  const [status, setStatus] = useState<'idle' | 'ready' | 'unavailable'>('idle');
  const activeReviewId = workspace.activeTab?.type === 'review_detail' ? workspace.activeTab.refId : null;
  const activeReviewDetail = activeReviewId && reviewDetail?.id === activeReviewId ? reviewDetail : null;

  useEffect(() => {
    if (!activeReviewId) {
      return;
    }
    let cancelled = false;
    async function loadReviewDetail() {
      try {
        const response = await apiGet<ReviewDetailResponse>(`/api/v1/reviews/${activeReviewId}`);
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
  }, [activeReviewId]);

  if (!workspace.activeTab) {
    return null;
  }

  return (
    <div className="glass" style={{ padding: '1rem', borderRadius: '14px', marginBottom: '1rem' }}>
      {workspace.activeTab.type === 'review_detail' && !activeReviewDetail && status !== 'unavailable' ? (
        <LoadingState message="Loading review workspace detail..." />
      ) : null}
      {workspace.activeTab.type === 'review_detail' && status === 'unavailable' ? (
        <UnavailableState
          message="Review workspace detail is unavailable."
          detail="The current review detail API could not confirm the selected review."
        />
      ) : null}
      {workspace.activeTab.type === 'review_detail' && activeReviewDetail ? (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1rem' }}>
          <ReviewOutcomePanel detail={activeReviewDetail} />
          <ReviewKnowledgePanel detail={activeReviewDetail} />
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
