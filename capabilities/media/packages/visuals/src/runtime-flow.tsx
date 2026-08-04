import type {CSSProperties} from 'react';

export const runtimeStages = [
  {id: 'participant', label: 'Participant / Host', detail: 'Admit work'},
  {id: 'workspace', label: 'Git Workspace', detail: 'Bind source'},
  {id: 'job', label: 'Durable Job', detail: 'Commit identity'},
  {id: 'attempt', label: 'Owned Attempt', detail: 'Supervise process'},
  {id: 'evidence', label: 'Result / Artifact', detail: 'Preserve evidence'},
  {id: 'recovery', label: 'Observe / Recover', detail: 'Continue safely'},
] as const;

export type RuntimeStage = (typeof runtimeStages)[number]['id'];

export interface RuntimeFlowProps {
  activeStage?: RuntimeStage;
  progress?: number;
  compact?: boolean;
  style?: CSSProperties;
}

export function RuntimeFlow({activeStage = 'job', progress = 1, compact = false, style}: RuntimeFlowProps) {
  const activeIndex = runtimeStages.findIndex((stage) => stage.id === activeStage);
  const boundedProgress = Math.max(0, Math.min(1, progress));

  return (
    <div
      aria-label="Ordivon Runtime execution flow"
      style={{
        display: 'grid',
        gridTemplateColumns: compact ? '1fr' : `repeat(${runtimeStages.length}, minmax(0, 1fr))`,
        gap: 1,
        background: 'color-mix(in srgb, var(--ordivon-color-paper) 18%, transparent)',
        border: '1px solid color-mix(in srgb, var(--ordivon-color-paper) 18%, transparent)',
        overflow: 'hidden',
        ...style,
      }}
    >
      {runtimeStages.map((stage, index) => {
        const reached = index < activeIndex || (index === activeIndex && boundedProgress > 0);
        const current = index === activeIndex;
        return (
          <div
            key={stage.id}
            data-stage={stage.id}
            data-active={current || undefined}
            style={{
              minHeight: compact ? 88 : 220,
              padding: compact ? 16 : 20,
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              background: current
                ? 'color-mix(in srgb, var(--ordivon-color-accent) 24%, var(--ordivon-color-ink-soft))'
                : reached
                  ? 'color-mix(in srgb, var(--ordivon-color-accent) 9%, var(--ordivon-color-ink-soft))'
                  : 'var(--ordivon-color-ink-soft)',
              color: current ? 'var(--ordivon-color-paper)' : 'var(--ordivon-color-paper-soft)',
              opacity: reached || current ? 1 : 0.55,
              transform: current ? `translateY(${(1 - boundedProgress) * 8}px)` : undefined,
            }}
          >
            <span
              style={{
                fontFamily: 'var(--ordivon-font-mono)',
                fontSize: 12,
                letterSpacing: '0.08em',
                textTransform: 'uppercase',
                color: current ? 'var(--ordivon-color-accent-soft)' : 'var(--ordivon-color-muted)',
              }}
            >
              {String(index + 1).padStart(2, '0')}
            </span>
            <div>
              <strong style={{display: 'block', fontSize: compact ? 18 : 24, lineHeight: 1.05}}>{stage.label}</strong>
              <span style={{display: 'block', marginTop: 8, fontSize: compact ? 13 : 15, color: 'var(--ordivon-color-muted)'}}>
                {stage.detail}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
