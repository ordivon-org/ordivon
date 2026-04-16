'use client';

export default function PendingReviews() {
  const pendingItems = [
    { id: 'reco_3', symbol: 'SOL/USDT', action: 'exit', closedAt: 'Yesterday', reason: 'TP Hit' },
  ];

  const handleTriggerReview = (id: string) => {
    console.log('Triggering review for:', id);
    // TODO: 调用 POST /api/v1/reviews/generate-skeleton
    // 并导航至复盘编辑页面
    window.location.href = `/audits?triggerReview=${id}`;
  };

  return (
    <div className="pending-reviews glass" style={{ padding: '1.25rem', borderRadius: '12px', height: '100%', border: '1px solid var(--warn)' }}>
      <h3 style={{ marginBottom: '1.25rem', fontSize: '1rem' }}>✍️ Pending Performance Reviews</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
        {pendingItems.length === 0 && <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>All reviews completed. Excellence maintained.</div>}
        {pendingItems.map(item => (
          <div key={item.id} style={{
            padding: '12px',
            background: 'rgba(210, 153, 34, 0.05)',
            border: '1px solid rgba(210, 153, 34, 0.2)',
            borderRadius: '8px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <div>
              <div style={{ fontWeight: 'bold', fontSize: '0.9rem' }}>{item.symbol}</div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                Closed {item.closedAt} · Action: {item.action}
              </div>
            </div>
            <button 
              onClick={() => handleTriggerReview(item.id)}
              style={{
                padding: '6px 12px',
                background: 'var(--warn)',
                color: 'black',
                fontWeight: 'bold',
                border: 'none',
                borderRadius: '4px',
                fontSize: '0.7rem',
                cursor: 'pointer'
              }}
            >
              Start Review
            </button>
          </div>
        ))}
      </div>
      <div style={{ marginTop: '1.5rem', fontSize: '0.7rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
        Post-mortem reviews are essential for system-user calibration and rule evolution.
      </div>
    </div>
  );
}
