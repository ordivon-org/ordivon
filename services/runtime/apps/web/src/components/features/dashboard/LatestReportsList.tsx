'use client';

export default function LatestReportsList() {
  const reports = [
    { id: 'rep_1', title: 'BTC Structural Breakout Analysis', symbol: 'BTC/USDT', type: 'analyze', time: '15m ago', decision: 'allow' },
    { id: 'rep_2', title: 'ETH Market Regime Review', symbol: 'ETH/USDT', type: 'review', time: '2h ago', decision: 'warn' },
    { id: 'rep_3', title: 'SOL Risk Mitigation Memo', symbol: 'SOL/USDT', type: 'analyze', time: '5h ago', decision: 'block' },
  ];

  return (
    <div className="reports-list glass" style={{
      padding: '1.25rem',
      borderRadius: '12px',
      height: '100%'
    }}>
      <h3 style={{ marginBottom: '1.25rem', fontSize: '1rem' }}>📄 Latest Reports</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
        {reports.map(r => (
          <div key={r.id} style={{
            display: 'flex',
            alignItems: 'center',
            gap: '1rem',
            padding: '10px',
            background: 'rgba(255,255,255,0.02)',
            borderRadius: '8px',
            border: '1px solid transparent',
            cursor: 'pointer',
            transition: 'border 0.2s'
          }}
          onMouseEnter={(e) => e.currentTarget.style.borderColor = 'var(--border-color)'}
          onMouseLeave={(e) => e.currentTarget.style.borderColor = 'transparent'}
          >
            <div style={{ fontSize: '1.5rem' }}>
              {r.type === 'analyze' ? '📝' : '🧐'}
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ 
                fontWeight: '600', 
                fontSize: '0.85rem', 
                whiteSpace: 'nowrap', 
                overflow: 'hidden', 
                textOverflow: 'ellipsis' 
              }}>
                {r.title}
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                {r.symbol} · {r.time}
              </div>
            </div>
            <div className={`badge badge-${r.decision}`} style={{ fontSize: '0.6rem' }}>
              {r.decision}
            </div>
          </div>
        ))}
      </div>
      
      <button style={{
        marginTop: '1.5rem',
        width: '100%',
        padding: '8px',
        background: 'transparent',
        border: '1px solid var(--border-color)',
        borderRadius: '6px',
        color: 'var(--text-muted)',
        fontSize: '0.75rem',
        cursor: 'pointer'
      }}>
        View Research Archive →
      </button>
    </div>
  );
}
