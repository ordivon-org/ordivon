'use client';

import { useEffect } from 'react';
import { useSearchParams } from 'next/navigation';

import { useWorkspaceContext } from '@/components/workspace/WorkspaceProvider';

export function ConsoleWorkspaceSeed() {
  const searchParams = useSearchParams();
  const workspace = useWorkspaceContext();

  useEffect(() => {
    const reviewId = searchParams.get('review_id');
    const recommendationId = searchParams.get('recommendation_id');
    const traceRef = searchParams.get('trace_ref');

    if (reviewId) {
      workspace.openTab({
        id: `review:${reviewId}`,
        type: 'review_detail',
        title: `Review ${reviewId}`,
        refId: reviewId,
      });
    }

    if (recommendationId) {
      workspace.openTab({
        id: `recommendation:${recommendationId}`,
        type: 'recommendation_detail',
        title: `Recommendation ${recommendationId}`,
        refId: recommendationId,
      });
    }

    if (traceRef) {
      workspace.openTab({
        id: `trace:${traceRef}`,
        type: 'trace_detail',
        title: `Trace ${traceRef}`,
        refId: traceRef,
      });
    }
  }, [searchParams, workspace]);

  return null;
}
