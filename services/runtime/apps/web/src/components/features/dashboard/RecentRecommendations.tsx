'use client';

import { useState, useEffect } from 'react';

export default function RecentRecommendations() {
  const [recos, setRecos] = useState<any[]>([]);

  useEffect(() => {
    // 模拟数据或对接真实 API
    setRecos([
      { id: 'reco_1', symbol: 'BTC/USDT', action: 'accumulate', confidence: 0.85, status: 'generated', time: '5m ago' },
      { id: 'reco_2', symbol: 'ETH/USDT', action: 'reduce', confidence: 0.65, status: 'adopted', time: '1h ago' },
    ]);
  }, []);

  const handleUpdate = (id: string, newStatus: string) => {
    setRecos(prev => prev.map(r => r.id === id ? { ...r, status: newStatus } : r));
    // TODO: 调用 PATCH /api/v1/recommendations/{id}/status
  };

  return (
    <div className="recommendations-box glass" style={{ padding: '1.25rem', borderRadius: '12px', height: '100%' }}>
      <h3 style={{ marginBottom: '1.25rem', fontSize: '1rem' }}>💡 Live Recommendations</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {recos.length === 0 && <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>No active recommendations.</div>}
        {recos.map(r => (
          <div key={r.id} style={{ paddingBottom: '1rem', borderBottom: '1px solid var(--border-color)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ fontWeight: 'bold' }}>{r.symbol}</span>
              <span className={`badge badge-${r.status === 'generated' ? 'warn' : 'allow'}`} style={{ fontSize: '0.65rem' }}>{r.status}</span>
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '12px' }}>
              Action: <span style={{ color: 'var(--primary-hover)', fontWeight: '600' }}>{r.action}</span> ({Math.round(r.confidence * 100)}%)
            </div>
            
            {r.status === 'generated' && (
              <div style={{ display: 'flex', gap: '8px' }}>
                <button 
                  onClick={() => handleUpdate(r.id, 'adopted')}
                  style={{ flex: 1, padding: '6px', background: 'rgba(63, 185, 80, 0.1)', border: '1px solid #3fb950', borderRadius: '4px', color: '#3fb950', fontSize: '0.7rem', cursor: 'pointer' }}>
                  Adopt 
                </button>
                <button 
                  onClick={() => handleUpdate(r.id, 'ignored')}
                  style={{ flex: 1, padding: '6px', background: 'transparent', border: '1px solid var(--border-color)', borderRadius: '4px', color: 'var(--text-muted)', fontSize: '0.7rem', cursor: 'pointer' }}>
                  Ignore
                </button>
              </div>
            )}
            {r.status === 'adopted' && (
              <button 
                onClick={() => handleUpdate(r.id, 'closed')}
                style={{ width: '100%', padding: '6px', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border-color)', borderRadius: '4px', color: 'var(--foreground)', fontSize: '0.7rem', cursor: 'pointer' }}>
                Mark as Closed (Ready for Review)
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
