'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';

import { apiGet } from '@/lib/api';
import { honestMissingCopy, semanticNote, trustTierForSignal } from '@/lib/semanticSignals';
import { EmptyState, LoadingState, UnavailableState } from '@/components/state/SurfaceStates';
import { ObjectTypeBadge, TimeSemantic, TrustTierBadge } from '@/components/state/ProductSignals';
import type { PendingReviewItem, PendingReviewListResponse } from '@/types/api';

interface PendingReviewState {
  status: 'loading' | 'ready' | 'empty' | 'unavailable';
  reviews: PendingReviewItem[];
}

export default function PendingReviews() {
  const [state, setState] = useState<PendingReviewState>({
    status: 'loading',
    reviews: [],
  });

  const loadPendingReviews = async () => {
    try {
      const response = await apiGet<PendingReviewListResponse>('/api/v1/reviews/pending?limit=5');
      const reviews = response.reviews ?? [];
      setState({
        reviews,
        status: reviews.length > 0 ? 'ready' : 'empty',
      });
    } catch (error) {
      console.error('Failed to load pending reviews:', error);
      setState({
        reviews: [],
        status: 'unavailable',
      });
    }
  };

  useEffect(() => {
    const initialLoad = window.setTimeout(() => {
      void loadPendingReviews();
    }, 0);

    return () => {
      window.clearTimeout(initialLoad);
    };
  }, []);

  return (
    <div
      className="pending-reviews glass"
      style={{
        padding: '1.25rem',
        borderRadius: '12px',
        height: '100%',
        border: '1px solid var(--warn)',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: '0.75rem', marginBottom: '1rem', alignItems: 'center' }}>
        <h3 style={{ fontSize: '1rem' }}>Pending Performance Reviews</h3>
        <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
          <ObjectTypeBadge label="Review" />
          <TrustTierBadge tier="fact" />
        </div>
      </div>
      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
        Command-center preview of supervision-needed review objects. Deep review work stays in the review workbench.
      </div>

      {state.status === 'loading' && (
        <LoadingState message="Loading pending review records..." />
      )}

      {state.status === 'empty' && (
        <EmptyState message="No pending review records are currently exposed by /api/v1/reviews/pending." />
      )}

      {state.status === 'unavailable' && (
        <UnavailableState message="Pending review records are currently unavailable because the review API could not be reached." />
      )}

      {state.status === 'ready' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
          {state.reviews.map((review) => (
            <div
              key={review.id}
              style={{
                padding: '12px',
                background: 'rgba(210, 153, 34, 0.05)',
                border: '1px solid rgba(210, 153, 34, 0.2)',
                borderRadius: '8px',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.4rem',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: '1rem', alignItems: 'center' }}>
                <div style={{ fontWeight: 'bold', fontSize: '0.9rem' }}>{review.review_type}</div>
                <span className={`badge badge-${review.status === 'pending' ? 'warn' : 'allow'}`}>{review.status}</span>
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                Recommendation: <span style={{ color: 'var(--foreground)' }}>{review.recommendation_id ?? 'not linked'}</span>
              </div>
              {review.expected_outcome && (
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  Expected outcome: <span style={{ color: 'var(--foreground)' }}>{review.expected_outcome}</span>
                </div>
              )}
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'flex', flexDirection: 'column', gap: '0.3rem', marginTop: '0.2rem' }}>
                <div style={{ color: 'var(--foreground)', fontWeight: 600, marginBottom: '0.05rem' }}>Trace references</div>
                <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center' }}>
                  <TrustTierBadge tier={trustTierForSignal('trace_detail')} />
                  <span>Relation detail</span>
                </div>
                <div>Workflow run: {review.workflow_run_id ?? honestMissingCopy('trace_detail')}</div>
                <div>Intelligence run: {review.intelligence_run_id ?? honestMissingCopy('trace_detail')}</div>
                <div>Recommendation receipt: {review.recommendation_generate_receipt_id ?? honestMissingCopy('trace_detail')}</div>
                <div>{semanticNote('trace_detail')}</div>
              </div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'flex', flexDirection: 'column', gap: '0.3rem', marginTop: '0.2rem' }}>
                <div style={{ color: 'var(--foreground)', fontWeight: 600, marginBottom: '0.05rem' }}>Outcome signal</div>
                <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center' }}>
                  <TrustTierBadge tier={trustTierForSignal('outcome_signal')} />
                  <span>Outcome signal</span>
                </div>
                <div>Status: {review.latest_outcome_status ?? honestMissingCopy('outcome_signal')}</div>
                <div>Reason: {review.latest_outcome_reason ?? honestMissingCopy('outcome_signal')}</div>
                <div>{semanticNote('outcome_signal')}</div>
              </div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'flex', flexDirection: 'column', gap: '0.3rem', marginTop: '0.2rem' }}>
                <div style={{ color: 'var(--foreground)', fontWeight: 600, marginBottom: '0.05rem' }}>Knowledge hints prepared</div>
                <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center' }}>
                  <TrustTierBadge tier={trustTierForSignal('knowledge_hint')} />
                  <span>Derived hint</span>
                </div>
                <div>Count: {review.knowledge_hint_count}</div>
                <div>{review.knowledge_hint_count > 0 ? 'Derived hints are linked for this review path.' : honestMissingCopy('knowledge_hint')}</div>
                <div>{semanticNote('knowledge_hint')}</div>
              </div>
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                <Link href={`/reviews?review_id=${review.id}&trace_ref=${review.id}`} style={{ color: 'var(--primary-hover)' }}>
                  Continue in review workbench
                </Link>
                {review.recommendation_id ? (
                  <Link href={`/reviews?review_id=${review.id}&recommendation_id=${review.recommendation_id}`} style={{ color: 'var(--primary-hover)' }}>
                    Open linked recommendation in reviews
                  </Link>
                ) : null}
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                <TimeSemantic label="Created" timestamp={review.created_at} staleAfterMinutes={240} />
              </div>
            </div>
          ))}
        </div>
      )}

      <div style={{ marginTop: '1.5rem', fontSize: '0.7rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
        This card is a command-center preview. Actual review supervision happens in the dedicated review workbench.
      </div>
    </div>
  );
}
