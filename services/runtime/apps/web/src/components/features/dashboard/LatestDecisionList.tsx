'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';

import { apiGet } from '@/lib/api';
import { EmptyState, LoadingState, UnavailableState } from '@/components/state/SurfaceStates';
import { ObjectTypeBadge, TrustTierBadge } from '@/components/state/ProductSignals';
import type { AuditEvent, AuditListResponse } from '@/types/api';
import type { ExperienceState } from '@/types/experience';

function formatTimestamp(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return 'timestamp unavailable';
  }
  return date.toLocaleString();
}

function summarizeEvent(event: AuditEvent): string {
  if (event.context_summary && event.context_summary !== event.workflow_name) {
    return event.context_summary;
  }

  if (event.subject_id) {
    return event.subject_id;
  }

  return 'No additional subject details';
}

export default function LatestDecisionList() {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [status, setStatus] = useState<ExperienceState>('loading');

  const loadEvents = async () => {
    try {
      const response = await apiGet<AuditListResponse>('/api/v1/audits/recent?limit=5');
      const records = response.audits ?? [];
      setEvents(records);
      setStatus(records.length > 0 ? 'ready' : 'empty');
    } catch (error) {
      console.error('Failed to fetch latest decision events:', error);
      setEvents([]);
      setStatus('unavailable');
    }
  };

  useEffect(() => {
    const initialLoad = window.setTimeout(() => {
      void loadEvents();
    }, 0);

    return () => {
      window.clearTimeout(initialLoad);
    };
  }, []);

  return (
    <div
      className="decision-list glass"
      style={{
        padding: '1.25rem',
        borderRadius: '12px',
        height: '100%',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: '0.75rem', marginBottom: '1rem', alignItems: 'center' }}>
        <h3 style={{ fontSize: '1rem' }}>Latest Audit Decisions</h3>
        <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
          <ObjectTypeBadge label="Audit Event" />
          <TrustTierBadge tier="fact" />
        </div>
      </div>
      <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem', marginBottom: '1rem' }}>
        This card represents recent persisted audit and governance events from <code>/api/v1/audits/recent</code>, not execution fills or trade confirmations.
      </div>

      {status === 'loading' && (
        <LoadingState message="Loading recent audit decision events..." />
      )}

      {status === 'empty' && (
        <EmptyState message="No recent audit decision events are available from /api/v1/audits/recent." />
      )}

      {status === 'unavailable' && (
        <UnavailableState message="Latest audit decision events are currently unavailable because the audit API could not be reached." />
      )}

      {status === 'ready' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {events.map((event) => (
            <div
              key={event.event_id}
              style={{
                paddingBottom: '1rem',
                borderBottom: '1px solid var(--border-color)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'flex-start',
              }}
            >
              <div>
                <div style={{ fontWeight: '600', marginBottom: '4px' }}>
                  {event.workflow_name}
                  <span style={{ fontWeight: '400', fontSize: '0.8rem', color: 'var(--text-muted)', marginLeft: '0.5rem' }}>
                    ({event.stage})
                  </span>
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '6px' }}>
                  Subject: <span style={{ color: 'var(--foreground)' }}>{summarizeEvent(event)}</span>
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  Status: <span style={{ color: 'var(--primary-hover)', fontWeight: '600' }}>{event.status}</span>
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '6px' }}>
                  Lineage: audit {event.event_id}
                </div>
                <div style={{ marginTop: '6px', fontSize: '0.75rem' }}>
                  <Link href={`/audits?event_id=${event.event_id}`} style={{ color: 'var(--primary-hover)' }}>
                    Open audit record
                  </Link>
                </div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <span className={`badge badge-${event.decision.toLowerCase() === 'pass' ? 'allow' : event.decision.toLowerCase()}`}>
                  {event.decision}
                </span>
                <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                  {formatTimestamp(event.created_at)}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
