'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function QuickAnalyze() {
  const router = useRouter();
  const [query, setQuery] = useState('');
  const [symbol, setSymbol] = useState('BTC/USDT');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query) return;

    setIsSubmitting(true);
    // 传递参数到分析页，让分析页执行请求
    const params = new URLSearchParams({
      query,
      symbol,
      autoRun: 'true'
    });
    
    // 模拟瞬间延迟，增强操作感
    setTimeout(() => {
      router.push(`/analyze?${params.toString()}`);
    }, 300);
  };

  return (
    <div className="quick-analyze glass" style={{
      padding: '1.5rem',
      borderRadius: '12px',
      marginBottom: '1.5rem'
    }}>
      <h3 style={{ marginBottom: '1rem', fontSize: '1rem', fontWeight: '600' }}>🚀 Quick Analyze</h3>
      <form onSubmit={handleAnalyze} style={{ display: 'flex', gap: '1rem', alignItems: 'flex-end' }}>
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Query / Intent</label>
          <input 
            type="text" 
            placeholder="e.g. BTC breakout validation, current sentiment..." 
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            style={{
              width: '100%',
              padding: '0.75rem',
              background: 'rgba(255,255,255,0.05)',
              border: '1px solid var(--border-color)',
              borderRadius: '6px',
              color: 'var(--foreground)',
              outline: 'none'
            }}
          />
        </div>

        <div style={{ width: '150px', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Symbol</label>
          <select 
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
            style={{
              width: '100%',
              padding: '0.75rem',
              background: 'rgba(255,255,255,0.05)',
              border: '1px solid var(--border-color)',
              borderRadius: '6px',
              color: 'var(--foreground)'
            }}
          >
            <option value="BTC/USDT">BTC/USDT</option>
            <option value="ETH/USDT">ETH/USDT</option>
            <option value="SOL/USDT">SOL/USDT</option>
          </select>
        </div>

        <button 
          type="submit"
          disabled={isSubmitting || !query}
          style={{
            padding: '0.75rem 1.5rem',
            background: 'var(--primary)',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            fontWeight: '600',
            cursor: query ? 'pointer' : 'not-allowed',
            opacity: query ? 1 : 0.5,
            transition: 'transform 0.1s'
          }}
          onMouseDown={(e) => e.currentTarget.style.transform = 'scale(0.98)'}
          onMouseUp={(e) => e.currentTarget.style.transform = 'scale(1)'}
        >
          {isSubmitting ? 'Initializing...' : 'Analyze'}
        </button>
      </form>
    </div>
  );
}
