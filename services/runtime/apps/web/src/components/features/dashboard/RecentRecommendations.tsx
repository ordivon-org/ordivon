'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';

import { apiGet } from '@/lib/api';
import { EmptyState, ErrorState, LoadingState } from '@/components/state/SurfaceStates';
import { ObjectTypeBadge, TimeSemantic, TrustTierBadge } from '@/components/state/ProductSignals';
import { TraceDetailPanel } from '@/components/state/TraceDetailPanel';
import { honestMissingCopy, semanticNote, trustTierForSignal } from '@/lib/semanticSignals';
import { useWorkspaceContext } from '@/components/workspace/WorkspaceProvider';
import type { RecommendationItem, RecommendationListResponse } from '@/types/api';
import type { ExperienceState } from '@/types/experience';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';

export default function RecentRecommendations() {
  const workspace = useWorkspaceContext();
  const [recos, setRecos] = useState<RecommendationItem[]>([]);
  const [state, setState] = useState<ExperienceState>('loading');

  const formatConfidence = (confidence: number | null): string =>
    confidence === null ? 'confidence unavailable' : `${Math.round(confidence * 100)}% confidence`;

  const getMetadataString = (recommendation: RecommendationItem, key: string, fallback: string): string => {
    const value = recommendation.metadata?.[key];
    return typeof value === 'string' && value.length > 0 ? value : fallback;
  };

  const getKnowledgeHintCount = (recommendation: RecommendationItem): number => {
    const value = recommendation.metadata?.knowledge_hint_count;
    return typeof value === 'number' ? value : 0;
  };

  const getKnowledgeHintSummaries = (recommendation: RecommendationItem): string[] => {
    const value = recommendation.metadata?.knowledge_hint_summaries;
    if (!Array.isArray(value)) {
      return [];
    }
    return value.filter((item): item is string => typeof item === 'string' && item.length > 0);
  };

  const fetchRecos = async () => {
    try {
      const data = await apiGet<RecommendationListResponse>('/api/v1/recommendations/recent');
      const records = data.recommendations || [];
      setRecos(records);
      setState(records.length > 0 ? 'ready' : 'empty');
    } catch (e) {
      console.error('Failed to fetch recommendations:', e);
      setRecos([]);
      setState('error');
    }
  };

  useEffect(() => {
    const initialLoad = window.setTimeout(() => {
      void fetchRecos();
    }, 0);
    const interval = setInterval(fetchRecos, 10000);
    return () => {
      window.clearTimeout(initialLoad);
      clearInterval(interval);
    };
  }, []);

  const handleUpdate = async (id: string, newStatus: string) => {
    try {
      const idempotencyKey = `recommendation:${id}:${newStatus}`;
      const res = await fetch(`${API_BASE_URL}/api/v1/recommendations/${id}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          lifecycle_status: newStatus,
          adopted: newStatus === 'adopted' ? true : newStatus === 'ignored' ? false : undefined,
          action_context: {
            actor: 'web.dashboard.recommendations',
            context: 'homepage_live_recommendations',
            reason: `update recommendation lifecycle to ${newStatus}`,
            idempotency_key: idempotencyKey,
          },
        }),
      });
      if (res.ok) {
        void fetchRecos();
      }
    } catch (e) {
      console.error('Failed to update status:', e);
    }
  };

  return (
    <div className="recommendations-box glass" style={{ padding: '1.25rem', borderRadius: '12px', height: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: '0.75rem', marginBottom: '1rem', alignItems: 'center' }}>
        <h3 style={{ fontSize: '1rem' }}>Live Recommendations</h3>
        <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
          <ObjectTypeBadge label="Recommendation" />
          <TrustTierBadge tier="inference" />
        </div>
      </div>
      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
        Command-center preview of recommendation objects. Updating status does not submit or execute an external trade.
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {state === 'loading' && <LoadingState message="Loading live recommendation objects..." />}
        {state === 'empty' && <EmptyState message="No recommendation objects are currently available from /api/v1/recommendations/recent." />}
        {state === 'error' && (
          <ErrorState
            message="Recommendation data could not be loaded from /api/v1/recommendations/recent."
            detail="The dashboard cannot confirm whether there are no recommendations or whether the API request failed."
          />
        )}
        {recos.map((recommendation) => (
          <div key={recommendation.id} style={{ paddingBottom: '1rem', borderBottom: '1px solid var(--border-color)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', gap: '0.75rem', alignItems: 'center' }}>
              <span style={{ fontWeight: 'bold' }}>{recommendation.symbol ?? recommendation.analysis_id ?? 'UNKNOWN'}</span>
              <span className={`badge badge-${recommendation.status === 'generated' ? 'warn' : 'allow'}`} style={{ fontSize: '0.65rem' }}>
                {recommendation.status}
              </span>
            </div>
            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '0.6rem' }}>
              <ObjectTypeBadge label="Recommendation" />
              {recommendation.review_status ? <ObjectTypeBadge label={`Review ${recommendation.review_status}`} /> : null}
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '12px' }}>
              Summary:{' '}
              <span style={{ color: 'var(--primary-hover)', fontWeight: '600' }}>
                {recommendation.action_summary ?? 'No summary'}
              </span>{' '}
              ({formatConfidence(recommendation.confidence)})
            </div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '0.75rem', display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
              <TimeSemantic label="Generated" timestamp={recommendation.created_at} staleAfterMinutes={180} />
              <div>Lineage: analysis {recommendation.analysis_id ?? 'unavailable'} {'->'} recommendation {recommendation.id}</div>
              <div style={{ marginTop: '0.15rem' }}>
                <div style={{ color: 'var(--foreground)', fontWeight: 600, marginBottom: '0.2rem' }}>Trace references</div>
                <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center' }}>
                  <TrustTierBadge tier={trustTierForSignal('trace_detail')} />
                  <span>Relation detail</span>
                </div>
                <div>Workflow run: {getMetadataString(recommendation, 'workflow_run_id', honestMissingCopy('trace_detail'))}</div>
                <div>Intelligence run: {getMetadataString(recommendation, 'intelligence_run_id', honestMissingCopy('trace_detail'))}</div>
                <div>Recommendation receipt: {getMetadataString(recommendation, 'recommendation_generate_receipt_id', honestMissingCopy('trace_detail'))}</div>
                <div>Report receipt: {getMetadataString(recommendation, 'execution_receipt_id', honestMissingCopy('report_artifact'))}</div>
                <div>Policy set: {getMetadataString(recommendation, 'governance_policy_set_id', honestMissingCopy('trace_detail'))}</div>
                <div>{semanticNote('trace_detail')}</div>
              </div>
              <div style={{ marginTop: '0.15rem' }}>
                <div style={{ color: 'var(--foreground)', fontWeight: 600, marginBottom: '0.2rem' }}>Outcome signal</div>
                <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center' }}>
                  <TrustTierBadge tier={trustTierForSignal('outcome_signal')} />
                  <span>Outcome signal</span>
                </div>
                <div>Status: {recommendation.outcome_status ?? 'unavailable'}</div>
                <div>Reason: {getMetadataString(recommendation, 'latest_outcome_reason', 'unavailable')}</div>
                <div style={{ color: 'var(--text-muted)' }}>{semanticNote('outcome_signal')}</div>
              </div>
              <div style={{ marginTop: '0.15rem' }}>
                <div style={{ color: 'var(--foreground)', fontWeight: 600, marginBottom: '0.2rem' }}>Knowledge hints prepared</div>
                <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center' }}>
                  <TrustTierBadge tier={trustTierForSignal('knowledge_hint')} />
                  <span>Derived hint</span>
                </div>
                <div>Count: {getKnowledgeHintCount(recommendation)}</div>
                {getKnowledgeHintCount(recommendation) > 0 ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.15rem' }}>
                    {getKnowledgeHintSummaries(recommendation).map((summary, index) => (
                      <div key={`${recommendation.id}-hint-${index}`}>
                        Derived hint: <span style={{ color: 'var(--foreground)' }}>{summary}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div>{honestMissingCopy('knowledge_hint')}</div>
                )}
                <div style={{ color: 'var(--text-muted)' }}>{semanticNote('knowledge_hint')}</div>
              </div>
              <TraceDetailPanel path={`/api/v1/traces/recommendations/${recommendation.id}`} />
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                <button
                  type="button"
                  onClick={() => {
                    workspace.openTab({
                      id: `recommendation:${recommendation.id}`,
                      type: 'recommendation_detail',
                      title: `Recommendation ${recommendation.id}`,
                      refId: recommendation.id,
                    });
                  }}
                  style={{ padding: '4px 8px', borderRadius: '6px', border: '1px solid var(--border-color)', background: 'transparent', color: 'var(--foreground)', cursor: 'pointer' }}
                >
                  Open recommendation tab
                </button>
                <button
                  type="button"
                  onClick={() => {
                    workspace.openTab({
                      id: `trace:${recommendation.id}`,
                      type: 'trace_detail',
                      title: `Trace ${recommendation.id}`,
                      refId: recommendation.id,
                    });
                  }}
                  style={{ padding: '4px 8px', borderRadius: '6px', border: '1px solid var(--border-color)', background: 'transparent', color: 'var(--foreground)', cursor: 'pointer' }}
                >
                  Open trace tab
                </button>
              </div>
              <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
                {recommendation.review_status ? (
                  <Link href={`/reviews?recommendation_id=${recommendation.id}`} style={{ color: 'var(--primary-hover)' }}>
                    Continue in review workbench
                  </Link>
                ) : null}
                <Link href={`/audits?recommendation_id=${recommendation.id}`} style={{ color: 'var(--primary-hover)' }}>
                  Trace in audits
                </Link>
                <Link href={`/reports?analysis_id=${recommendation.analysis_id ?? ''}`} style={{ color: 'var(--primary-hover)' }}>
                  Trace to reports
                </Link>
              </div>
            </div>

            {recommendation.status === 'generated' && (
              <div style={{ display: 'flex', gap: '8px' }}>
                <button
                  onClick={() => handleUpdate(recommendation.id, 'adopted')}
                  style={{ flex: 1, padding: '6px', background: 'rgba(63, 185, 80, 0.1)', border: '1px solid #3fb950', borderRadius: '4px', color: '#3fb950', fontSize: '0.7rem', cursor: 'pointer' }}
                >
                  Adopt Recommendation
                </button>
                <button
                  onClick={() => handleUpdate(recommendation.id, 'ignored')}
                  style={{ flex: 1, padding: '6px', background: 'transparent', border: '1px solid var(--border-color)', borderRadius: '4px', color: 'var(--text-muted)', fontSize: '0.7rem', cursor: 'pointer' }}
                >
                  Ignore Recommendation
                </button>
              </div>
            )}
            {recommendation.status === 'adopted' && (
              <button
                onClick={() => handleUpdate(recommendation.id, 'tracking')}
                style={{ width: '100%', padding: '6px', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border-color)', borderRadius: '4px', color: 'var(--foreground)', fontSize: '0.7rem', cursor: 'pointer' }}
              >
                Mark as Tracking
              </button>
            )}
            {recommendation.status === 'tracking' && (
              <button
                onClick={() => handleUpdate(recommendation.id, 'review_pending')}
                style={{ width: '100%', padding: '6px', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border-color)', borderRadius: '4px', color: 'var(--foreground)', fontSize: '0.7rem', cursor: 'pointer' }}
              >
                Mark Review Pending
              </button>
            )}
            {(recommendation.status === 'generated' || recommendation.status === 'adopted' || recommendation.status === 'tracking') && (
              <div style={{ marginTop: '0.65rem', fontSize: '0.72rem', color: 'var(--text-muted)', lineHeight: '1.5' }}>
                Consequence: this updates the recommendation lifecycle record and may affect review queue visibility. It does not trigger exchange execution.
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
