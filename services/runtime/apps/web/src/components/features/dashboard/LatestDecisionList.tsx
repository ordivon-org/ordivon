'use client';

export default function LatestDecisionList() {
  const decisions = [
    { id: 1, symbol: 'BTC/USDT', query: 'Breakout?', decision: 'allow', action: 'accumulate', confidence: 0.85, time: '12m ago' },
    { id: 2, symbol: 'ETH/USDT', query: 'Sell off risk?', decision: 'warn', action: 'reduce', confidence: 0.65, time: '1h ago' },
    { id: 3, symbol: 'SOL/USDT', query: 'Buy dip?', decision: 'block', action: 'observe', confidence: 0.45, time: '3h ago' },
  ];

  return (
    <div className="decision-list glass" style={{
      padding: '1.25rem',
      borderRadius: '12px',
      height: '100%'
    }}>
      <h3 style={{ marginBottom: '1.25rem', fontSize: '1rem' }}>🧠 Latest Decisions</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {decisions.map(d => (
          <div key={d.id} style={{
            paddingBottom: '1rem',
            borderBottom: '1px solid var(--border-color)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start'
          }}>
            <div>
              <div style={{ fontWeight: '600', marginBottom: '4px' }}>
                {d.symbol} <span style={{ fontWeight: '400', fontSize: '0.8rem', color: 'var(--text-muted)' }}>({d.query})</span>
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                Action: <span style={{ color: 'var(--primary-hover)', fontWeight: '600' }}>{d.action}</span>
                <span style={{ margin: '0 8px' }}>|</span>
                Confidence: <span style={{ color: 'var(--foreground)' }}>{Math.round(d.confidence * 100)}%</span>
              </div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <span className={`badge badge-${d.decision}`}>
                {d.decision}
              </span>
              <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', marginTop: '4px' }}>{d.time}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
