'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

import { ObjectTypeBadge, TrustTierBadge } from '@/components/state/ProductSignals';

export default function QuickAnalyze() {
  const router = useRouter();
  const [query, setQuery] = useState('');
  const [symbol, setSymbol] = useState('BTC/USDT');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query) return;

    setIsSubmitting(true);
    const params = new URLSearchParams({
      query,
      symbol,
      autoRun: 'true',
    });

    setTimeout(() => {
      router.push(`/analyze?${params.toString()}`);
    }, 300);
  };

  return (
    <div
      className="quick-analyze glass"
      style={{
        padding: '1.5rem',
        borderRadius: '12px',
        marginBottom: '1.5rem',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: '0.75rem', marginBottom: '1rem', alignItems: 'center' }}>
        <h3 style={{ fontSize: '1rem', fontWeight: '600' }}>Quick Analyze</h3>
        <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
          <ObjectTypeBadge label="Workflow Request" />
          <TrustTierBadge tier="artifact" />
        </div>
      </div>
      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '1rem', lineHeight: '1.5' }}>
        This action opens the reasoning workspace and submits an analysis request. It does not place or execute an external order.
      </div>

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
              outline: 'none',
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
              color: 'var(--foreground)',
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
            transition: 'transform 0.1s',
          }}
          onMouseDown={(e) => {
            e.currentTarget.style.transform = 'scale(0.98)';
          }}
          onMouseUp={(e) => {
            e.currentTarget.style.transform = 'scale(1)';
          }}
        >
          {isSubmitting ? 'Initializing...' : 'Analyze'}
        </button>
      </form>
    </div>
  );
}
