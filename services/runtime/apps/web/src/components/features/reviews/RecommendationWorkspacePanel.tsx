'use client';

import { useEffect, useState } from 'react';

import { apiGet } from '@/lib/api';
import { TraceDetailPanel } from '@/components/state/TraceDetailPanel';
import { LoadingState, UnavailableState } from '@/components/state/SurfaceStates';
import { honestMissingCopy, semanticNote, trustTierForSignal } from '@/lib/semanticSignals';
import { TrustTierBadge } from '@/components/state/ProductSignals';
import type { RecommendationItem } from '@/types/api';

export function RecommendationWorkspacePanel({ recommendationId }: { recommendationId: string }) {
  const [recommendation, setRecommendation] = useState<RecommendationItem | null>(null);
  const [status, setStatus] = useState<'loading' | 'ready' | 'unavailable'>('loading');

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const response = await apiGet<RecommendationItem>(`/api/v1/recommendations/${recommendationId}`);
        if (cancelled) {
          return;
        }
        setRecommendation(response);
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
  }, [recommendationId]);

  if (status === 'loading') {
    return <LoadingState message="Loading recommendation detail..." />;
  }

  if (!recommendation) {
    return (
      <UnavailableState
        message="Recommendation detail is unavailable."
        detail="The current recommendation list did not expose a matching object."
      />
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
      <div style={{ display: 'flex', gap: '0.45rem', alignItems: 'center' }}>
        <TrustTierBadge tier="inference" />
        <span style={{ color: 'var(--foreground)', fontWeight: 600 }}>Recommendation detail</span>
      </div>
      <div>Id: {recommendation.id}</div>
      <div>Status: {recommendation.status}</div>
      <div>Symbol: {recommendation.symbol ?? honestMissingCopy('trace_detail')}</div>
      <div>Review status: {recommendation.review_status ?? honestMissingCopy('trace_detail')}</div>
      <div>Outcome signal: {recommendation.outcome_status ?? honestMissingCopy('outcome_signal')}</div>
      <div>Knowledge hints: {typeof recommendation.metadata?.knowledge_hint_count === 'number' ? recommendation.metadata.knowledge_hint_count : 0}</div>
      <div style={{ display: 'flex', gap: '0.45rem', alignItems: 'center' }}>
        <TrustTierBadge tier={trustTierForSignal('outcome_signal')} />
        <span>{semanticNote('outcome_signal')}</span>
      </div>
      <TraceDetailPanel path={`/api/v1/traces/recommendations/${recommendation.id}`} buttonLabel="Show recommendation trace" />
    </div>
  );
}
