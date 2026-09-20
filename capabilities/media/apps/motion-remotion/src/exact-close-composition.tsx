import type {CSSProperties} from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import '@ordivon/identity/tokens.css';
import {compactProofValue, runtimeDemoReceipt} from './runtime-demo-receipt.ts';

const digestCard: CSSProperties = {
  padding: 32,
  background: 'var(--ordivon-color-ink-soft)',
  border: '1px solid color-mix(in srgb, var(--ordivon-color-paper) 20%, transparent)',
};

export function ExactCloseComposition() {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const reviewed = spring({frame, fps, config: {damping: 18, stiffness: 110}});
  const request = spring({frame: frame - 46, fps, config: {damping: 18, stiffness: 110}});
  const match = spring({frame: frame - 92, fps, config: {damping: 16, stiffness: 125}});
  const removed = interpolate(frame, [130, 160], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const receipt = runtimeDemoReceipt;
  const digest = receipt.workspace.sourceStateDigest;

  return (
    <AbsoluteFill style={{padding: 96, background: 'var(--ordivon-color-ink)', color: 'var(--ordivon-color-paper)', fontFamily: 'var(--ordivon-font-sans)'}}>
      <p style={{margin: 0, color: 'var(--ordivon-color-accent)', fontFamily: 'var(--ordivon-font-mono)', fontSize: 20, letterSpacing: '0.12em', textTransform: 'uppercase'}}>
        Reviewed state / compare-and-close
      </p>
      <h1 style={{margin: '18px 0 0', fontSize: 78, fontWeight: 520, letterSpacing: '-0.055em', lineHeight: 0.96}}>
        Close only what was reviewed.
      </h1>

      <div style={{display: 'grid', gridTemplateColumns: '1fr 120px 1fr', alignItems: 'center', gap: 24, marginTop: 96}}>
        <div style={{...digestCard, opacity: reviewed, transform: `translateY(${(1 - reviewed) * 28}px)`}}>
          <p style={{margin: 0, color: 'var(--ordivon-color-muted)', fontFamily: 'var(--ordivon-font-mono)', fontSize: 17, textTransform: 'uppercase', letterSpacing: '0.1em'}}>
            workspace.get
          </p>
          <strong style={{display: 'block', marginTop: 18, fontSize: 30}}>Reviewed source state</strong>
          <code style={{display: 'block', marginTop: 20, color: 'var(--ordivon-color-accent-soft)', fontFamily: 'var(--ordivon-font-mono)', fontSize: 22}}>
            {compactProofValue(digest, 28, 14)}
          </code>
        </div>

        <div style={{fontSize: 72, textAlign: 'center', color: 'var(--ordivon-color-success)', opacity: match, transform: `scale(${0.7 + match * 0.3})`}}>=</div>

        <div style={{...digestCard, opacity: request, transform: `translateY(${(1 - request) * 28}px)`, borderColor: 'var(--ordivon-color-accent)'}}>
          <p style={{margin: 0, color: 'var(--ordivon-color-muted)', fontFamily: 'var(--ordivon-font-mono)', fontSize: 17, textTransform: 'uppercase', letterSpacing: '0.1em'}}>
            workspace.close
          </p>
          <strong style={{display: 'block', marginTop: 18, fontSize: 30}}>expectedSourceStateDigest</strong>
          <code style={{display: 'block', marginTop: 20, color: 'var(--ordivon-color-accent-soft)', fontFamily: 'var(--ordivon-font-mono)', fontSize: 22}}>
            {compactProofValue(receipt.close.sourceStateDigest, 28, 14)}
          </code>
        </div>
      </div>

      <div style={{marginTop: 54, padding: 28, display: 'flex', alignItems: 'center', justifyContent: 'space-between', opacity: removed, background: 'color-mix(in srgb, var(--ordivon-color-success) 14%, var(--ordivon-color-ink-soft))', border: '1px solid var(--ordivon-color-success)'}}>
        <div>
          <strong style={{fontSize: 34, color: 'var(--ordivon-color-success)'}}>exact state matched</strong>
          <p style={{margin: '8px 0 0', fontSize: 20, color: 'var(--ordivon-color-paper-soft)'}}>
            {compactProofValue(receipt.workspace.workspaceId, 24, 10)}
          </p>
        </div>
        <code style={{fontFamily: 'var(--ordivon-font-mono)', fontSize: 26}}>removed: true</code>
      </div>
    </AbsoluteFill>
  );
}
