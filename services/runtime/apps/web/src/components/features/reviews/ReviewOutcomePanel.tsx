'use client';

import { honestMissingCopy, semanticNote, trustTierForSignal } from '@/lib/semanticSignals';
import { TrustTierBadge } from '@/components/state/ProductSignals';
import type { ReviewDetailResponse } from '@/types/api';

export function ReviewOutcomePanel({ detail }: { detail: ReviewDetailResponse }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
      <div style={{ display: 'flex', gap: '0.45rem', alignItems: 'center' }}>
        <TrustTierBadge tier={trustTierForSignal('outcome_signal')} />
        <span style={{ color: 'var(--foreground)', fontWeight: 600 }}>Outcome signal</span>
      </div>
      <div>Status: {detail.latest_outcome_status ?? honestMissingCopy('outcome_signal')}</div>
      <div>Reason: {detail.latest_outcome_reason ?? honestMissingCopy('outcome_signal')}</div>
      <div>{semanticNote('outcome_signal')}</div>
    </div>
  );
}
