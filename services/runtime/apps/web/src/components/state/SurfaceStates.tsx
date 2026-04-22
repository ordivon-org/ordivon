'use client';

import type { ReactNode } from 'react';
import type { TrustTier } from '@/types/experience';
import { TrustTierBadge } from '@/components/state/ProductSignals';

interface StateCardProps {
  title: string;
  message: string;
  detail?: ReactNode;
  tier?: TrustTier;
}

function StateCard({ title, message, detail, tier }: StateCardProps) {
  return (
    <div
      style={{
        padding: '1rem',
        border: '1px dashed var(--border-color)',
        borderRadius: '10px',
        background: 'rgba(255,255,255,0.02)',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.45rem',
      }}
    >
      <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--foreground)' }}>{title}</div>
      {tier ? <TrustTierBadge tier={tier} /> : null}
      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: '1.5' }}>{message}</div>
      {detail ? <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{detail}</div> : null}
    </div>
  );
}

export function LoadingState({ message }: { message: string }) {
  return <StateCard title="Loading" message={message} />;
}

export function EmptyState({ message }: { message: string }) {
  return <StateCard title="No Data" message={message} tier="missing" />;
}

export function UnavailableState({ message, detail }: { message: string; detail?: ReactNode }) {
  return <StateCard title="Unavailable" message={message} detail={detail} tier="unavailable" />;
}

export function ErrorState({ message, detail }: { message: string; detail?: ReactNode }) {
  return <StateCard title="Error" message={message} detail={detail} tier="unavailable" />;
}
