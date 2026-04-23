'use client';

import { useEffect, useState } from 'react';

import { apiGet } from '@/lib/api';
import type { AuditListResponse, EvalRunResponse, HealthResponse, ReportListResponse } from '@/types/api';

interface StatusViewModel {
  api: string;
  reasoning: string;
  gate: string;
  lastAudit: string;
  lastReport: string;
  lastWorkflow: string;
  monitoring: string;
  failures: string;
  summary: string;
}

function formatTimestamp(value: string | undefined): string {
  if (!value) {
    return 'unavailable';
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return 'unavailable';
  }

  return date.toLocaleString();
}

export default function SystemStatusBar() {
  const [status, setStatus] = useState<StatusViewModel>({
    api: 'checking',
    reasoning: 'unavailable',
    gate: 'unknown',
    lastAudit: 'unavailable',
    lastReport: 'unavailable',
    lastWorkflow: 'unavailable',
    monitoring: 'unavailable',
    failures: 'unavailable',
    summary: 'Checking live system surface...',
  });

  const loadStatus = async () => {
    try {
      const [health, evals, reports, audits] = await Promise.all([
        apiGet<HealthResponse>('/api/v1/health'),
        apiGet<EvalRunResponse>('/api/v1/evals/latest'),
        apiGet<ReportListResponse>('/api/v1/reports/latest?limit=1'),
        apiGet<AuditListResponse>('/api/v1/audits/recent?limit=1'),
      ]);

      setStatus({
        api: health.status === 'ok' ? 'online' : health.status,
        reasoning: health.runtime_model || health.reasoning_provider || evals.provider || 'unavailable',
        gate: evals.gate_decision || 'unknown',
        lastAudit: formatTimestamp(health.last_audit_at || audits.audits[0]?.created_at),
        lastReport: formatTimestamp(reports.reports[0]?.created_at),
        lastWorkflow: formatTimestamp(health.last_workflow_at || undefined),
        monitoring: health.monitoring_status || 'unavailable',
        failures:
          health.monitoring_status === 'unavailable'
            ? 'unavailable'
            : `${health.recent_failed_workflow_count ?? 0} workflow / ${health.recent_failed_execution_count ?? 0} execution`,
        summary:
          health.status === 'ok'
            ? `Live services reachable. Monitoring is ${health.monitoring_status || 'unavailable'} across the last ${health.monitoring_window_hours ?? 0}h window; treat downstream cards according to their own object and state labels.`
            : `API responded with a non-ready status${health.runtime_status ? ` and the active runtime is ${health.runtime_status}` : health.hermes_status ? ` and Hermes is ${health.hermes_status}` : ''}${health.monitoring_status === 'unavailable' ? ' and monitoring could not be confirmed' : ''}. Downstream cards may be partially unavailable.`,
      });
    } catch (error) {
      console.error('Failed to load system status:', error);
      setStatus({
        api: 'offline',
        reasoning: 'unavailable',
        gate: 'unknown',
        lastAudit: 'unavailable',
        lastReport: 'unavailable',
        lastWorkflow: 'unavailable',
        monitoring: 'unavailable',
        failures: 'unavailable',
        summary: 'Live system status could not be confirmed. Treat the dashboard as unavailable until API reachability is restored.',
      });
    }
  };

  useEffect(() => {
    const initialLoad = window.setTimeout(() => {
      void loadStatus();
    }, 0);

    return () => {
      window.clearTimeout(initialLoad);
    };
  }, []);

  const gateBadge = status.gate.toLowerCase() === 'pass' ? 'allow' : status.gate.toLowerCase();

  return (
    <div
      className="status-bar glass"
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '2rem',
        padding: '0.75rem 1.5rem',
        borderRadius: '8px',
        fontSize: '0.85rem',
        marginBottom: '1.5rem',
        width: '100%',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <span
          style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            background: status.api === 'online' ? 'var(--success)' : 'var(--warn)',
          }}
        />
        <span style={{ color: 'var(--text-muted)' }}>API:</span>
        <span style={{ fontWeight: '600' }}>{status.api}</span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <span style={{ color: 'var(--text-muted)' }}>Reasoning:</span>
        <span style={{ fontWeight: '600', color: 'var(--primary-hover)' }}>{status.reasoning}</span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <span style={{ color: 'var(--text-muted)' }}>Gate:</span>
        <span className={`badge badge-${gateBadge}`}>{status.gate}</span>
      </div>

      <div
        style={{
          marginLeft: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: '1.5rem',
          color: 'var(--text-muted)',
          fontSize: '0.75rem',
        }}
      >
        <div style={{ maxWidth: '420px', lineHeight: '1.5' }}>
          <strong style={{ color: 'var(--foreground)' }}>Homepage Status:</strong> {status.summary}
        </div>
        <div style={{ display: 'flex', gap: '1.5rem' }}>
          <span>
            Monitoring: <strong>{status.monitoring}</strong>
          </span>
          <span>
            Recent Failures: <strong>{status.failures}</strong>
          </span>
          <span>
            Last Workflow: <strong>{status.lastWorkflow}</strong>
          </span>
          <span>
            Last Audit: <strong>{status.lastAudit}</strong>
          </span>
          <span>
            Last Report: <strong>{status.lastReport}</strong>
          </span>
        </div>
      </div>
    </div>
  );
}
