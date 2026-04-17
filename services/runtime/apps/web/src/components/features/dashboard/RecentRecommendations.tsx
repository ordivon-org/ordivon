'use client';

import { useState, useEffect } from 'react';

export default function RecentRecommendations() {
  const [recos, setRecos] = useState<any[]>([]);

  const fetchRecos = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/v1/recommendations/recent');
      if (res.ok) {
        const data = await res.json();
        setRecos(data.recommendations || []);
      }
    } catch (e) {
      console.error('Failed to fetch recommendations:', e);
    }
  };

  useEffect(() => {
    fetchRecos();
    const interval = setInterval(fetchRecos, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleUpdate = async (id: string, newStatus: string) => {
    try {
      const res = await fetch(`http://localhost:8000/api/v1/recommendations/${id}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            lifecycle_status: newStatus,
            adopted: newStatus === 'adopted' ? true : newStatus === 'ignored' ? false : undefined
        }),
      });
      if (res.ok) {
        fetchRecos();
      }
    } catch (e) {
      console.error('Failed to update status:', e);
    }
  };

  return (
    <div className="recommendations-box glass" style={{ padding: '1.25rem', borderRadius: '12px', height: '100%' }}>
      <h3 style={{ marginBottom: '1.25rem', fontSize: '1rem' }}>💡 Live Recommendations</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {recos.length === 0 && <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>No active recommendations.</div>}
        {recos.map(r => (
          <div key={r.recommendation_id} style={{ paddingBottom: '1rem', borderBottom: '1px solid var(--border-color)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ fontWeight: 'bold' }}>{r.symbol}</span>
              <span className={`badge badge-${r.lifecycle_status === 'generated' ? 'warn' : 'allow'}`} style={{ fontSize: '0.65rem' }}>{r.lifecycle_status}</span>
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '12px' }}>
              Action: <span style={{ color: 'var(--primary-hover)', fontWeight: '600' }}>{r.action?.toUpperCase()}</span> ({Math.round(r.confidence * 100)}%)
            </div>
            
            {r.lifecycle_status === 'generated' && (
              <div style={{ display: 'flex', gap: '8px' }}>
                <button 
                  onClick={() => handleUpdate(r.recommendation_id, 'adopted')}
                  style={{ flex: 1, padding: '6px', background: 'rgba(63, 185, 80, 0.1)', border: '1px solid #3fb950', borderRadius: '4px', color: '#3fb950', fontSize: '0.7rem', cursor: 'pointer' }}>
                  Adopt 
                </button>
                <button 
                  onClick={() => handleUpdate(r.recommendation_id, 'ignored')}
                  style={{ flex: 1, padding: '6px', background: 'transparent', border: '1px solid var(--border-color)', borderRadius: '4px', color: 'var(--text-muted)', fontSize: '0.7rem', cursor: 'pointer' }}>
                  Ignore
                </button>
              </div>
            )}
            {r.lifecycle_status === 'adopted' && (
              <button 
                onClick={() => handleUpdate(r.recommendation_id, 'tracking')}
                style={{ width: '100%', padding: '6px', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border-color)', borderRadius: '4px', color: 'var(--foreground)', fontSize: '0.7rem', cursor: 'pointer' }}>
                Mark as Tracking
              </button>
            )}
            {r.lifecycle_status === 'tracking' && (
              <button 
                onClick={() => handleUpdate(r.recommendation_id, 'due_review')}
                style={{ width: '100%', padding: '6px', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border-color)', borderRadius: '4px', color: 'var(--foreground)', fontSize: '0.7rem', cursor: 'pointer' }}>
                Conclude (Due Review)
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
