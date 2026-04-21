'use client';

import { useEffect, useState } from 'react';

import { apiGet } from '@/lib/api';
import type { AuditListResponse } from '@/types/api';

interface AuditSummaryState {
  status: 'loading' | 'ready' | 'empty' | 'unavailable';
  totalEvents: number;
  reviewEvents: number;
  recommendationEvents: number;
  latestTimestamp: string | null;
}

function formatTimestamp(value: string | null): string {
  if (!value) {
    return 'No events';
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return parsed.toLocaleString();
}

export default function AuditSummary() {
  const [state, setState] = useState<AuditSummaryState>({
    status: 'loading',
    totalEvents: 0,
    reviewEvents: 0,
    recommendationEvents: 0,
    latestTimestamp: null,
  });

  const loadSummary = async () => {
    try {
      const response = await apiGet<AuditListResponse>('/api/v1/audits/recent?limit=20');
      const audits = response.audits ?? [];

      if (audits.length === 0) {
        setState({
          status: 'empty',
          totalEvents: 0,
          reviewEvents: 0,
          recommendationEvents: 0,
          latestTimestamp: null,
        });
        return;
      }

      setState({
        status: 'ready',
        totalEvents: audits.length,
        reviewEvents: audits.filter((event) => event.stage === 'review').length,
        recommendationEvents: audits.filter((event) => event.stage === 'recommendation').length,
        latestTimestamp: audits[0]?.created_at ?? null,
      });
    } catch (error) {
      console.error('Failed to fetch audit summary:', error);
      setState({
        status: 'unavailable',
        totalEvents: 0,
        reviewEvents: 0,
        recommendationEvents: 0,
        latestTimestamp: null,
      });
    }
  };

  useEffect(() => {
    const initialLoad = window.setTimeout(() => {
      void loadSummary();
    }, 0);

    return () => {
      window.clearTimeout(initialLoad);
    };
  }, []);

  if (state.status === 'loading') {
    return (
      <div
        className="audit-summary glass"
        style={{ padding: '2rem', borderRadius: '12px', marginBottom: '2rem', color: 'var(--text-muted)' }}
      >
        Loading audit summary...
      </div>
    );
  }

  if (state.status === 'empty') {
    return (
      <div
        className="audit-summary glass"
        style={{ padding: '2rem', borderRadius: '12px', marginBottom: '2rem', color: 'var(--text-muted)' }}
      >
        No audit events are currently available from `/api/v1/audits/recent`.
      </div>
    );
  }

  if (state.status === 'unavailable') {
    return (
      <div
        className="audit-summary glass"
        style={{ padding: '2rem', borderRadius: '12px', marginBottom: '2rem', color: 'var(--text-muted)' }}
      >
        Audit summary is currently unavailable because the audit API could not be reached.
      </div>
    );
  }

  return (
    <div
      className="audit-summary glass"
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(4, 1fr)',
        gap: '1.5rem',
        padding: '2rem',
        borderRadius: '12px',
        marginBottom: '2rem',
      }}
    >
      <div style={{ textAlign: 'center' }}>
        <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: 'var(--foreground)' }}>{state.totalEvents}</div>
        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', letterSpacing: '1px' }}>RECENT EVENTS</div>
      </div>
      <div style={{ textAlign: 'center' }}>
        <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: 'var(--warn)' }}>{state.reviewEvents}</div>
        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', letterSpacing: '1px' }}>REVIEW STAGE</div>
      </div>
      <div style={{ textAlign: 'center' }}>
        <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: 'var(--primary-hover)' }}>{state.recommendationEvents}</div>
        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', letterSpacing: '1px' }}>RECOMMENDATION STAGE</div>
      </div>
      <div style={{ textAlign: 'center', backgroundColor: 'rgba(255,255,255,0.03)', borderRadius: '8px', padding: '10px' }}>
        <div style={{ fontSize: '0.95rem', fontWeight: 'bold', color: 'var(--foreground)' }}>{formatTimestamp(state.latestTimestamp)}</div>
        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', letterSpacing: '1px' }}>LATEST EVENT</div>
      </div>
    </div>
  );
}
