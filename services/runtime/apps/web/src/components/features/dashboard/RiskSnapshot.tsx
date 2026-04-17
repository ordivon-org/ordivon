'use client';

'use client';

import { useState, useEffect } from 'react';

export default function RiskSnapshot() {
  const [data, setData] = useState<any>(null);

  const fetchSummary = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/v1/dashboard/summary');
      if (res.ok) {
        setData(await res.json());
      }
    } catch (e) {
      console.error('Failed to fetch dashboard summary:', e);
    }
  };

  useEffect(() => {
    fetchSummary();
    const interval = setInterval(fetchSummary, 15000);
    return () => clearInterval(interval);
  }, []);

  const stats = {
    allow: data?.recommendation_stats?.adopted || 0,
    warn: data?.recommendation_stats?.generated || 0,
    block: data?.recommendation_stats?.ignored || 0,
    pendingReviews: data?.pending_review_count || 0,
    lastOutcome: data?.recent_outcomes?.[0]?.reason || 'No recent activity detected.'
  };

  return (
    <div className="risk-snapshot glass" style={{
      padding: '1.25rem',
      borderRadius: '12px',
      height: '100%',
      borderLeft: '4px solid var(--primary)'
    }}>
      <h3 style={{ marginBottom: '1rem', fontSize: '0.9rem', color: 'var(--text-muted)' }}>📊 Operational Core Loop</h3>
      
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: 'var(--success)' }}>{stats.allow}</div>
          <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>ADOPTED</div>
        </div>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: 'var(--warn)' }}>{stats.warn}</div>
          <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>PENDING</div>
        </div>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: 'var(--error)' }}>{stats.block}</div>
          <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>IGNORED</div>
        </div>
      </div>

      <div style={{ fontSize: '0.75rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        <div>
          <span style={{ color: 'var(--text-muted)' }}>Pending Reviews:</span>
          <span style={{ marginLeft: '0.5rem', color: stats.pendingReviews > 0 ? 'var(--warn)' : 'var(--text-muted)', fontWeight: 'bold' }}>
            {stats.pendingReviews}
          </span>
        </div>
        <div>
          <span style={{ color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Latest Outcome Trace:</span>
          <div style={{ 
            color: 'var(--foreground)', 
            padding: '8px', 
            background: 'rgba(255, 255, 255, 0.03)',
            border: '1px solid var(--border-color)',
            borderRadius: '6px',
            fontSize: '0.7rem',
            lineHeight: '1.4'
          }}>
            {stats.lastOutcome}
          </div>
        </div>
      </div>
    </div>
  );
}
