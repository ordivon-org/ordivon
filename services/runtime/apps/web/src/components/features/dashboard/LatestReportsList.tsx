'use client';

import Link from 'next/link';
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
        const data = await apiGet<ReportListResponse>('/api/v1/reports/latest?limit=5');
        const records = data.reports;
        setReports(records);
        setState(records.length > 0 ? 'ready' : 'empty');
      } catch (e) {
        console.error('Failed to fetch reports:', e);
        setReports([]);
        setState('error');
      }
    };

    void fetchReports();
  }, []);

  return (
    <div className="reports-list glass" style={{ padding: '1.25rem', borderRadius: '12px', height: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: '0.75rem', marginBottom: '1rem', alignItems: 'center' }}>
        <h3 style={{ fontSize: '1rem' }}>Latest Reports</h3>
        <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
          <ObjectTypeBadge label="Report" />
          <TrustTierBadge tier="artifact" />
        </div>
      </div>
      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
        Reports are system artifacts derived from upstream analysis. They are not the source of truth for execution state.
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
        {state === 'loading' && <LoadingState message="Loading latest report artifacts..." />}
        {state === 'empty' && <EmptyState message="No report artifacts are currently available from /api/v1/reports/latest." />}
        {state === 'error' && (
          <ErrorState
            message="Report artifacts could not be loaded from /api/v1/reports/latest."
            detail="The dashboard cannot confirm whether no reports exist or whether the API request failed."
          />
        )}
        {reports.map((report) => (
          <Link key={report.report_id} href="/reports" style={{ textDecoration: 'none', color: 'inherit' }}>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '1rem',
                padding: '10px',
                background: 'rgba(255,255,255,0.02)',
                borderRadius: '8px',
                border: '1px solid transparent',
                cursor: 'pointer',
                transition: 'border 0.2s',
              }}
            >
              <div style={{ fontSize: '1.5rem' }}>Report</div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontWeight: '600', fontSize: '0.85rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {report.title}
                </div>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                  {formatReportMeta(report)}
                </div>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                  <TimeSemantic label="Generated" timestamp={report.created_at} staleAfterMinutes={240} />
                </div>
              </div>
              <div className={`badge badge-${report.status === 'generated' ? 'allow' : 'warn'}`} style={{ fontSize: '0.6rem' }}>
                {report.status}
              </div>
            </div>
          </Link>
        ))}
      </div>

      <Link
        href="/reports"
        style={{
          marginTop: '1.5rem',
          width: '100%',
          display: 'block',
          padding: '8px',
          background: 'transparent',
          border: '1px solid var(--border-color)',
          borderRadius: '6px',
          color: 'var(--text-muted)',
          fontSize: '0.75rem',
          cursor: 'pointer',
          textDecoration: 'none',
          textAlign: 'center',
        }}
      >
        View Research Archive
      </Link>
    </div>
  );
}
