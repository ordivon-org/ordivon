'use client';

import type { AnalyzeWorkspaceResult } from '@/components/features/analyze/types';

interface GovernancePanelProps {
  data: AnalyzeWorkspaceResult | null;
  isLoading: boolean;
}

export default function GovernancePanel({ data, isLoading }: GovernancePanelProps) {
  if (isLoading) {
    return (
      <div className="governance-panel glass" style={{ padding: '1.5rem', height: '100%', opacity: 0.5 }}>
        <h2 id="analyze-governance-panel" style={{ marginBottom: '1.5rem', fontSize: '0.9rem', color: 'var(--text-muted)' }}>
          Gating Status
        </h2>
        <div style={{ padding: '1rem', border: '1px dashed var(--border-color)', borderRadius: '8px', textAlign: 'center' }}>
          Validating policy...
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="governance-panel glass" style={{ padding: '1.5rem', height: '100%', border: '1px dashed var(--border-color)', borderRadius: '12px' }}>
        <h2 id="analyze-governance-panel" style={{ marginBottom: '1.5rem', fontSize: '0.9rem', color: 'var(--text-muted)' }}>
          Gating Status
        </h2>
        <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>No governance result available.</div>
      </div>
    );
  }

  const decision = data.decision;
  const riskFlags = data.risk_flags ?? [];
  const auditEventId = data.audit_event_id ?? null;
  const reportPath = data.report_path ?? null;
  const workflow = data.workflow ?? 'unavailable';
  const governanceSource =
    typeof data.metadata?.governance_source === 'string' ? data.metadata.governance_source : 'unavailable';

  const badgeKey = decision === 'execute' ? 'allow' : decision === 'reject' ? 'block' : 'warn';

  return (
    <div
      className="governance-panel glass"
      style={{
        padding: '1.5rem',
        borderRadius: '12px',
        height: '100%',
        backgroundColor: decision === 'reject' ? 'rgba(248, 81, 73, 0.03)' : 'transparent',
      }}
    >
      <h2 id="analyze-governance-panel" style={{ marginBottom: '1.5rem', fontSize: '0.9rem', color: 'var(--text-muted)' }}>
        Gating Result
      </h2>

      <div
        style={{
          textAlign: 'center',
          padding: '1.5rem',
          borderRadius: '8px',
          background:
            decision === 'reject'
              ? 'rgba(248, 81, 73, 0.1)'
              : decision === 'execute'
                ? 'rgba(35, 134, 54, 0.1)'
                : 'rgba(210, 153, 34, 0.1)',
          border:
            decision === 'reject'
              ? '1px solid rgba(248, 81, 73, 0.2)'
              : decision === 'execute'
                ? '1px solid rgba(35, 134, 54, 0.2)'
                : '1px solid rgba(210, 153, 34, 0.2)',
          marginBottom: '2rem',
        }}
      >
        <div
          className={`badge badge-${badgeKey}`}
          style={{ fontSize: '0.95rem', padding: '0.45rem 0.7rem', display: 'inline-block' }}
        >
          {decision ?? 'unavailable'}
        </div>
        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '10px' }}>
          Decision source: {governanceSource}
        </div>
      </div>

      <section style={{ marginBottom: '2rem' }}>
        <h4 style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>RISK FLAGS</h4>
        {riskFlags.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {riskFlags.map((flag, index) => (
              <div
                key={index}
                style={{
                  padding: '8px 12px',
                  background: 'rgba(255,255,255,0.04)',
                  borderLeft: '3px solid var(--border-color)',
                  borderRadius: '4px',
                  fontSize: '0.75rem',
                  color: 'var(--foreground)',
                }}
              >
                {flag}
              </div>
            ))}
          </div>
        ) : (
          <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>Risk flags unavailable.</div>
        )}
      </section>

      <section
        style={{
          marginTop: 'auto',
          paddingTop: '1.5rem',
          borderTop: '1px solid var(--border-color)',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.75rem',
          fontSize: '0.75rem',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span style={{ color: 'var(--text-muted)' }}>Audit UUID:</span>
          <code style={{ fontSize: '0.7rem', color: 'var(--primary-hover)' }}>
            {auditEventId ? `${auditEventId.slice(0, 8)}...` : 'unavailable'}
          </code>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span style={{ color: 'var(--text-muted)' }}>Workflow:</span>
          <span>{workflow}</span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span style={{ color: 'var(--text-muted)' }}>Archive:</span>
          <span style={{ color: reportPath ? 'var(--success)' : 'var(--text-muted)' }}>
            {reportPath ?? 'unavailable'}
          </span>
        </div>
      </section>
    </div>
  );
}
