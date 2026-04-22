'use client';

import { useState } from 'react';
import type { TrustTier } from '@/types/experience';

export function ObjectTypeBadge({ label }: { label: string }) {
  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        padding: '2px 8px',
        borderRadius: '999px',
        border: '1px solid var(--border-color)',
        color: 'var(--text-muted)',
        fontSize: '0.65rem',
        textTransform: 'uppercase',
        letterSpacing: '0.08em',
      }}
    >
      {label}
    </span>
  );
}

const TIER_STYLES: Record<TrustTier | 'inference' | 'diagnostic', { border: string; color: string; label: string }> = {
  fact: { border: '#3fb950', color: '#3fb950', label: 'Fact Record' },
  artifact: { border: '#58a6ff', color: '#58a6ff', label: 'System Artifact' },
  inference: { border: '#d29922', color: '#d29922', label: 'Inference' },
  diagnostic: { border: '#a371f7', color: '#a371f7', label: 'Diagnostic' },
  outcome_signal: { border: '#e3b341', color: '#e3b341', label: 'Outcome Signal' },
  hint: { border: '#ff7b72', color: '#ff7b72', label: 'Derived Hint' },
  missing: { border: '#8b949e', color: '#8b949e', label: 'Missing' },
  unavailable: { border: '#6e7681', color: '#6e7681', label: 'Unavailable' },
};

export function TrustTierBadge({
  tier,
}: {
  tier: TrustTier | 'inference' | 'diagnostic';
}) {
  const style = TIER_STYLES[tier];
  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        padding: '2px 8px',
        borderRadius: '999px',
        border: `1px solid ${style.border}`,
        color: style.color,
        fontSize: '0.65rem',
      }}
    >
      {style.label}
    </span>
  );
}

export function TimeSemantic({
  label,
  timestamp,
  staleAfterMinutes,
}: {
  label: string;
  timestamp: string | null | undefined;
  staleAfterMinutes?: number;
}) {
  const [now] = useState(() => Date.now());

  if (!timestamp) {
    return <span style={{ color: 'var(--text-muted)' }}>{label}: unavailable</span>;
  }

  const parsed = new Date(timestamp);
  if (Number.isNaN(parsed.getTime())) {
    return <span style={{ color: 'var(--text-muted)' }}>{label}: unavailable</span>;
  }

  const ageMinutes = Math.max(0, Math.round((now - parsed.getTime()) / 60000));
  const stale = staleAfterMinutes !== undefined && ageMinutes > staleAfterMinutes;

  return (
    <span style={{ color: stale ? 'var(--warn)' : 'var(--text-muted)' }}>
      {label}: {parsed.toLocaleString()} {stale ? '(stale)' : '(current)'}
    </span>
  );
}
