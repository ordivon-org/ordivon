'use client';

import { useState, useEffect } from 'react';

export default function ValidationHub() {
  const [summary, setSummary] = useState<any>(null);

  useEffect(() => {
    const fetchSummary = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/v1/validation/summary');
        if (res.ok) {
          const data = await res.json();
          setSummary(data);
        }
      } catch (e) {
        console.error('Failed to fetch validation summary:', e);
      }
    };
    
    fetchSummary();
  }, []);

  if (!summary) return null;

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
          {summary?.key_lessons && summary.key_lessons.length > 0 ? (
            summary.key_lessons.map((lesson: string, i: number) => (
              <li key={i} style={{ color: 'var(--warn)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '1.2rem' }}>•</span> {lesson}
              </li>
            ))
          ) : (
            <li style={{ color: 'var(--text-muted)' }}>No critical defects pending. System health nominal.</li>
          )}
        </ul>
      </div>
    </div>
  );
}
