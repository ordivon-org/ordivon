'use client';

import { useState } from 'react';

import { apiGet } from '@/lib/api';
import { honestMissingCopy, semanticNote, trustTierForSignal } from '@/lib/semanticSignals';
import { LoadingState, UnavailableState } from '@/components/state/SurfaceStates';
import { TrustTierBadge } from '@/components/state/ProductSignals';
import type { ReviewDetailResponse } from '@/types/api';

export function ReviewDetailPanel({ reviewId }: { reviewId: string }) {
  const [expanded, setExpanded] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [detail, setDetail] = useState<ReviewDetailResponse | null>(null);

  const toggle = async () => {
    if (expanded) {
      setExpanded(false);
      return;
    }
    setExpanded(true);
    if (detail || loading) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const result = await apiGet<ReviewDetailResponse>(`/api/v1/reviews/${reviewId}`);
      setDetail(result);
    } catch (err) {
      console.error('Failed to load review detail:', err);
      setError('Review detail is unavailable.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ marginTop: '0.55rem', display: 'flex', flexDirection: 'column', gap: '0.45rem' }}>
      <button
        type="button"
        onClick={() => {
          void toggle();
        }}
        style={{
          alignSelf: 'flex-start',
          padding: '4px 8px',
          borderRadius: '6px',
          border: '1px solid var(--border-color)',
          background: 'transparent',
          color: 'var(--text-muted)',
          fontSize: '0.72rem',
          cursor: 'pointer',
        }}
      >
        {expanded ? 'Hide review detail' : 'Show review detail'}
      </button>
      {expanded && loading ? <LoadingState message="Loading review detail..." /> : null}
      {expanded && error ? <UnavailableState message={error} detail="The surface cannot confirm missing review links beyond the current detail API result." /> : null}
      {expanded && detail ? (
        <div
          style={{
            padding: '0.75rem',
            border: '1px dashed var(--border-color)',
            borderRadius: '10px',
            background: 'rgba(255,255,255,0.02)',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.35rem',
            fontSize: '0.72rem',
            color: 'var(--text-muted)',
          }}
        >
          <div style={{ color: 'var(--foreground)', fontWeight: 600 }}>Review detail</div>
          <div>Status: {detail.status}</div>
          <div>Review type: {detail.review_type}</div>
          <div>Verdict: {detail.verdict ?? honestMissingCopy('trace_detail')}</div>
          <div>Observed outcome: {detail.observed_outcome ?? honestMissingCopy('outcome_signal')}</div>
          <div>Variance summary: {detail.variance_summary ?? honestMissingCopy('outcome_signal')}</div>
          <div>Cause tags: {detail.cause_tags.length > 0 ? detail.cause_tags.join(', ') : honestMissingCopy('trace_detail')}</div>
          <div>Lessons captured: {detail.lessons.length}</div>
          <div>Follow-up actions: {detail.followup_actions.length}</div>

          <div style={{ display: 'flex', gap: '0.45rem', alignItems: 'center', marginTop: '0.2rem' }}>
            <TrustTierBadge tier={trustTierForSignal('trace_detail')} />
            <span style={{ color: 'var(--foreground)', fontWeight: 600 }}>Execution references</span>
          </div>
          <div>Submit request: {detail.submit_execution_request_id ?? honestMissingCopy('trace_detail')}</div>
          <div>Submit receipt: {detail.submit_execution_receipt_id ?? honestMissingCopy('trace_detail')}</div>
          <div>Complete request: {detail.complete_execution_request_id ?? honestMissingCopy('trace_detail')}</div>
          <div>Complete receipt: {detail.complete_execution_receipt_id ?? honestMissingCopy('trace_detail')}</div>
          <div>{semanticNote('trace_detail')}</div>

          <div style={{ display: 'flex', gap: '0.45rem', alignItems: 'center', marginTop: '0.2rem' }}>
            <TrustTierBadge tier={trustTierForSignal('outcome_signal')} />
            <span style={{ color: 'var(--foreground)', fontWeight: 600 }}>Latest outcome signal</span>
          </div>
          <div>Status: {detail.latest_outcome_status ?? honestMissingCopy('outcome_signal')}</div>
          <div>Reason: {detail.latest_outcome_reason ?? honestMissingCopy('outcome_signal')}</div>
          <div>{semanticNote('outcome_signal')}</div>

          <div style={{ display: 'flex', gap: '0.45rem', alignItems: 'center', marginTop: '0.2rem' }}>
            <TrustTierBadge tier={trustTierForSignal('knowledge_hint')} />
            <span style={{ color: 'var(--foreground)', fontWeight: 600 }}>Feedback packet signal</span>
          </div>
          <div>Packet id: {detail.knowledge_feedback_packet_id ?? honestMissingCopy('knowledge_hint')}</div>
          <div>Governance hints: {detail.governance_hint_count}</div>
          <div>Intelligence hints: {detail.intelligence_hint_count}</div>
          <div>{semanticNote('knowledge_hint')}</div>
        </div>
      ) : null}
    </div>
  );
}
