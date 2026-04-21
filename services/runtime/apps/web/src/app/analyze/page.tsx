'use client';

import { Suspense, useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';

import AnalyzeInput from '@/components/features/analyze/AnalyzeInput';
import GovernancePanel from '@/components/features/analyze/GovernancePanel';
import ReasoningPanel from '@/components/features/analyze/ReasoningPanel';
import { TrustTierBadge } from '@/components/state/ProductSignals';
import type { AnalyzeWorkspaceResult } from '@/components/features/analyze/types';

function AnalyzePageInner() {
  const searchParams = useSearchParams();
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<AnalyzeWorkspaceResult | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    const query = searchParams.get('query');
    const symbol = searchParams.get('symbol');
    const autoRun = searchParams.get('autoRun');
    if (autoRun === 'true' && query && symbol) {
      void handleRunAnalysis(query, symbol);
    }
  }, [searchParams]);

  const handleRunAnalysis = async (query: string, symbol: string) => {
    setIsLoading(true);
    setResult(null);
    setErrorMessage(null);

    try {
      const response = await fetch('http://localhost:8000/api/v1/analyze-and-suggest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, symbols: [symbol] }),
      });

      if (!response.ok) {
        throw new Error(`Analysis request failed with status ${response.status}`);
      }

      const data: AnalyzeWorkspaceResult = await response.json();
      setResult(data);
    } catch (error) {
      console.error('Analysis failed:', error);
      setResult(null);
      setErrorMessage('Analyze API is currently unavailable. No analysis result was generated.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="analyze-page" style={{ height: 'calc(100vh - 4rem)' }}>
      <header style={{ marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>Reasoning Workspace</h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
          Execute an analysis workflow request and inspect the resulting inference and governance artifacts.
        </p>
        <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap', marginTop: '0.75rem' }}>
          <TrustTierBadge tier="inference" />
          <TrustTierBadge tier="artifact" />
        </div>
      </header>

      {errorMessage && (
        <div
          className="glass"
          style={{
            marginBottom: '1rem',
            padding: '0.9rem 1rem',
            borderRadius: '10px',
            border: '1px solid rgba(248, 81, 73, 0.35)',
            background: 'rgba(248, 81, 73, 0.08)',
            color: 'var(--foreground)',
            fontSize: '0.85rem',
          }}
        >
          {errorMessage}
        </div>
      )}

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '300px 1fr 300px',
          gap: '1.5rem',
          height: 'calc(100% - 4rem)',
        }}
      >
        <AnalyzeInput onRun={handleRunAnalysis} isLoading={isLoading} />
        <ReasoningPanel data={result} isLoading={isLoading} />
        <GovernancePanel data={result} isLoading={isLoading} />
      </div>
    </div>
  );
}

export default function AnalyzePage() {
  return (
    <Suspense fallback={<div style={{ padding: '2rem', color: 'var(--text-muted)' }}>Loading workspace...</div>}>
      <AnalyzePageInner />
    </Suspense>
  );
}
