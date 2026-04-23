'use client';

import { useEffect, useState } from 'react';

import { apiGet } from '@/lib/api';
import { honestMissingCopy, semanticNote, trustTierForSignal } from '@/lib/semanticSignals';
import { TrustTierBadge } from '@/components/state/ProductSignals';
import { LoadingState } from '@/components/state/SurfaceStates';
import type { KnowledgeRetrieveResponse, ReviewDetailResponse } from '@/types/api';

export function ReviewKnowledgePanel({ detail }: { detail: ReviewDetailResponse }) {
  const [knowledge, setKnowledge] = useState<KnowledgeRetrieveResponse | null>(null);
  const [status, setStatus] = useState<'loading' | 'ready' | 'unavailable'>('loading');

  useEffect(() => {
    let cancelled = false;
    async function loadKnowledge() {
      try {
        const response = await apiGet<KnowledgeRetrieveResponse>(`/api/v1/knowledge/reviews/${detail.id}`);
        if (!cancelled) {
          setKnowledge(response);
          setStatus('ready');
        }
      } catch {
        if (!cancelled) {
          setKnowledge(null);
          setStatus('unavailable');
        }
      }
    }
    void loadKnowledge();
    return () => {
      cancelled = true;
    };
  }, [detail.id]);

  if (status === 'loading') {
    return <LoadingState message="Loading knowledge advisory detail..." />;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
      <div style={{ display: 'flex', gap: '0.45rem', alignItems: 'center' }}>
        <TrustTierBadge tier={trustTierForSignal('knowledge_hint')} />
        <span style={{ color: 'var(--foreground)', fontWeight: 600 }}>Knowledge feedback</span>
      </div>
      <div>Packet id: {detail.knowledge_feedback_packet_id ?? honestMissingCopy('knowledge_hint')}</div>
      <div>Governance hints: {detail.governance_hint_count}</div>
      <div>Intelligence hints: {detail.intelligence_hint_count}</div>
      <div>Knowledge entries: {knowledge?.entries.length ?? 0}</div>
      <div>Recurring issues: {knowledge?.recurring_issues.length ?? 0}</div>
      <div>Candidate rules: {knowledge?.candidate_rules.length ?? 0}</div>
      {knowledge?.entries[0] ? (
        <div style={{ color: 'var(--text-muted)', fontSize: '0.72rem', lineHeight: '1.4' }}>
          Latest advisory: {knowledge.entries[0].title}
        </div>
      ) : null}
      <div>{semanticNote('knowledge_hint')}</div>
      <div style={{ color: 'var(--text-muted)', fontSize: '0.72rem', lineHeight: '1.4' }}>
        Advisory-only retrieval. Candidate rules and recurring issues support supervision but do not become policy or truth here.
      </div>
    </div>
  );
}
