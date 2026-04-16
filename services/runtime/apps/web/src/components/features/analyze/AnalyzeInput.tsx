'use client';

import { useState } from 'react';

interface AnalyzeInputProps {
  onRun: (query: string, symbol: string) => void;
  isLoading: boolean;
}

export default function AnalyzeInput({ onRun, isLoading }: AnalyzeInputProps) {
  const [query, setQuery] = useState('');
  const [symbol, setSymbol] = useState('BTC/USDT');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query) onRun(query, symbol);
  };

  return (
    <div className="analyze-input glass" style={{
      padding: '1.5rem',
      borderRadius: '12px',
      height: '100%',
      // borderRight: '1px solid var(--border-color)'
    }}>
      <h3 style={{ marginBottom: '1.5rem', fontSize: '1rem', fontWeight: '600' }}>🔍 Execution Request</h3>
      
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Symbol / Contract</label>
          <select 
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
            style={{
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

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Analysis Query</label>
          <textarea 
            rows={6}
            placeholder="Describe your intent or market scenario..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            style={{
              padding: '0.75rem',
              background: 'rgba(255,255,255,0.05)',
              border: '1px solid var(--border-color)',
              borderRadius: '6px',
              color: 'var(--foreground)',
              resize: 'none',
              fontFamily: 'inherit'
            }}
          />
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Timeframe</label>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            {['15m', '1h', '4h', '1d'].map(tf => (
              <button key={tf} type="button" style={{
                flex: 1,
                padding: '0.5rem',
                fontSize: '0.75rem',
                borderRadius: '4px',
                border: '1px solid var(--border-color)',
                background: tf === '1h' ? 'rgba(137, 87, 229, 0.2)' : 'transparent',
                color: tf === '1h' ? 'var(--primary-hover)' : 'var(--text-muted)'
              }}>{tf}</button>
            ))}
          </div>
        </div>

        <button 
          type="submit"
          disabled={isLoading || !query}
          style={{
            marginTop: '1rem',
            padding: '1rem',
            background: 'var(--primary)',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            fontWeight: 'bold',
            cursor: query ? 'pointer' : 'not-allowed',
            opacity: query ? 1 : 0.5
          }}
        >
          {isLoading ? 'Running Analysis...' : '🚀 Execute Analyze'}
        </button>
      </form>

      <div style={{ marginTop: '2rem', fontSize: '0.7rem', color: 'var(--text-muted)', background: 'rgba(0,0,0,0.1)', padding: '1rem', borderRadius: '4px', border: '1px dashed var(--border-color)' }}>
        <strong>Note</strong>: This request will be audited by the Risk Engine before persistence.
      </div>
    </div>
  );
}
