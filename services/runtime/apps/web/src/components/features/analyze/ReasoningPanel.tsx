'use client';

import type { AnalyzeWorkspaceResult } from '@/components/features/analyze/types';

interface ReasoningPanelProps {
  data: AnalyzeWorkspaceResult | null;
  isLoading: boolean;
}

export default function ReasoningPanel({ data, isLoading }: ReasoningPanelProps) {
  if (isLoading) {
    return (
      <div
        className="reasoning-panel glass"
        style={{
          padding: '2rem',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          gap: '1rem',
        }}
      >
        <div
          className="spinner"
          style={{
            width: '40px',
            height: '40px',
            border: '3px solid rgba(137, 87, 229, 0.2)',
            borderTopColor: 'var(--primary)',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
          }}
        />
        <div style={{ color: 'var(--text-muted)' }}>Running analysis...</div>
        <style dangerouslySetInnerHTML={{ __html: '@keyframes spin { to { transform: rotate(360deg); } }' }} />
      </div>
    );
  }

  if (!data) {
    return (
      <div
        className="reasoning-panel glass"
        style={{
          padding: '2rem',
          height: '100%',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          color: 'var(--text-muted)',
          border: '1px dashed var(--border-color)',
          borderRadius: '12px',
        }}
      >
        No analysis result available.
      </div>
    );
  }

  const symbol = data.metadata?.symbol;
  const summary = data.summary;
  const recommendations = data.recommendations ?? [];

  return (
    <div
      className="reasoning-panel glass"
      style={{
        padding: '2rem',
        borderRadius: '12px',
        height: '100%',
        overflowY: 'auto',
      }}
    >
      <header style={{ marginBottom: '2rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '1rem' }}>
        <h2 id="analyze-result-panel" style={{ fontSize: '1.25rem', marginBottom: '0.5rem' }}>
          Analysis Result
        </h2>
        <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
          Symbol:{' '}
          <span style={{ color: 'var(--foreground)', fontWeight: 600 }}>
            {symbol ?? 'unavailable'}
          </span>
        </div>
      </header>

      <section style={{ marginBottom: '2rem' }}>
        <h3
          style={{
            fontSize: '0.9rem',
            color: 'var(--primary-hover)',
            marginBottom: '0.75rem',
            textTransform: 'uppercase',
            letterSpacing: '1px',
          }}
        >
          Summary
        </h3>
        {summary ? (
          <p style={{ fontSize: '1.05rem', lineHeight: '1.6', fontWeight: '500' }}>{summary}</p>
        ) : (
          <div style={{ color: 'var(--text-muted)' }}>Summary unavailable.</div>
        )}
      </section>

      <section>
        <h3 style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>RECOMMENDATIONS</h3>
        {recommendations.length > 0 ? (
          <ul style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem', paddingLeft: '1.2rem' }}>
            {recommendations.map((item, index) => (
              <li key={index} style={{ lineHeight: '1.5' }}>
                {item}
              </li>
            ))}
          </ul>
        ) : (
          <div style={{ color: 'var(--text-muted)' }}>Recommendations unavailable.</div>
        )}
      </section>
    </div>
  );
}
