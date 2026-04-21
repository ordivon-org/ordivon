'use client';

import { useState } from 'react';

import { apiGet } from '@/lib/api';
import { semanticNote, trustTierForSignal } from '@/lib/semanticSignals';
import type { TraceBundleResponse, TraceReferenceResponse } from '@/types/api';
import { TrustTierBadge } from '@/components/state/ProductSignals';
import { LoadingState, UnavailableState } from '@/components/state/SurfaceStates';

function TraceRefLine({ label, reference }: { label: string; reference: TraceReferenceResponse }) {
  return (
    <div>
      {label}: {reference.object_id ?? 'not linked yet'} ({reference.status}, {reference.relation_source})
    </div>
  );
}

export function TraceDetailPanel({
  path,
  buttonLabel = 'Show trace detail',
}: {
  path: string;
  buttonLabel?: string;
}) {
  const [expanded, setExpanded] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [bundle, setBundle] = useState<TraceBundleResponse | null>(null);

  const toggle = async () => {
    if (expanded) {
      setExpanded(false);
      return;
    }
    setExpanded(true);
    if (bundle || loading) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const result = await apiGet<TraceBundleResponse>(path);
      setBundle(result);
    } catch (err) {
      console.error('Failed to load trace detail:', err);
      setError('Trace detail is unavailable.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ marginTop: '0.55rem', display: 'flex', flexDirection: 'column', gap: '0.45rem' }}>
      <button
        type="button"
        onClick={() => {
          void toggle();
        }}
        style={{
          alignSelf: 'flex-start',
          padding: '4px 8px',
          borderRadius: '6px',
          border: '1px solid var(--border-color)',
          background: 'transparent',
          color: 'var(--text-muted)',
          fontSize: '0.72rem',
          cursor: 'pointer',
        }}
      >
        {expanded ? 'Hide trace detail' : buttonLabel}
      </button>
      {expanded && loading ? <LoadingState message="Loading trace detail..." /> : null}
      {expanded && error ? <UnavailableState message={error} detail="The surface cannot confirm links beyond the current trace API result." /> : null}
      {expanded && bundle ? (
        <div
          style={{
            padding: '0.75rem',
            border: '1px dashed var(--border-color)',
            borderRadius: '10px',
            background: 'rgba(255,255,255,0.02)',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.35rem',
            fontSize: '0.72rem',
            color: 'var(--text-muted)',
          }}
        >
          <div style={{ display: 'flex', gap: '0.45rem', alignItems: 'center', marginBottom: '0.1rem' }}>
            <TrustTierBadge tier={trustTierForSignal('trace_detail')} />
            <span style={{ color: 'var(--foreground)', fontWeight: 600 }}>
              Trace detail for {bundle.root_type} {bundle.root_id}
            </span>
          </div>
          <TraceRefLine label="Analysis" reference={bundle.analysis} />
          <TraceRefLine label="Recommendation" reference={bundle.recommendation} />
          <TraceRefLine label="Review" reference={bundle.review} />
          <TraceRefLine label="Workflow run" reference={bundle.workflow_run} />
          <TraceRefLine label="Intelligence run" reference={bundle.intelligence_run} />
          <TraceRefLine label="Primary receipt" reference={bundle.execution_receipt} />
          <TraceRefLine label="Review receipt" reference={bundle.review_execution_receipt} />
          <TraceRefLine label="Outcome" reference={bundle.outcome} />
          <TraceRefLine label="Knowledge signal" reference={bundle.knowledge_feedback} />
          <div>{semanticNote('trace_detail')}</div>
        </div>
      ) : null}
    </div>
  );
}
