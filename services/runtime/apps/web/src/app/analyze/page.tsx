'use client';

import { Suspense, useEffect, useState } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';

import AnalyzeInput from '@/components/features/analyze/AnalyzeInput';
import GovernancePanel from '@/components/features/analyze/GovernancePanel';
import ReasoningPanel from '@/components/features/analyze/ReasoningPanel';
import { TrustTierBadge } from '@/components/state/ProductSignals';
import { ConsolePageFrame } from '@/components/workspace/ConsolePageFrame';
import { getApiBaseUrl } from '@/lib/api';
import type { AnalyzeWorkspaceResult } from '@/components/features/analyze/types';

function AnalyzePageInner() {
  const searchParams = useSearchParams();
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<AnalyzeWorkspaceResult | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleRunAnalysis = async (query: string, symbol: string, timeframe?: string) => {
    setIsLoading(true);
    setResult(null);
    setErrorMessage(null);

    try {
      const response = await fetch(`${getApiBaseUrl()}/api/v1/analyze-and-suggest`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, symbols: [symbol], timeframe }),
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

  useEffect(() => {
    const query = searchParams.get('query');
    const symbol = searchParams.get('symbol');
    const timeframe = searchParams.get('timeframe');
    const autoRun = searchParams.get('autoRun');
    if (autoRun === 'true' && query && symbol) {
      void handleRunAnalysis(query, symbol, timeframe ?? undefined);
    }
  }, [searchParams]);

  const recommendationId =
    typeof result?.metadata?.recommendation_id === 'string'
      ? result.metadata.recommendation_id
      : typeof result?.recommendation_id === 'string'
        ? result.recommendation_id
        : null;
  const decision = result?.decision ?? null;
  const needsReviewHandoff = Boolean(recommendationId && decision === 'execute');
  const reviewHref = recommendationId ? `/reviews?recommendation_id=${recommendationId}` : '/reviews';

  return (
    <div className="analyze-page" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <header style={{ marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>Workflow Execution Workspace</h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
          Execute a new analysis workflow here, inspect the resulting inference and governance artifacts, then hand off broader monitoring to the command center or supervision-heavy follow-through to the review workbench.
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
          alignItems: 'stretch',
        }}
      >
        <section aria-labelledby="analyze-request-panel">
          <AnalyzeInput
            onRun={handleRunAnalysis}
            isLoading={isLoading}
            initialQuery={searchParams.get('query') ?? ''}
            initialSymbol={searchParams.get('symbol') ?? undefined}
            initialTimeframe={searchParams.get('timeframe') ?? undefined}
          />
        </section>
        <section aria-labelledby="analyze-result-panel">
          <ReasoningPanel data={result} isLoading={isLoading} />
        </section>
        <section aria-labelledby="analyze-governance-panel">
          <GovernancePanel data={result} isLoading={isLoading} />
        </section>
      </div>
      {result ? (
        <section
          className="glass"
          style={{
            marginTop: '1.5rem',
            padding: '1rem 1.25rem',
            borderRadius: '12px',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.75rem',
          }}
        >
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
            Next Actions
          </div>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            This workspace owns execution and immediate inspection only. Use the command center to watch the broader system, and continue in the review workbench when the recommendation needs supervision.
          </div>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
              gap: '0.75rem',
            }}
          >
            <div
              style={{
                border: '1px solid var(--border-color)',
                borderRadius: '10px',
                padding: '0.9rem 1rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.35rem',
              }}
            >
              <div style={{ color: 'var(--foreground)', fontWeight: 600 }}>1. Confirm the result</div>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                Review the reasoning summary and governance result here before continuing.
              </div>
            </div>
            <div
              style={{
                border: '1px solid var(--border-color)',
                borderRadius: '10px',
                padding: '0.9rem 1rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.35rem',
              }}
            >
              <div style={{ color: 'var(--foreground)', fontWeight: 600 }}>
                {needsReviewHandoff ? '2. Hand off to supervision' : '2. Choose the next surface'}
              </div>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                {needsReviewHandoff
                  ? 'This result produced a recommendation. Continue in the review workbench for recommendation, trace, and outcome follow-through.'
                  : 'If no supervision path is active yet, use the command center for broad monitoring and the review workbench for queue-driven supervision.'}
              </div>
            </div>
          </div>
          <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
            <Link href="/" style={{ color: 'var(--primary-hover)' }}>
              Return to command center
            </Link>
            {recommendationId ? (
              <Link href={reviewHref} style={{ color: 'var(--primary-hover)' }}>
                Hand off recommendation to review workbench
              </Link>
            ) : (
              <Link href="/reviews" style={{ color: 'var(--primary-hover)' }}>
                Open review workbench
              </Link>
            )}
          </div>
        </section>
      ) : null}
    </div>
  );
}

export default function AnalyzePage() {
  return (
    <ConsolePageFrame>
      <Suspense fallback={<div style={{ padding: '2rem', color: 'var(--text-muted)' }}>Loading workspace...</div>}>
        <AnalyzePageInner />
      </Suspense>
    </ConsolePageFrame>
  );
}
