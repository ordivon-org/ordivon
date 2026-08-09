import type {CSSProperties, ReactNode} from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import '@ordivon/identity/tokens.css';
import {compactProofValue, runtimeDemoReceipt} from './runtime-demo-receipt.ts';

const card: CSSProperties = {
  padding: 28,
  border: '1px solid color-mix(in srgb, var(--ordivon-color-paper) 20%, transparent)',
  background: 'var(--ordivon-color-ink-soft)',
};

function ProofCard({label, children, style}: {label: string; children: ReactNode; style?: CSSProperties}) {
  return (
    <div style={{...card, ...style}}>
      <p style={{margin: 0, color: 'var(--ordivon-color-muted)', fontFamily: 'var(--ordivon-font-mono)', fontSize: 17, letterSpacing: '0.1em', textTransform: 'uppercase'}}>
        {label}
      </p>
      <div style={{marginTop: 18}}>{children}</div>
    </div>
  );
}

export function RequestReplayComposition() {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const firstRequest = spring({frame, fps, config: {damping: 18, stiffness: 120}});
  const jobReveal = spring({frame: frame - 26, fps, config: {damping: 18, stiffness: 110}});
  const reconnect = spring({frame: frame - 62, fps, config: {damping: 18, stiffness: 110}});
  const confirmation = interpolate(frame, [116, 146], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const receipt = runtimeDemoReceipt;

  return (
    <AbsoluteFill style={{padding: 96, background: 'var(--ordivon-color-ink)', color: 'var(--ordivon-color-paper)', fontFamily: 'var(--ordivon-font-sans)'}}>
      <div>
        <p style={{margin: 0, color: 'var(--ordivon-color-accent)', fontFamily: 'var(--ordivon-font-mono)', fontSize: 20, letterSpacing: '0.12em', textTransform: 'uppercase'}}>
          Uncertain delivery / exact replay
        </p>
        <h1 style={{margin: '18px 0 0', fontSize: 78, fontWeight: 520, letterSpacing: '-0.055em', lineHeight: 0.96}}>
          Reconnect to the same work.
        </h1>
      </div>

      <div style={{position: 'relative', flex: 1, marginTop: 70}}>
        <ProofCard
          label="Client A / first delivery"
          style={{position: 'absolute', left: 0, top: 0, width: 560, opacity: firstRequest, transform: `translateX(${(1 - firstRequest) * -50}px)`}}
        >
          <code style={{fontFamily: 'var(--ordivon-font-mono)', fontSize: 22, color: 'var(--ordivon-color-paper-soft)'}}>
            {compactProofValue(receipt.execution.clientRequestId, 30, 12)}
          </code>
        </ProofCard>

        <ProofCard
          label="Recorded execution identity"
          style={{position: 'absolute', right: 0, top: 94, width: 660, opacity: jobReveal, transform: `scale(${0.95 + jobReveal * 0.05})`, borderColor: 'var(--ordivon-color-accent)'}}
        >
          <strong style={{display: 'block', fontSize: 34, fontWeight: 560}}>Job {compactProofValue(receipt.execution.jobId, 22, 10)}</strong>
          <code style={{display: 'block', marginTop: 16, fontFamily: 'var(--ordivon-font-mono)', fontSize: 20, color: 'var(--ordivon-color-muted)'}}>
            Attempt {compactProofValue(receipt.execution.attemptId, 22, 10)}
          </code>
        </ProofCard>

        <div style={{position: 'absolute', left: 560, top: 101, width: 420, height: 2, background: 'var(--ordivon-color-accent)', transformOrigin: 'left', transform: `scaleX(${jobReveal})`}} />

        <ProofCard
          label="Client B / reconnect"
          style={{position: 'absolute', left: 0, bottom: 30, width: 560, opacity: reconnect, transform: `translateY(${(1 - reconnect) * 40}px)`}}
        >
          <code style={{fontFamily: 'var(--ordivon-font-mono)', fontSize: 22, color: 'var(--ordivon-color-paper-soft)'}}>
            same {compactProofValue(receipt.execution.clientRequestId, 26, 12)}
          </code>
        </ProofCard>

        <div style={{position: 'absolute', left: 560, bottom: 131, width: 420, height: 2, background: 'var(--ordivon-color-accent)', transformOrigin: 'left', transform: `scaleX(${reconnect}) rotate(-13deg)`}} />

        <div style={{position: 'absolute', right: 0, bottom: 30, width: 660, padding: 24, opacity: confirmation, background: 'color-mix(in srgb, var(--ordivon-color-success) 14%, var(--ordivon-color-ink-soft))', border: '1px solid var(--ordivon-color-success)'}}>
          <strong style={{fontSize: 30, color: 'var(--ordivon-color-success)'}}>same Job · same Attempt</strong>
          <p style={{margin: '10px 0 0', color: 'var(--ordivon-color-paper-soft)', fontSize: 20}}>
            Exact replay returns the recorded Job. It does not admit a second Job.
          </p>
        </div>
      </div>
    </AbsoluteFill>
  );
}
