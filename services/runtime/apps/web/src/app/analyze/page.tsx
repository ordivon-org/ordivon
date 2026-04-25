'use client';

import { Suspense, useEffect, useState } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';

import AnalyzeInput from '@/components/features/analyze/AnalyzeInput';
import { DecisionIntakePanel } from '@/components/features/analyze/DecisionIntakePanel';
import { GovernanceDetailInspector } from '@/components/features/analyze/GovernanceDetailInspector';
import GovernancePanel from '@/components/features/analyze/GovernancePanel';
import ReasoningPanel from '@/components/features/analyze/ReasoningPanel';
import { ConsoleSection } from '@/components/layout/ConsoleSection';
import { MainContentGrid, RightDetailPanel } from '@/components/layout/MainContentGrid';
import { PageHeader } from '@/components/layout/PageHeader';
import { TrustTierBadge } from '@/components/state/ProductSignals';
import { ConsolePageFrame } from '@/components/workspace/ConsolePageFrame';
import { getApiBaseUrl } from '@/lib/api';
import type { AnalyzeWorkspaceResult } from '@/components/features/analyze/types';

function AnalyzePageInner() {
  const searchParams = useSearchParams();
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<AnalyzeWorkspaceResult | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const isControlledMode = searchParams.get('mode') === 'controlled';

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
    <div className="console-page analyze-page">
      <PageHeader
        eyebrow="Experience / Execution Workspace"
        title="Workflow Execution Workspace"
        description="Execute a new analysis workflow here, inspect the resulting inference and governance artifacts, then hand off broader monitoring to the command center or supervision-heavy follow-through to the review workbench."
        badges={
          <>
          <TrustTierBadge tier="inference" />
          <TrustTierBadge tier="artifact" />
          </>
        }
      />

      {errorMessage && (
        <div
          className="glass console-card"
          style={{
            border: '1px solid rgba(248, 81, 73, 0.35)',
            background: 'rgba(248, 81, 73, 0.08)',
            color: 'var(--text-primary)',
            fontSize: '0.85rem',
          }}
        >
          {errorMessage}
        </div>
      )}

      {isControlledMode ? (
        <ConsoleSection
          title="Controlled Decision Intake"
          description="Batch 1 captures structured intake only. Governance, receipts, outcomes, reviews, and knowledge remain deferred."
        >
          <DecisionIntakePanel prioritized />
        </ConsoleSection>
      ) : null}

      <ConsoleSection
        title="Execution Surface"
        description="This workspace owns request entry, reasoning inspection, and governance review for the current run."
      >
        <MainContentGrid columns="three-up">
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
          <RightDetailPanel>
            <section aria-labelledby="analyze-governance-panel">
              <GovernancePanel data={result} isLoading={isLoading} />
            </section>
          </RightDetailPanel>
        </MainContentGrid>
      </ConsoleSection>
      {result ? (
        <ConsoleSection
          title="Next Actions"
          description="Use execution here to confirm the run, then move broader monitoring back to the command center or hand supervision to the review workbench."
        >
          <div className="glass console-card console-card--soft" style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <div className="console-card__copy">
            This workspace owns execution and immediate inspection only. Use the command center to watch the broader system, and continue in the review workbench when the recommendation needs supervision.
          </div>
          <MainContentGrid columns="two-up">
            <div className="glass console-card console-card--soft" style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
              <div className="console-card__title">1. Confirm the result</div>
              <div className="console-card__copy">
                Review the reasoning summary and governance result here before continuing.
              </div>
            </div>
            <div className="glass console-card console-card--soft" style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
              <div className="console-card__title">
                {needsReviewHandoff ? '2. Hand off to supervision' : '2. Choose the next surface'}
              </div>
              <div className="console-card__copy">
                {needsReviewHandoff
                  ? 'This result produced a recommendation. Continue in the review workbench for recommendation, trace, and outcome follow-through.'
                  : 'If no supervision path is active yet, use the command center for broad monitoring and the review workbench for queue-driven supervision.'}
              </div>
            </div>
          </MainContentGrid>
          <div className="console-link-row">
            <Link href="/" className="console-link">
              Return to command center
            </Link>
            {recommendationId ? (
              <Link href={reviewHref} className="console-link">
                Hand off recommendation to review workbench
              </Link>
            ) : (
              <Link href="/reviews" className="console-link">
                Open review workbench
              </Link>
            )}
          </div>
          <GovernanceDetailInspector data={result} />
          </div>
        </ConsoleSection>
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
