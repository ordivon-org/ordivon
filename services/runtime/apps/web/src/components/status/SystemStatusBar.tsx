'use client';

import { useEffect, useState } from 'react';

export default function SystemStatusBar() {
  const [status, setStatus] = useState({
    api: 'connecting...',
    reasoning: 'hermes_cli',
    gate: 'PASS',
    lastAudit: '2m ago',
    lastReport: '15m ago'
  });

  // TODO: 实际对接 /health 与 /evals/latest
  useEffect(() => {
    // 模拟检测
    const timer = setTimeout(() => {
      setStatus(prev => ({ ...prev, api: 'online' }));
    }, 1000);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="status-bar glass" style={{
      display: 'flex',
      alignItems: 'center',
      gap: '2rem',
      padding: '0.75rem 1.5rem',
      borderRadius: '8px',
      fontSize: '0.85rem',
      marginBottom: '1.5rem',
      width: '100%'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: status.api === 'online' ? 'var(--success)' : 'var(--warn)' }}></span>
        <span style={{ color: 'var(--text-muted)' }}>API:</span>
        <span style={{ fontWeight: '600' }}>{status.api}</span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <span style={{ color: 'var(--text-muted)' }}>Reasoning:</span>
        <span style={{ fontWeight: '600', color: 'var(--primary-hover)' }}>{status.reasoning}</span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <span style={{ color: 'var(--text-muted)' }}>Gate:</span>
        <span className={`badge badge-${status.gate.toLowerCase()}`}>{status.gate}</span>
      </div>

      <div style={{ marginLeft: 'auto', display: 'flex', gap: '1.5rem', color: 'var(--text-muted)', fontSize: '0.75rem' }}>
        <span>Last Audit: <strong>{status.lastAudit}</strong></span>
        <span>Last Report: <strong>{status.lastReport}</strong></span>
      </div>
    </div>
  );
}
