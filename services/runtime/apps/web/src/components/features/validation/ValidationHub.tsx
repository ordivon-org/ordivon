'use client';

import { useState, useEffect } from 'react';

export default function ValidationHub() {
  const [summary, setSummary] = useState<any>(null);

  useEffect(() => {
    // 模拟数据回显 (待对接真实统计)
    setSummary({
      days_used: 5,
      analysis_count: 12,
      recommendations_count: 6,
      reviews_count: 2,
      open_p0_count: 0,
      open_p1_count: 1,
      go_no_go: 'continue'
    });
  }, []);

  return (
    <div className="validation-hub" style={{ 
      padding: '1.5rem', 
      background: 'rgba(13, 17, 23, 0.4)', 
      border: '1px solid var(--border-color)', 
      borderRadius: '12px',
      marginTop: '2rem'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h2 style={{ fontSize: '1.1rem', fontWeight: 'bold' }}>🛡️ Validation & Stability Control</h2>
        <div style={{ 
          padding: '4px 12px', 
          borderRadius: '20px', 
          fontSize: '0.75rem', 
          background: summary?.go_no_go === 'continue' ? 'rgba(63, 185, 80, 0.1)' : 'rgba(210, 153, 34, 0.1)',
          color: summary?.go_no_go === 'continue' ? '#3fb950' : '#d29922',
          border: `1px solid ${summary?.go_no_go === 'continue' ? '#3fb950' : '#d29922'}`
        }}>
          Verdict: {summary?.go_no_go === 'continue' ? 'GO (Continue)' : 'NO-GO (Stabilize More)'}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', marginBottom: '1.5rem' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Days Active</div>
          <div style={{ fontSize: '1.25rem', fontWeight: 'bold' }}>{summary?.days_used}/7</div>
        </div>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Real Analysis</div>
          <div style={{ fontSize: '1.25rem', fontWeight: 'bold' }}>{summary?.analysis_count}</div>
        </div>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Critical P0</div>
          <div style={{ fontSize: '1.25rem', fontWeight: 'bold', color: summary?.open_p0_count > 0 ? 'var(--error)' : 'inherit' }}>
            {summary?.open_p0_count}
          </div>
        </div>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Severity P1</div>
          <div style={{ fontSize: '1.25rem', fontWeight: 'bold', color: summary?.open_p1_count > 0 ? 'var(--warn)' : 'inherit' }}>
            {summary?.open_p1_count}
          </div>
        </div>
      </div>

      <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '1rem' }}>
        <h3 style={{ fontSize: '0.85rem', marginBottom: '1rem', opacity: 0.8 }}>Active Stabilization Focus (P0/P1)</h3>
        <ul style={{ listStyle: 'none', padding: 0, fontSize: '0.8rem', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {summary?.open_p1_count > 0 ? (
            <li style={{ color: 'var(--warn)', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '1.2rem' }}>•</span> [P1] [Reasoning] Evidence duplication in some edge cases.
            </li>
          ) : (
            <li style={{ color: 'var(--text-muted)' }}>No critical defects pending. System health nominal.</li>
          )}
        </ul>
      </div>
    </div>
  );
}
