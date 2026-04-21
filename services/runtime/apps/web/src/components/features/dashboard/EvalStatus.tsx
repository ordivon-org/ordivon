'use client';

import { useEffect, useState } from 'react';

import { apiGet } from '@/lib/api';
import { ErrorState, LoadingState } from '@/components/state/SurfaceStates';
import { ObjectTypeBadge, TimeSemantic, TrustTierBadge } from '@/components/state/ProductSignals';
import type { EvalRunResponse } from '@/types/api';
import type { ExperienceState } from '@/types/experience';

export default function EvalStatus() {
  const [evalData, setEvalData] = useState<EvalRunResponse | null>(null);
  const [state, setState] = useState<ExperienceState>('loading');

  useEffect(() => {
    const fetchEval = async () => {
      try {
        const data = await apiGet<EvalRunResponse>('/api/v1/evals/latest');
        setEvalData(data);
        setState('ready');
      } catch (e) {
        console.error('Failed to fetch eval status:', e);
        setEvalData(null);
        setState('error');
      }
    };

    void fetchEval();
  }, []);

  if (state === 'loading') {
    return <LoadingState message="Loading evaluation diagnostics..." />;
  }

  if (state === 'error' || !evalData) {
    return (
      <ErrorState
        message="Evaluation diagnostics could not be loaded from /api/v1/evals/latest."
        detail="This widget cannot distinguish between no eval run and an API failure until the request succeeds."
      />
    );
  }

  return (
    <div className="eval-status glass" style={{ padding: '1.25rem', borderRadius: '12px', height: '100%', borderLeft: '4px solid var(--primary)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: '0.75rem', marginBottom: '1rem', alignItems: 'center' }}>
        <h3 style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>Evaluation Quality</h3>
        <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
          <ObjectTypeBadge label="Diagnostic" />
          <TrustTierBadge tier="diagnostic" />
        </div>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
        <div>
          <div style={{ fontSize: '1.25rem', fontWeight: 'bold', color: 'var(--foreground)' }}>
            {Math.round(evalData.summary.avg_total_score * 100)}%
          </div>
          <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>QUALITY SCORE</div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <span className={`badge badge-${evalData.gate_decision === 'PASS' ? 'allow' : 'block'}`}>
            {evalData.gate_decision}
          </span>
          <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', marginTop: '4px' }}>GATE STATUS</div>
        </div>
      </div>

      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span>Parse Failure:</span>
          <span style={{ color: evalData.summary.parse_failure_rate > 0.05 ? 'var(--error)' : 'var(--success)' }}>
            {(evalData.summary.parse_failure_rate * 100).toFixed(1)}%
          </span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span>Aggressive Action:</span>
          <span style={{ color: evalData.summary.aggressive_action_rate > 0.15 ? 'var(--warn)' : 'var(--foreground)' }}>
            {(evalData.summary.aggressive_action_rate * 100).toFixed(1)}%
          </span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span>Cases Passed:</span>
          <span>{evalData.summary.passed_cases}/{evalData.summary.total_cases}</span>
        </div>
        <div style={{ marginTop: '4px', textAlign: 'center', opacity: 0.6 }}>
          Run ID: {evalData.run_id.slice(-8)}
        </div>
        <div style={{ marginTop: '4px', textAlign: 'center', opacity: 0.6 }}>
          <TimeSemantic label="Run time" timestamp={evalData.timestamp} staleAfterMinutes={720} />
        </div>
      </div>
    </div>
  );
}
