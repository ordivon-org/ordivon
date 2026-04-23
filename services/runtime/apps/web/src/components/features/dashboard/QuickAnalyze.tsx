'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

import { ObjectTypeBadge, TrustTierBadge } from '@/components/state/ProductSignals';
import { getFinanceAnalyzeSurfaceOptions } from '@packs/finance/analyze_surface';

export default function QuickAnalyze() {
  const router = useRouter();
  const financeAnalyze = getFinanceAnalyzeSurfaceOptions();
  const [query, setQuery] = useState('');
  const [symbol, setSymbol] = useState(financeAnalyze.defaultSymbol);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query) return;

    setIsSubmitting(true);
    const params = new URLSearchParams({
      query,
      symbol,
      timeframe: financeAnalyze.defaultTimeframe,
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
        This is the command-center entry into the workflow execution workspace. It seeds the analyze route and does not place or execute an external order.
      </div>
      <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '1rem', lineHeight: '1.5' }}>
        {financeAnalyze.copy.dashboardHint} Default timeframe: <span style={{ color: 'var(--foreground)' }}>{financeAnalyze.defaultTimeframe}</span>.
      </div>

      <form onSubmit={handleAnalyze} style={{ display: 'flex', gap: '1rem', alignItems: 'flex-end' }}>
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <label htmlFor="quick-analyze-query" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            {financeAnalyze.labels.query}
          </label>
          <input
            id="quick-analyze-query"
            type="text"
            placeholder={financeAnalyze.copy.queryPlaceholder}
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
          <label htmlFor="quick-analyze-symbol" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            {financeAnalyze.labels.symbol}
          </label>
          <select
            id="quick-analyze-symbol"
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
            {financeAnalyze.supportedSymbols.map((supportedSymbol) => (
              <option key={supportedSymbol} value={supportedSymbol}>
                {supportedSymbol}
              </option>
            ))}
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
