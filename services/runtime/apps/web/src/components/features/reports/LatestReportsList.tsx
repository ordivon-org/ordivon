'use client';

import { useEffect, useState } from 'react';

import { apiGet } from '@/lib/api';
import { EmptyState, ErrorState, LoadingState } from '@/components/state/SurfaceStates';
import { ObjectTypeBadge, TimeSemantic, TrustTierBadge } from '@/components/state/ProductSignals';
import type { ReportItem, ReportListResponse } from '@/types/api';
import type { ExperienceState } from '@/types/experience';

function formatReportMeta(report: ReportItem): string {
  const symbol = report.symbol ?? 'symbol unavailable';
  return `${symbol} | ${new Date(report.created_at).toLocaleString()}`;
}

export default function LatestReportsList() {
  const [reports, setReports] = useState<ReportItem[]>([]);
  const [state, setState] = useState<ExperienceState>('loading');

  useEffect(() => {
    const fetchReports = async () => {
      try {
        const data = await apiGet<ReportListResponse>('/api/v1/reports/latest?limit=20');
        const records = data.reports;
        setReports(records);
        setState(records.length > 0 ? 'ready' : 'empty');
      } catch (e) {
        console.error('Failed to fetch reports archive:', e);
        setReports([]);
        setState('error');
      }
    };

    void fetchReports();
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
        <ObjectTypeBadge label="Report" />
        <TrustTierBadge tier="artifact" />
      </div>

      {state === 'loading' && <LoadingState message="Loading report archive..." />}
      {state === 'empty' && <EmptyState message="No report artifacts are currently available from /api/v1/reports/latest." />}
      {state === 'error' && (
        <ErrorState
          message="The report archive could not be loaded from /api/v1/reports/latest."
          detail="This page cannot currently distinguish between no results and an API failure."
        />
      )}

      {reports.map((report) => {
        const content = (
          <>
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: '1rem', marginBottom: '0.5rem' }}>
              <strong>{report.title}</strong>
              <span className={`badge badge-${report.status === 'generated' ? 'allow' : 'warn'}`}>{report.status}</span>
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.35rem' }}>
              {formatReportMeta(report)}
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.35rem' }}>
              <TimeSemantic label="Generated" timestamp={report.created_at} staleAfterMinutes={240} />
            </div>
            {report.metadata?.query ? (
              <div style={{ fontSize: '0.8rem', color: 'var(--foreground)' }}>
                Query: {report.metadata.query}
              </div>
            ) : null}
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
              {report.report_path ?? 'Report document not generated yet.'}
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.5rem', display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
              <a href={`/audits?report_id=${report.report_id}`} style={{ color: 'var(--primary-hover)' }}>
                Trace in audits
              </a>
              <span>Lineage: report {report.report_id}</span>
            </div>
          </>
        );

        if (!report.report_path) {
          return (
            <div
              key={report.report_id}
              style={{
                display: 'block',
                padding: '1rem',
                border: '1px solid var(--border-color)',
                borderRadius: '10px',
                color: 'inherit',
                background: 'rgba(255,255,255,0.02)',
              }}
            >
              {content}
            </div>
          );
        }

        return (
          <a
            key={report.report_id}
            href={report.report_path}
            target="_blank"
            rel="noreferrer"
            style={{
              display: 'block',
              padding: '1rem',
              border: '1px solid var(--border-color)',
              borderRadius: '10px',
              textDecoration: 'none',
              color: 'inherit',
              background: 'rgba(255,255,255,0.02)',
            }}
          >
            {content}
          </a>
        );
      })}
    </div>
  );
}
