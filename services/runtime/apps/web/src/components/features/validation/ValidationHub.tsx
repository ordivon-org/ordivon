'use client';

import { useEffect, useState } from 'react';

import { apiGet } from '@/lib/api';
import { ErrorState, LoadingState } from '@/components/state/SurfaceStates';
import { ObjectTypeBadge, TrustTierBadge } from '@/components/state/ProductSignals';
import type { ValidationSummaryResponse } from '@/types/api';
import type { ExperienceState } from '@/types/experience';

export default function ValidationHub() {
  const [summary, setSummary] = useState<ValidationSummaryResponse | null>(null);
  const [state, setState] = useState<ExperienceState>('loading');

  useEffect(() => {
    const fetchSummary = async () => {
      try {
        const data = await apiGet<ValidationSummaryResponse>('/api/v1/validation/summary');
        setSummary(data);
        setState('ready');
      } catch (e) {
        console.error('Failed to fetch validation summary:', e);
        setSummary(null);
        setState('error');
      }
    };

    void fetchSummary();
  }, []);

  if (state === 'loading') {
    return <LoadingState message="Loading validation summary..." />;
  }

  if (state === 'error' || !summary) {
    return (
      <ErrorState
        message="Validation summary is currently unavailable because /api/v1/validation/summary could not be loaded."
        detail="The product surface cannot confirm validation state until the API succeeds."
      />
    );
  }

  const keyLessons = summary.metadata?.key_lessons ?? [];

  return (
    <div className="validation-hub" style={{ padding: '1.5rem', background: 'rgba(13, 17, 23, 0.4)', border: '1px solid var(--border-color)', borderRadius: '12px', marginTop: '2rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div>
          <h2 style={{ fontSize: '1.1rem', fontWeight: 'bold', marginBottom: '0.35rem' }}>Validation & Stability Control</h2>
          <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
            <ObjectTypeBadge label="Validation Summary" />
            <TrustTierBadge tier="artifact" />
          </div>
        </div>
        <div
          style={{
            padding: '4px 12px',
            borderRadius: '20px',
            fontSize: '0.75rem',
            background: summary.system_go_no_go === 'continue' ? 'rgba(63, 185, 80, 0.1)' : 'rgba(210, 153, 34, 0.1)',
            color: summary.system_go_no_go === 'continue' ? '#3fb950' : '#d29922',
            border: `1px solid ${summary.system_go_no_go === 'continue' ? '#3fb950' : '#d29922'}`,
          }}
        >
          Verdict: {summary.system_go_no_go === 'continue' ? 'GO (Continue)' : 'NO-GO (Stabilize More)'}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', marginBottom: '1.5rem' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Days Active</div>
          <div style={{ fontSize: '1.25rem', fontWeight: 'bold' }}>{summary.days_active}/7</div>
        </div>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Real Analysis</div>
          <div style={{ fontSize: '1.25rem', fontWeight: 'bold' }}>{summary.total_analyses}</div>
        </div>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Critical Issues</div>
          <div style={{ fontSize: '1.25rem', fontWeight: 'bold', color: summary.open_critical_issues > 0 ? 'var(--error)' : 'inherit' }}>
            {summary.open_critical_issues}
          </div>
        </div>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Recommendations</div>
          <div style={{ fontSize: '1.25rem', fontWeight: 'bold' }}>{summary.total_recommendations}</div>
        </div>
      </div>

      <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '1rem' }}>
        <h3 style={{ fontSize: '0.85rem', marginBottom: '1rem', opacity: 0.8 }}>Active Stabilization Focus</h3>
        <ul style={{ listStyle: 'none', padding: 0, fontSize: '0.8rem', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {keyLessons.length > 0 ? (
            keyLessons.map((lesson, index) => (
              <li key={`${lesson}-${index}`} style={{ color: 'var(--warn)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '1.2rem' }}>•</span> {lesson}
              </li>
            ))
          ) : (
            <li style={{ color: 'var(--text-muted)' }}>No critical defects pending. System health nominal.</li>
          )}
        </ul>
        <div style={{ marginTop: '0.85rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          Validation period: {summary.period_id ?? 'unavailable'}
        </div>
      </div>
    </div>
  );
}
