'use client';

import type { ReactNode } from 'react';

interface StateCardProps {
  title: string;
  message: string;
  detail?: ReactNode;
}

function StateCard({ title, message, detail }: StateCardProps) {
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
      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: '1.5' }}>{message}</div>
      {detail ? <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{detail}</div> : null}
    </div>
  );
}

export function LoadingState({ message }: { message: string }) {
  return <StateCard title="Loading" message={message} />;
}

export function EmptyState({ message }: { message: string }) {
  return <StateCard title="No Data" message={message} />;
}

export function UnavailableState({ message, detail }: { message: string; detail?: ReactNode }) {
  return <StateCard title="Unavailable" message={message} detail={detail} />;
}

export function ErrorState({ message, detail }: { message: string; detail?: ReactNode }) {
  return <StateCard title="Error" message={message} detail={detail} />;
}
