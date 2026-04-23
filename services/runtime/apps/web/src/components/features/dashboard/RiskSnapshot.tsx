'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';

import { apiGet } from '@/lib/api';
import { ErrorState, LoadingState } from '@/components/state/SurfaceStates';
import { ObjectTypeBadge, TrustTierBadge } from '@/components/state/ProductSignals';
import type { DashboardSummaryResponse } from '@/types/api';
import type { ExperienceState } from '@/types/experience';

export default function RiskSnapshot() {
  const [data, setData] = useState<DashboardSummaryResponse | null>(null);
  const [state, setState] = useState<ExperienceState>('loading');

  const fetchSummary = async () => {
    try {
      const summary = await apiGet<DashboardSummaryResponse>('/api/v1/dashboard/summary');
      setData(summary);
      setState('ready');
    } catch (e) {
      console.error('Failed to fetch dashboard summary:', e);
      setData(null);
      setState('error');
    }
  };

  useEffect(() => {
    const initialLoad = window.setTimeout(() => {
      void fetchSummary();
    }, 0);
    const interval = setInterval(fetchSummary, 15000);
    return () => {
      window.clearTimeout(initialLoad);
      clearInterval(interval);
    };
  }, []);

  if (state === 'loading') {
    return <LoadingState message="Loading dashboard summary..." />;
  }

  if (state === 'error' || !data) {
    return (
      <ErrorState
        message="Dashboard summary is currently unavailable because /api/v1/dashboard/summary could not be loaded."
        detail="No recommendation summary or outcome trace can be trusted until the API request succeeds."
      />
    );
  }

  const recommendationEntries = Object.entries(data.recommendation_stats ?? {});
  const lastOutcome = data.recent_outcomes?.[0] ?? null;

  return (
    <div
      className="risk-snapshot glass"
      style={{
        padding: '1.25rem',
        borderRadius: '12px',
        height: '100%',
        borderLeft: '4px solid var(--primary)',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: '0.75rem', marginBottom: '1rem', alignItems: 'center' }}>
        <h3 style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>Dashboard Summary</h3>
        <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
          <ObjectTypeBadge label="View Aggregate" />
          <TrustTierBadge tier="artifact" />
        </div>
      </div>
      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '1rem', lineHeight: '1.5' }}>
        This widget reflects the raw dashboard summary aggregate. It does not rename backend counts into new business truths.
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
        {recommendationEntries.length > 0 ? recommendationEntries.map(([statusKey, count]) => (
          <div key={statusKey} style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: 'var(--foreground)' }}>{count}</div>
            <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>{statusKey}</div>
          </div>
        )) : (
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>No recommendation status counts were returned.</div>
        )}
      </div>

      <div style={{ fontSize: '0.75rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        <div>
          <span style={{ color: 'var(--text-muted)' }}>Pending Reviews:</span>
          <span
            style={{
              marginLeft: '0.5rem',
              color: data.pending_review_count > 0 ? 'var(--warn)' : 'var(--text-muted)',
              fontWeight: 'bold',
            }}
          >
            {data.pending_review_count}
          </span>
        </div>
        <div>
          <span style={{ color: 'var(--text-muted)' }}>Reasoning Runtime:</span>
          <span style={{ marginLeft: '0.5rem', color: 'var(--foreground)', fontWeight: 'bold' }}>
            {data.reasoning_provider ?? 'unknown'}
            {data.runtime_status ? ` (${data.runtime_status})` : data.hermes_status ? ` (${data.hermes_status})` : ''}
          </span>
        </div>
        <div>
          <span style={{ color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Latest Agent Action</span>
          <div
            style={{
              color: 'var(--foreground)',
              padding: '8px',
              background: 'rgba(255, 255, 255, 0.03)',
              border: '1px solid var(--border-color)',
              borderRadius: '6px',
              fontSize: '0.7rem',
              lineHeight: '1.4',
            }}
          >
            {data.last_agent_action ? (
              <>
                <div>{data.last_agent_action.task_type}</div>
                <div style={{ marginTop: '0.35rem', color: 'var(--text-muted)' }}>
                  {data.last_agent_action.provider ?? 'runtime'} / {data.last_agent_action.model ?? 'auto'} / {data.last_agent_action.status}
                </div>
              </>
            ) : (
              'No agent action has been recorded yet.'
            )}
          </div>
        </div>
        <div>
          <span style={{ color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Latest Outcome Trace</span>
          <div
            style={{
              color: 'var(--foreground)',
              padding: '8px',
              background: 'rgba(255, 255, 255, 0.03)',
              border: '1px solid var(--border-color)',
              borderRadius: '6px',
              fontSize: '0.7rem',
              lineHeight: '1.4',
            }}
          >
            {lastOutcome ? (
              <>
                <div>{lastOutcome.reason}</div>
                <div style={{ marginTop: '0.35rem', color: 'var(--text-muted)' }}>
                  Symbol: {lastOutcome.symbol} | State: {lastOutcome.state}
                </div>
              </>
            ) : (
              'No recent outcome trace was returned.'
            )}
          </div>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
          <Link href="/audits" style={{ color: 'var(--primary-hover)' }}>
            Trace through audits
          </Link>
          <Link href="/reports" style={{ color: 'var(--primary-hover)' }}>
            Trace through reports
          </Link>
        </div>
      </div>
    </div>
  );
}
