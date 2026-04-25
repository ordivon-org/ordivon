'use client';

import { FormEvent, useState } from 'react';

import { getApiBaseUrl } from '@/lib/api';
import { getFinanceAnalyzeSurfaceOptions } from '@packs/finance/analyze_surface';

type ExplicitBooleanAnswer = '' | 'yes' | 'no';

interface DecisionIntakeValidationError {
  field: string;
  code: string;
  message: string;
}

interface GovernanceAdvisoryHintResponse {
  target: string;
  hint_type: string;
  summary: string;
  evidence_object_ids: string[];
}

interface DecisionIntakeResponse {
  id: string;
  pack_id: string;
  intake_type: string;
  status: 'validated' | 'invalid';
  validation_errors: DecisionIntakeValidationError[];
  governance_status: 'not_started' | 'execute' | 'escalate' | 'reject';
  advisory_hints?: GovernanceAdvisoryHintResponse[];
  created_at: string;
}

interface DecisionIntakePanelProps {
  prioritized?: boolean;
}

function explicitBooleanValue(value: ExplicitBooleanAnswer): boolean | null {
  if (value === 'yes') {
    return true;
  }
  if (value === 'no') {
    return false;
  }
  return null;
}

export function DecisionIntakePanel({ prioritized = false }: DecisionIntakePanelProps) {
  const financeAnalyze = getFinanceAnalyzeSurfaceOptions();
  const [symbol, setSymbol] = useState(financeAnalyze.defaultSymbol);
  const [timeframe, setTimeframe] = useState(financeAnalyze.defaultTimeframe);
  const [direction, setDirection] = useState('observe');
  const [thesis, setThesis] = useState('');
  const [entryCondition, setEntryCondition] = useState('');
  const [invalidationCondition, setInvalidationCondition] = useState('');
  const [stopLoss, setStopLoss] = useState('');
  const [target, setTarget] = useState('');
  const [positionSizeUsdt, setPositionSizeUsdt] = useState('');
  const [maxLossUsdt, setMaxLossUsdt] = useState('');
  const [riskUnitUsdt, setRiskUnitUsdt] = useState('');
  const [isRevengeTrade, setIsRevengeTrade] = useState<ExplicitBooleanAnswer>('');
  const [isChasing, setIsChasing] = useState<ExplicitBooleanAnswer>('');
  const [emotionalState, setEmotionalState] = useState('');
  const [confidence, setConfidence] = useState('');
  const [notes, setNotes] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [result, setResult] = useState<DecisionIntakeResponse | null>(null);
  const [isGoverning, setIsGoverning] = useState(false);

  const handleGovern = async () => {
    if (!result) return;
    setIsGoverning(true);
    setSubmitError(null);

    try {
      const response = await fetch(`${getApiBaseUrl()}/api/v1/finance-decisions/intake/${result.id}/govern`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error(`Governance request failed with status ${response.status}`);
      }

      const data: DecisionIntakeResponse = await response.json();
      setResult(data);
    } catch (error) {
      console.error('Governance failed:', error);
      setSubmitError('Governance step failed to execute.');
    } finally {
      setIsGoverning(false);
    }
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsSubmitting(true);
    setSubmitError(null);
    setResult(null);

    try {
      const response = await fetch(`${getApiBaseUrl()}/api/v1/finance-decisions/intake`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          symbol,
          timeframe,
          direction,
          thesis: thesis || null,
          entry_condition: entryCondition || null,
          invalidation_condition: invalidationCondition || null,
          stop_loss: stopLoss || null,
          target: target || null,
          position_size_usdt: positionSizeUsdt === '' ? null : Number(positionSizeUsdt),
          max_loss_usdt: maxLossUsdt === '' ? null : Number(maxLossUsdt),
          risk_unit_usdt: riskUnitUsdt === '' ? null : Number(riskUnitUsdt),
          is_revenge_trade: explicitBooleanValue(isRevengeTrade),
          is_chasing: explicitBooleanValue(isChasing),
          emotional_state: emotionalState || null,
          confidence: confidence === '' ? null : Number(confidence),
          rule_exceptions: [],
          notes: notes || null,
        }),
      });

      if (!response.ok) {
        throw new Error(`Decision intake request failed with status ${response.status}`);
      }

      const data: DecisionIntakeResponse = await response.json();
      setResult(data);
    } catch (error) {
      console.error('Decision intake failed:', error);
      setSubmitError('Decision intake is currently unavailable. No governance step has started.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="glass console-card" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.45rem' }}>
        <h2 id="decision-intake-panel" style={{ margin: 0, fontSize: '1rem', fontWeight: 600 }}>
          Controlled Decision Intake
        </h2>
        <div className="console-card__copy">
          Capture a high-consequence finance decision as a structured intake before any governance or action-plan step begins.
        </div>
        <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
          Finance is the first pressure-test pack here. Stop-loss numeric semantics are deferred to Batch 2; Batch 1 validates
          stop-loss presence only.
        </div>
        {prioritized ? (
          <div style={{ fontSize: '0.72rem', color: 'var(--accent)' }}>
            Controlled mode is active from the command center handoff.
          </div>
        ) : null}
      </div>

      {submitError ? (
        <div
          className="glass console-card console-card--soft"
          style={{
            border: '1px solid rgba(248, 81, 73, 0.35)',
            background: 'rgba(248, 81, 73, 0.08)',
          }}
        >
          {submitError}
        </div>
      ) : null}

      <form onSubmit={handleSubmit} style={{ display: 'grid', gap: '1rem' }}>
        <div style={{ display: 'grid', gap: '1rem', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))' }}>
          <label style={{ display: 'grid', gap: '0.45rem' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Symbol / Contract</span>
            <select value={symbol} onChange={(event) => setSymbol(event.target.value)} aria-label="Decision symbol">
              {financeAnalyze.supportedSymbols.map((supportedSymbol) => (
                <option key={supportedSymbol} value={supportedSymbol}>
                  {supportedSymbol}
                </option>
              ))}
            </select>
          </label>

          <label style={{ display: 'grid', gap: '0.45rem' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Timeframe</span>
            <select value={timeframe} onChange={(event) => setTimeframe(event.target.value)} aria-label="Decision timeframe">
              {financeAnalyze.supportedTimeframes.map((supportedTimeframe) => (
                <option key={supportedTimeframe} value={supportedTimeframe}>
                  {supportedTimeframe}
                </option>
              ))}
            </select>
          </label>

          <label style={{ display: 'grid', gap: '0.45rem' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Direction</span>
            <select value={direction} onChange={(event) => setDirection(event.target.value)} aria-label="Decision direction">
              <option value="long">long</option>
              <option value="short">short</option>
              <option value="hold">hold</option>
              <option value="observe">observe</option>
            </select>
          </label>
        </div>

        <label style={{ display: 'grid', gap: '0.45rem' }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Thesis</span>
          <textarea aria-label="Decision thesis" rows={3} value={thesis} onChange={(event) => setThesis(event.target.value)} />
        </label>

        <div style={{ display: 'grid', gap: '1rem', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))' }}>
          <label style={{ display: 'grid', gap: '0.45rem' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Entry condition</span>
            <input aria-label="Entry condition" value={entryCondition} onChange={(event) => setEntryCondition(event.target.value)} />
          </label>

          <label style={{ display: 'grid', gap: '0.45rem' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Invalidation condition</span>
            <input
              aria-label="Invalidation condition"
              value={invalidationCondition}
              onChange={(event) => setInvalidationCondition(event.target.value)}
            />
          </label>
        </div>

        <div style={{ display: 'grid', gap: '1rem', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))' }}>
          <label style={{ display: 'grid', gap: '0.45rem' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Stop loss</span>
            <input aria-label="Stop loss" value={stopLoss} onChange={(event) => setStopLoss(event.target.value)} />
          </label>

          <label style={{ display: 'grid', gap: '0.45rem' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Target</span>
            <input aria-label="Target" value={target} onChange={(event) => setTarget(event.target.value)} />
          </label>
        </div>

        <div style={{ display: 'grid', gap: '1rem', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))' }}>
          <label style={{ display: 'grid', gap: '0.45rem' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Position size (USDT)</span>
            <input
              aria-label="Position size usdt"
              type="number"
              min="0"
              step="0.01"
              value={positionSizeUsdt}
              onChange={(event) => setPositionSizeUsdt(event.target.value)}
            />
          </label>

          <label style={{ display: 'grid', gap: '0.45rem' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Max loss (USDT)</span>
            <input
              aria-label="Max loss usdt"
              type="number"
              min="0"
              step="0.01"
              value={maxLossUsdt}
              onChange={(event) => setMaxLossUsdt(event.target.value)}
            />
          </label>

          <label style={{ display: 'grid', gap: '0.45rem' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Risk unit (USDT)</span>
            <input
              aria-label="Risk unit usdt"
              type="number"
              min="0"
              step="0.01"
              value={riskUnitUsdt}
              onChange={(event) => setRiskUnitUsdt(event.target.value)}
            />
          </label>
        </div>

        <div style={{ display: 'grid', gap: '1rem', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))' }}>
          <label style={{ display: 'grid', gap: '0.45rem' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Is this a revenge trade?</span>
            <select
              aria-label="Is revenge trade"
              value={isRevengeTrade}
              onChange={(event) => setIsRevengeTrade(event.target.value as ExplicitBooleanAnswer)}
            >
              <option value="">Select answer</option>
              <option value="yes">yes</option>
              <option value="no">no</option>
            </select>
          </label>

          <label style={{ display: 'grid', gap: '0.45rem' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Is this chasing?</span>
            <select aria-label="Is chasing" value={isChasing} onChange={(event) => setIsChasing(event.target.value as ExplicitBooleanAnswer)}>
              <option value="">Select answer</option>
              <option value="yes">yes</option>
              <option value="no">no</option>
            </select>
          </label>

          <label style={{ display: 'grid', gap: '0.45rem' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Emotional state</span>
            <input aria-label="Emotional state" value={emotionalState} onChange={(event) => setEmotionalState(event.target.value)} />
          </label>

          <label style={{ display: 'grid', gap: '0.45rem' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Confidence (0..1)</span>
            <input
              aria-label="Confidence"
              type="number"
              min="0"
              max="1"
              step="0.05"
              value={confidence}
              onChange={(event) => setConfidence(event.target.value)}
            />
          </label>
        </div>

        <label style={{ display: 'grid', gap: '0.45rem' }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Notes</span>
          <textarea aria-label="Decision notes" rows={3} value={notes} onChange={(event) => setNotes(event.target.value)} />
        </label>

        <button type="submit" disabled={isSubmitting} style={{ width: 'fit-content', padding: '0.8rem 1.1rem' }}>
          {isSubmitting ? 'Saving intake...' : 'Save controlled decision intake'}
        </button>
      </form>

      {result ? (
        <div className="glass console-card console-card--soft" style={{ display: 'grid', gap: '0.65rem' }}>
          <div className="console-card__title">Intake persistence result</div>
          <div className="console-card__copy">
            Status: <strong>{result.status}</strong> | Governance: <strong>{result.governance_status}</strong>
          </div>
          {result.validation_errors.length ? (
            <ul style={{ margin: 0, paddingLeft: '1.2rem', display: 'grid', gap: '0.35rem' }}>
              {result.validation_errors.map((error) => (
                <li key={`${error.field}-${error.code}`}>
                  <strong>{error.field}</strong>: {error.message}
                </li>
              ))}
            </ul>
          ) : (
            <div className="console-card__copy">
              Intake is persisted. {result.governance_status === 'not_started' ? 'No governance step has started yet.' : 'Governance check complete.'}
            </div>
          )}

          {result.governance_status === 'not_started' && result.status === 'validated' && (
            <button
              type="button"
              onClick={handleGovern}
              disabled={isGoverning}
              style={{ width: 'fit-content', padding: '0.6rem 1rem', marginTop: '0.5rem', background: 'var(--accent)', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
            >
              {isGoverning ? 'Running Governance...' : 'Run Trading Discipline Governance'}
            </button>
          )}

          {result.advisory_hints && result.advisory_hints.length > 0 && (
            <div style={{ marginTop: '1rem', borderTop: '1px solid var(--border)', paddingTop: '0.8rem' }}>
              <div className="console-card__title">Advisory Hints</div>
              <ul style={{ margin: 0, paddingLeft: '1.2rem', display: 'grid', gap: '0.35rem', fontSize: '0.85rem' }}>
                {result.advisory_hints.map((hint, i) => (
                  <li key={i}>
                    <strong>[{hint.hint_type.toUpperCase()}]</strong> {hint.summary}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      ) : null}
    </div>
  );
}
