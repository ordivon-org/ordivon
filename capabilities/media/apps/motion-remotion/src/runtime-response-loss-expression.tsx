import type {CSSProperties} from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import '@ordivon/identity/tokens.css';
import {compactProofValue, runtimeDemoReceipt} from './runtime-demo-receipt.ts';

const mono: CSSProperties = {fontFamily: 'var(--ordivon-font-mono)', letterSpacing: '0.08em', textTransform: 'uppercase'};

function clamp(frame: number, input: [number, number], output: [number, number]) {
  return interpolate(frame, input, output, {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
}

export function RuntimeResponseLossExpression() {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const receipt = runtimeDemoReceipt;

  const requestIn = spring({frame, fps, config: {damping: 18, stiffness: 120}});
  const jobIn = spring({frame: frame - 28, fps, config: {damping: 18, stiffness: 115}});
  const returnGrow = clamp(frame, [58, 88], [0, 1]);
  const rupture = clamp(frame, [88, 104], [0, 1]);
  const hold = clamp(frame, [106, 126], [0, 1]);
  const reconnectIn = spring({frame: frame - 132, fps, config: {damping: 18, stiffness: 115}});
  const resolve = clamp(frame, [178, 208], [0, 1]);

  const jobId = compactProofValue(receipt.execution.jobId, 20, 10);
  const attemptId = compactProofValue(receipt.execution.attemptId, 18, 8);
  const requestId = compactProofValue(receipt.execution.clientRequestId, 24, 9);

  return (
    <AbsoluteFill style={{background: 'var(--ordivon-color-ink)', color: 'var(--ordivon-color-paper)', fontFamily: 'var(--ordivon-font-sans)', padding: '78px 92px 76px'}}>
      <header style={{display: 'flex', justifyContent: 'space-between', alignItems: 'baseline'}}>
        <p style={{...mono, margin: 0, fontSize: 18, color: 'var(--ordivon-color-accent)'}}>A3-1 · uncertain delivery</p>
        <p style={{...mono, margin: 0, fontSize: 14, color: 'var(--ordivon-color-muted)'}}>receipt-bound / no fabricated terminal</p>
      </header>

      <div style={{position: 'relative', flex: 1, marginTop: 38, overflow: 'hidden'}}>
        <div style={{position: 'absolute', left: 0, top: 88, width: 410, opacity: requestIn, transform: `translateX(${(1-requestIn)*-70}px)`}}>
          <p style={{...mono, margin: 0, fontSize: 15, color: 'var(--ordivon-color-muted)'}}>Client A</p>
          <h1 style={{margin: '12px 0 16px', maxWidth: 360, fontSize: 60, lineHeight: .94, letterSpacing: '-0.055em', fontWeight: 520}}>The request leaves.</h1>
          <code style={{fontFamily: 'var(--ordivon-font-mono)', fontSize: 17, color: 'var(--ordivon-color-paper-soft)'}}>{requestId}</code>
        </div>

        <div style={{position: 'absolute', left: 385, top: 258, width: 385, height: 2, background: 'var(--ordivon-color-accent)', transformOrigin: 'left', transform: `scaleX(${requestIn})`}} />

        <div style={{position: 'absolute', left: 760, top: 146, width: 500, minHeight: 250, padding: 30, border: '1px solid var(--ordivon-color-accent)', background: 'color-mix(in srgb, var(--ordivon-color-accent) 11%, var(--ordivon-color-ink-soft))', opacity: jobIn, transform: `scale(${.94 + jobIn*.06})`}}>
          <p style={{...mono, margin: 0, fontSize: 15, color: 'var(--ordivon-color-accent-soft)'}}>Recorded execution identity</p>
          <strong style={{display: 'block', marginTop: 35, fontSize: 42, fontWeight: 560}}>Job {jobId}</strong>
          <code style={{display: 'block', marginTop: 18, fontFamily: 'var(--ordivon-font-mono)', fontSize: 20, color: 'var(--ordivon-color-muted)'}}>Attempt {attemptId}</code>
          <p style={{margin: '30px 0 0', fontSize: 19, color: 'var(--ordivon-color-paper-soft)'}}>Durable state is already here.</p>
        </div>

        <div style={{position: 'absolute', left: 1260, top: 258, width: 380, height: 2, overflow: 'visible'}}>
          <div style={{width: '100%', height: 2, background: 'var(--ordivon-color-paper-soft)', transformOrigin: 'left', transform: `scaleX(${returnGrow})`, opacity: .5}} />
          <div style={{position: 'absolute', left: 205, top: -26, width: 76, height: 56, opacity: rupture}}>
            <span style={{position: 'absolute', left: 0, top: 27, width: 30, height: 2, background: 'var(--ordivon-color-signal)', transform: 'rotate(-24deg)'}} />
            <span style={{position: 'absolute', left: 23, top: 27, width: 30, height: 2, background: 'var(--ordivon-color-signal)', transform: 'rotate(28deg)'}} />
            <span style={{position: 'absolute', left: 47, top: 27, width: 30, height: 2, background: 'var(--ordivon-color-signal)', transform: 'rotate(-24deg)'}} />
          </div>
        </div>

        <div style={{position: 'absolute', right: 0, top: 95, width: 310, opacity: rupture}}>
          <p style={{...mono, margin: 0, fontSize: 15, color: 'var(--ordivon-color-signal)'}}>Response lost</p>
          <p style={{margin: '12px 0 0', fontSize: 27, lineHeight: 1.06, letterSpacing: '-.035em'}}>Delivery becomes uncertain.</p>
        </div>

        <div style={{position: 'absolute', left: 748, top: 440, width: 525, textAlign: 'center', opacity: hold}}>
          <p style={{margin: 0, fontFamily: 'var(--ordivon-font-serif)', fontSize: 38, lineHeight: 1.12, color: 'var(--ordivon-color-paper)'}}>The response disappeared.</p>
          <p style={{margin: '8px 0 0', fontSize: 24, color: 'var(--ordivon-color-accent-soft)'}}>The work did not.</p>
        </div>

        <div style={{position: 'absolute', right: 0, bottom: 40, width: 410, opacity: reconnectIn, transform: `translateX(${(1-reconnectIn)*70}px)`, textAlign: 'right'}}>
          <p style={{...mono, margin: 0, fontSize: 15, color: 'var(--ordivon-color-muted)'}}>Client B</p>
          <h2 style={{margin: '12px 0 14px', fontSize: 48, lineHeight: .96, letterSpacing: '-.05em', fontWeight: 520}}>Reconnect.</h2>
          <code style={{fontFamily: 'var(--ordivon-font-mono)', fontSize: 17, color: 'var(--ordivon-color-paper-soft)'}}>same {requestId}</code>
        </div>

        <div style={{position: 'absolute', left: 1260, bottom: 146, width: 305, height: 2, background: 'var(--ordivon-color-success)', transformOrigin: 'right', transform: `scaleX(${reconnectIn})`}} />

        <div style={{position: 'absolute', left: 760, bottom: 24, width: 500, padding: '22px 28px', borderTop: '1px solid var(--ordivon-color-success)', opacity: resolve, background: 'linear-gradient(180deg, color-mix(in srgb, var(--ordivon-color-success) 10%, transparent), transparent)'}}>
          <strong style={{display: 'block', fontSize: 30, color: 'var(--ordivon-color-success)'}}>same Job · same Attempt</strong>
          <p style={{margin: '8px 0 0', fontSize: 18, color: 'var(--ordivon-color-paper-soft)'}}>Communication continuity failed. Execution identity remained recoverable.</p>
        </div>
      </div>
    </AbsoluteFill>
  );
}
