'use client';

import { honestMissingCopy, semanticNote, trustTierForSignal } from '@/lib/semanticSignals';
import { TrustTierBadge } from '@/components/state/ProductSignals';
import type { ReviewDetailResponse } from '@/types/api';

export function ReviewKnowledgePanel({ detail }: { detail: ReviewDetailResponse }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
      <div style={{ display: 'flex', gap: '0.45rem', alignItems: 'center' }}>
        <TrustTierBadge tier={trustTierForSignal('knowledge_hint')} />
        <span style={{ color: 'var(--foreground)', fontWeight: 600 }}>Knowledge feedback</span>
      </div>
      <div>Packet id: {detail.knowledge_feedback_packet_id ?? honestMissingCopy('knowledge_hint')}</div>
      <div>Governance hints: {detail.governance_hint_count}</div>
      <div>Intelligence hints: {detail.intelligence_hint_count}</div>
      <div>{semanticNote('knowledge_hint')}</div>
    </div>
  );
}
