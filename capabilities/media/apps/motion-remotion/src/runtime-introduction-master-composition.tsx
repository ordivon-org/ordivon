import type {CSSProperties, ReactNode} from 'react';
import {AbsoluteFill, interpolate, Sequence, useCurrentFrame} from 'remotion';
import '@ordivon/identity/tokens.css';
import {ExactCloseComposition} from './exact-close-composition.tsx';
import {RequestReplayComposition} from './request-replay-composition.tsx';
import {RuntimeFlowComposition} from './runtime-flow-composition.tsx';
import {compactProofValue, runtimeDemoReceipt} from './runtime-demo-receipt.ts';

const mono: CSSProperties = {
  fontFamily: 'var(--ordivon-font-mono)',
  letterSpacing: '0.09em',
  textTransform: 'uppercase',
};

function ramp(frame: number, start: number, end: number) {
  return interpolate(frame, [start, end], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
}

function Shell({children, label, provenance = 'receipt-derived evidence view'}: {children: ReactNode; label: string; provenance?: string}) {
  return (
    <AbsoluteFill
      style={{
        background: 'var(--ordivon-color-ink)',
        color: 'var(--ordivon-color-paper)',
        fontFamily: 'var(--ordivon-font-sans)',
        padding: '74px 92px 68px',
      }}
    >
      <header style={{display: 'flex', justifyContent: 'space-between', alignItems: 'baseline'}}>
        <p style={{...mono, margin: 0, fontSize: 15, color: 'var(--ordivon-color-accent)'}}>Ordivon Runtime / one real proof</p>
        <p style={{...mono, margin: 0, fontSize: 12, color: 'var(--ordivon-color-muted)'}}>{label}</p>
      </header>
      {children}
      <p style={{position: 'absolute', left: 92, bottom: 34, margin: 0, ...mono, fontSize: 11, color: 'var(--ordivon-color-muted)'}}>
        {provenance} · not a terminal capture
      </p>
    </AbsoluteFill>
  );
}

function BigStatement({eyebrow, children, note}: {eyebrow: string; children: ReactNode; note?: string}) {
  const frame = useCurrentFrame();
  const enter = ramp(frame, 4, 24);
  return (
    <div style={{marginTop: 142, opacity: enter, transform: `translateY(${(1 - enter) * 24}px)`}}>
      <p style={{...mono, margin: 0, fontSize: 15, color: 'var(--ordivon-color-accent-soft)'}}>{eyebrow}</p>
      <h1 style={{maxWidth: 1250, margin: '20px 0 0', fontSize: 86, lineHeight: 0.94, letterSpacing: '-0.06em', fontWeight: 520}}>{children}</h1>
      {note && <p style={{maxWidth: 880, margin: '34px 0 0', color: 'var(--ordivon-color-paper-soft)', fontSize: 24, lineHeight: 1.45}}>{note}</p>}
    </div>
  );
}

function EvidenceCard({label, value, detail, accent = false}: {label: string; value: string; detail?: string; accent?: boolean}) {
  return (
    <div style={{padding: 27, border: `1px solid ${accent ? 'var(--ordivon-color-accent)' : 'var(--ordivon-color-line-strong)'}`, background: accent ? 'color-mix(in srgb, var(--ordivon-color-accent) 8%, var(--ordivon-color-ink-soft))' : 'var(--ordivon-color-ink-soft)'}}>
      <span style={{...mono, display: 'block', fontSize: 12, color: accent ? 'var(--ordivon-color-accent-soft)' : 'var(--ordivon-color-muted)'}}>{label}</span>
      <strong style={{display: 'block', marginTop: 14, fontSize: 31, lineHeight: 1.08, fontWeight: 540, overflowWrap: 'anywhere'}}>{value}</strong>
      {detail && <p style={{margin: '12px 0 0', color: 'var(--ordivon-color-muted)', fontSize: 16, lineHeight: 1.4}}>{detail}</p>}
    </div>
  );
}

function HookScene() {
  return (
    <Shell label="problem / uncertain delivery" provenance="Studio explanatory framing">
      <BigStatement eyebrow="The failure boundary" note="Reliable Agent work cannot treat a missing response as permission to blindly dispatch the operation again.">
        The response can disappear.<br/><em style={{fontWeight: 450, color: 'var(--ordivon-color-accent-soft)'}}>The work does not have to.</em>
      </BigStatement>
    </Shell>
  );
}

function SourcePatchScene() {
  const frame = useCurrentFrame();
  const reveal = ramp(frame, 18, 62);
  const receipt = runtimeDemoReceipt;
  return (
    <Shell label="exact source / guarded mutation">
      <div style={{marginTop: 110}}>
        <p style={{...mono, margin: 0, fontSize: 15, color: 'var(--ordivon-color-accent-soft)'}}>Start from identified source. Change only the state that was read.</p>
        <h1 style={{maxWidth: 1150, margin: '18px 0 46px', fontSize: 68, lineHeight: 0.98, letterSpacing: '-0.055em', fontWeight: 520}}>A Patch is admitted against exact bytes, not remembered source.</h1>
        <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 18, opacity: reveal}}>
          <EvidenceCard label="demo source revision" value={compactProofValue(receipt.source.revision, 22, 12)} detail="fresh fixture committed before workspace.open" />
          <EvidenceCard label="changed path" value={receipt.patch.files.join(', ')} detail="one bounded source mutation" accent />
          <EvidenceCard label="patch request digest" value={compactProofValue(receipt.patch.requestDigest, 24, 12)} detail="first admission · replayed = false" />
        </div>
      </div>
    </Shell>
  );
}

function ObserveScene() {
  const frame = useCurrentFrame();
  const receipt = runtimeDemoReceipt;
  const progress = ramp(frame, 28, 110);
  const steps = ['inspect', 'verify', 'report'];
  return (
    <Shell label="durable Job / observable Attempt">
      <div style={{marginTop: 95}}>
        <p style={{...mono, margin: 0, fontSize: 15, color: 'var(--ordivon-color-accent-soft)'}}>Admitted execution identity</p>
        <h1 style={{margin: '18px 0 38px', fontSize: 66, letterSpacing: '-0.055em', lineHeight: 0.98, fontWeight: 520}}>The operation becomes a recorded Job before the caller can rely on delivery.</h1>
        <div style={{display: 'grid', gridTemplateColumns: '1.25fr 1fr', gap: 22}}>
          <EvidenceCard label="Job" value={compactProofValue(receipt.execution.jobId, 27, 14)} detail={`status ${receipt.execution.status} · exit ${receipt.execution.exitCode}`} accent />
          <EvidenceCard label="recorded Attempt" value={compactProofValue(receipt.execution.attemptId, 25, 12)} detail={`${receipt.execution.elapsedMs} ms observed execution`} />
        </div>
        <div style={{display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 18, marginTop: 28}}>
          {steps.map((step, index) => {
            const local = Math.max(0, Math.min(1, progress * 3 - index));
            return <div key={step} style={{padding: 22, borderTop: `2px solid ${local >= 0.98 ? 'var(--ordivon-color-success)' : 'var(--ordivon-color-line-strong)'}`, opacity: 0.35 + local * 0.65}}><span style={{...mono, fontSize: 12, color: 'var(--ordivon-color-muted)'}}>step {index + 1} / 3</span><strong style={{display: 'block', marginTop: 12, fontSize: 28}}>{step}</strong></div>;
          })}
        </div>
      </div>
    </Shell>
  );
}

function RecoveryScene() {
  const receipt = runtimeDemoReceipt;
  return (
    <Shell label="reconnect / recover recorded work">
      <div style={{marginTop: 122}}>
        <p style={{...mono, margin: 0, fontSize: 15, color: 'var(--ordivon-color-accent-soft)'}}>After uncertain delivery</p>
        <h1 style={{maxWidth: 1200, margin: '18px 0 48px', fontSize: 72, lineHeight: 0.96, letterSpacing: '-0.06em', fontWeight: 520}}>Replay the exact request identity.<br/>Recover the recorded Job.</h1>
        <div style={{display: 'grid', gridTemplateColumns: '1fr 160px 1fr', gap: 18, alignItems: 'center'}}>
          <EvidenceCard label="client request" value={compactProofValue(receipt.execution.clientRequestId, 26, 12)} />
          <div style={{textAlign: 'center', fontSize: 54, color: 'var(--ordivon-color-success)'}}>→</div>
          <EvidenceCard label="replay result" value="same recorded Job" detail={`sameJobAfterReplay = ${String(receipt.execution.sameJobAfterReplay)}`} accent />
        </div>
      </div>
    </Shell>
  );
}

function EvidenceScene() {
  const receipt = runtimeDemoReceipt;
  return (
    <Shell label="bounded execution evidence">
      <div style={{marginTop: 100}}>
        <p style={{...mono, margin: 0, fontSize: 15, color: 'var(--ordivon-color-accent-soft)'}}>The Job leaves inspectable evidence</p>
        <h1 style={{margin: '18px 0 42px', maxWidth: 1120, fontSize: 67, lineHeight: 0.97, letterSpacing: '-0.055em', fontWeight: 520}}>Success is a physical execution fact here—not semantic Task completion.</h1>
        <div style={{display: 'grid', gridTemplateColumns: '1.3fr .7fr .7fr', gap: 18}}>
          <EvidenceCard label="terminal evidence digest" value={compactProofValue(receipt.evidence.digest, 26, 14)} detail={compactProofValue(receipt.evidence.artifactId, 31, 15)} accent />
          <EvidenceCard label="process tree" value={receipt.evidence.processTreeDisposition} detail={receipt.evidence.reasonCode} />
          <EvidenceCard label="delivery" value={receipt.evidence.deliveryDisposition} detail={receipt.evidence.executionDisposition} />
        </div>
        <p style={{margin: '30px 0 0', maxWidth: 980, color: 'var(--ordivon-color-muted)', fontSize: 20, lineHeight: 1.5}}>The receipt binds Job, Attempt, Workspace, source revision, terminal Artifacts, execution disposition and observation time. It does not prove every external-world effect.</p>
      </div>
    </Shell>
  );
}

function DiffScene() {
  const receipt = runtimeDemoReceipt;
  return (
    <Shell label="source consequence / structured diff">
      <BigStatement eyebrow="The source effect remains inspectable" note={`changedPaths = ${receipt.diff.changedPaths.join(', ')} · truncated = ${String(receipt.diff.truncated)}`}>
        One modified path.<br/><em style={{fontWeight: 450, color: 'var(--ordivon-color-accent-soft)'}}>policy.py</em>
      </BigStatement>
    </Shell>
  );
}

function BoundaryScene() {
  return (
    <Shell label="what Runtime does not claim" provenance="Studio boundary framing · source-bound to current Runtime">
      <div style={{marginTop: 105}}>
        <p style={{...mono, margin: 0, fontSize: 15, color: 'var(--ordivon-color-signal)'}}>Boundary</p>
        <h1 style={{maxWidth: 1100, margin: '18px 0 44px', fontSize: 67, lineHeight: 0.97, letterSpacing: '-0.055em', fontWeight: 520}}>Durable execution evidence is not universal outcome truth.</h1>
        <div style={{display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 18}}>
          <EvidenceCard label="not owned" value="semantic Task completion" detail="Host/domain verification decides meaning" />
          <EvidenceCard label="not provided" value="hostile multi-tenant sandbox" detail="owner-trusted local authority boundary" />
          <EvidenceCard label="not implied" value="external-effect idempotency" detail="replay identity does not prove every outside effect" />
        </div>
      </div>
    </Shell>
  );
}

function EndScene() {
  return (
    <Shell label="current product boundary" provenance="Studio current-state framing · source-bound to current Runtime">
      <BigStatement eyebrow="Ordivon Runtime" note="Operational for owner-trusted local engineering work. Public interface remains pre-1.0.">
        Recover the same work.<br/><em style={{fontWeight: 450, color: 'var(--ordivon-color-accent-soft)'}}>Inspect the evidence.</em>
      </BigStatement>
    </Shell>
  );
}

function Unlabelled({children}: {children: ReactNode}) {
  return <AbsoluteFill>{children}</AbsoluteFill>;
}

export function RuntimeIntroductionMasterComposition() {
  return (
    <AbsoluteFill style={{background: 'var(--ordivon-color-ink)'}}>
      <Sequence from={0} durationInFrames={180}><HookScene /></Sequence>
      <Sequence from={180} durationInFrames={210}><Unlabelled><RuntimeFlowComposition /></Unlabelled></Sequence>
      <Sequence from={390} durationInFrames={330}><SourcePatchScene /></Sequence>
      <Sequence from={720} durationInFrames={390}><ObserveScene /></Sequence>
      <Sequence from={1110} durationInFrames={180}><Unlabelled><RequestReplayComposition /></Unlabelled></Sequence>
      <Sequence from={1290} durationInFrames={150}><RecoveryScene /></Sequence>
      <Sequence from={1440} durationInFrames={330}><EvidenceScene /></Sequence>
      <Sequence from={1770} durationInFrames={180}><Unlabelled><ExactCloseComposition /></Unlabelled></Sequence>
      <Sequence from={1950} durationInFrames={90}><DiffScene /></Sequence>
      <Sequence from={2040} durationInFrames={210}><BoundaryScene /></Sequence>
      <Sequence from={2250} durationInFrames={90}><EndScene /></Sequence>
    </AbsoluteFill>
  );
}
