'use client';

import { useState } from 'react';
import { getFinanceAnalyzeSurfaceOptions } from '@packs/finance/analyze_surface';

interface AnalyzeInputProps {
  onRun: (query: string, symbol: string, timeframe: string) => void;
  isLoading: boolean;
  initialQuery?: string;
  initialSymbol?: string;
  initialTimeframe?: string;
}

export default function AnalyzeInput({
  onRun,
  isLoading,
  initialQuery = '',
  initialSymbol,
  initialTimeframe,
}: AnalyzeInputProps) {
  const financeAnalyze = getFinanceAnalyzeSurfaceOptions();
  const resolvedInitialSymbol = financeAnalyze.supportedSymbols.includes(initialSymbol ?? '')
    ? (initialSymbol as string)
    : financeAnalyze.defaultSymbol;
  const resolvedInitialTimeframe = financeAnalyze.supportedTimeframes.includes(initialTimeframe ?? '')
    ? (initialTimeframe as string)
    : financeAnalyze.defaultTimeframe;
  const [query, setQuery] = useState(initialQuery);
  const [symbol, setSymbol] = useState(resolvedInitialSymbol);
  const [timeframe, setTimeframe] = useState(resolvedInitialTimeframe);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query) {
      onRun(query, symbol, timeframe);
    }
  };

  return (
    <div
      className="analyze-input glass"
      style={{
        padding: '1.5rem',
        borderRadius: '12px',
        height: '100%',
      }}
    >
      <h3 style={{ marginBottom: '1.5rem', fontSize: '1rem', fontWeight: '600' }}>Workflow Execution Request</h3>

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{financeAnalyze.labels.symbol}</label>
          <select
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
            style={{
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

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{financeAnalyze.labels.query}</label>
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
              fontFamily: 'inherit',
            }}
          />
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{financeAnalyze.labels.timeframe}</label>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            {financeAnalyze.supportedTimeframes.map((supportedTimeframe) => (
              <button
                key={supportedTimeframe}
                type="button"
                onClick={() => setTimeframe(supportedTimeframe)}
                style={{
                  flex: 1,
                  padding: '0.5rem',
                  fontSize: '0.75rem',
                  borderRadius: '4px',
                  border: '1px solid var(--border-color)',
                  background: supportedTimeframe === timeframe ? 'rgba(137, 87, 229, 0.2)' : 'transparent',
                  color: supportedTimeframe === timeframe ? 'var(--primary-hover)' : 'var(--text-muted)',
                  cursor: 'pointer',
                }}
              >
                {supportedTimeframe}
              </button>
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
            opacity: query ? 1 : 0.5,
          }}
        >
          {isLoading ? 'Running Analysis...' : 'Execute Analyze Workflow'}
        </button>
      </form>

      <div
        style={{
          marginTop: '2rem',
          fontSize: '0.7rem',
          color: 'var(--text-muted)',
          background: 'rgba(0,0,0,0.1)',
          padding: '1rem',
          borderRadius: '4px',
          border: '1px dashed var(--border-color)',
        }}
      >
        <strong>Note</strong>: {financeAnalyze.copy.analyzeHint}
      </div>
    </div>
  );
}
