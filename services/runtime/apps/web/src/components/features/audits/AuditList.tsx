'use client';

import { useEffect, useState } from 'react';

import { apiGet } from '@/lib/api';
import { useWorkspaceContext } from '@/components/workspace/WorkspaceProvider';
import type { AuditEvent, AuditListResponse } from '@/types/api';

function formatTimestamp(value: string): string {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return parsed.toLocaleString();
}

function summarizeSubject(event: AuditEvent): string {
  if (event.subject_id) {
    return event.subject_id;
  }
  return event.context_summary || 'No subject recorded';
}

function summarizeDetails(details: Record<string, unknown>): string | null {
  const entries = Object.entries(details);
  if (entries.length === 0) {
    return null;
  }

  return entries
    .slice(0, 3)
    .map(([key, value]) => `${key}: ${String(value)}`)
    .join(' | ');
}

export default function AuditList() {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [audits, setAudits] = useState<AuditEvent[]>([]);
  const [status, setStatus] = useState<'loading' | 'ready' | 'empty' | 'unavailable'>('loading');
  const workspace = useWorkspaceContext();

  function openAuditTabs(audit: AuditEvent) {
    const recommendationId =
      typeof audit.details.recommendation_id === 'string'
        ? audit.details.recommendation_id
        : audit.stage === 'recommendation'
          ? audit.subject_id
          : null;
    const reviewId =
      typeof audit.details.review_id === 'string'
        ? audit.details.review_id
        : audit.stage === 'review'
          ? audit.subject_id
          : null;
    const traceRef = reviewId ?? recommendationId ?? audit.subject_id;

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
  }

  const loadAudits = async () => {
    try {
      const response = await apiGet<AuditListResponse>('/api/v1/audits/recent?limit=20');
      const records = response.audits ?? [];
      setAudits(records);
      setStatus(records.length > 0 ? 'ready' : 'empty');
    } catch (error) {
      console.error('Failed to fetch audit events:', error);
      setAudits([]);
      setStatus('unavailable');
    }
  };

  useEffect(() => {
    const initialLoad = window.setTimeout(() => {
      void loadAudits();
    }, 0);

    return () => {
      window.clearTimeout(initialLoad);
    };
  }, []);

  if (status === 'loading') {
    return <div style={{ padding: '1.5rem', color: 'var(--text-muted)' }}>Loading audit events...</div>;
  }

  if (status === 'empty') {
    return (
      <div style={{ padding: '1.5rem', color: 'var(--text-muted)' }}>
        No audit events are currently available from `/api/v1/audits/recent`.
      </div>
    );
  }

  if (status === 'unavailable') {
    return (
      <div style={{ padding: '1.5rem', color: 'var(--text-muted)' }}>
        Audit events are currently unavailable because the audit API could not be reached.
      </div>
    );
  }

  return (
    <div className="audit-list">
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '110px 1fr 150px 170px 80px',
          padding: '1rem',
          borderBottom: '2px solid var(--border-color)',
          fontSize: '0.75rem',
          color: 'var(--text-muted)',
          fontWeight: 'bold',
        }}
      >
        <div>DECISION</div>
        <div>SUBJECT / SUMMARY</div>
        <div>WORKFLOW</div>
        <div>TIME</div>
        <div>ACTION</div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column' }}>
        {audits.map((audit) => {
          const detailsSummary = summarizeDetails(audit.details);
          const badgeKey = audit.decision.toLowerCase() === 'pass' ? 'allow' : audit.decision.toLowerCase();

          return (
            <div key={audit.event_id} style={{ borderBottom: '1px solid var(--border-color)' }}>
              <div
                onClick={() => setExpandedId(expandedId === audit.event_id ? null : audit.event_id)}
                style={{
                  display: 'grid',
                  gridTemplateColumns: '110px 1fr 150px 170px 80px',
                  padding: '1.25rem 1rem',
                  alignItems: 'center',
                  cursor: 'pointer',
                  background: expandedId === audit.event_id ? 'rgba(255,255,255,0.02)' : 'transparent',
                }}
              >
                <div className={`badge badge-${badgeKey}`}>{audit.decision}</div>
                <div style={{ fontSize: '0.9rem' }}>
                  <strong>{summarizeSubject(audit)}</strong>
                  <span style={{ marginLeft: '1rem', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                    {audit.context_summary}
                  </span>
                </div>
                <div style={{ fontSize: '0.75rem', opacity: 0.7 }}>{audit.workflow_name}</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{formatTimestamp(audit.created_at)}</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--primary-hover)' }}>
                  {expandedId === audit.event_id ? 'Hide' : 'View'}
                </div>
              </div>

              {expandedId === audit.event_id && (
                <div
                  style={{
                    padding: '1rem 2rem 2rem 6rem',
                    background: 'rgba(0,0,0,0.2)',
                    borderLeft: '4px solid var(--primary)',
                  }}
                >
                  <h4 style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
                    EVENT DETAILS
                  </h4>

                  <p style={{ fontSize: '0.85rem', lineHeight: '1.5', color: 'var(--foreground)', marginBottom: '0.75rem' }}>
                    <strong>Stage:</strong> {audit.stage}
                  </p>
                  <p style={{ fontSize: '0.85rem', lineHeight: '1.5', color: 'var(--foreground)', marginBottom: '0.75rem' }}>
                    <strong>Status:</strong> {audit.status}
                  </p>
                  <p style={{ fontSize: '0.85rem', lineHeight: '1.5', color: 'var(--foreground)', marginBottom: '0.75rem' }}>
                    <strong>Context Summary:</strong> {audit.context_summary}
                  </p>

                  {detailsSummary && (
                    <p style={{ fontSize: '0.85rem', lineHeight: '1.5', color: 'var(--foreground)', marginBottom: '0.75rem' }}>
                      <strong>Details:</strong> {detailsSummary}
                    </p>
                  )}

                  <div style={{ display: 'flex', gap: '0.6rem', flexWrap: 'wrap', marginBottom: '0.75rem' }}>
                    <button
                      type="button"
                      onClick={() => openAuditTabs(audit)}
                      style={{
                        padding: '0.5rem 0.75rem',
                        borderRadius: '6px',
                        border: '1px solid var(--border-color)',
                        background: 'rgba(255,255,255,0.04)',
                        color: 'var(--foreground)',
                        cursor: 'pointer',
                      }}
                    >
                      Open Related Tabs
                    </button>
                  </div>

                  {audit.report_path && (
                    <p style={{ fontSize: '0.85rem', lineHeight: '1.5', color: 'var(--foreground)' }}>
                      <strong>Report Path:</strong> {audit.report_path}
                    </p>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
