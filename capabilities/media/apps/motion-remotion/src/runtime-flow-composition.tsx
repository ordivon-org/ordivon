import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {RuntimeFlow, runtimeStages} from '@ordivon/visuals';
import '@ordivon/identity/tokens.css';

export function RuntimeFlowComposition() {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const stageIndex = Math.min(runtimeStages.length - 1, Math.floor(frame / 30));
  const localFrame = frame - stageIndex * 30;
  const progress = spring({frame: localFrame, fps, config: {damping: 18, stiffness: 120}});
  const titleOpacity = interpolate(frame, [0, 18], [0, 1], {extrapolateRight: 'clamp'});

  return (
    <AbsoluteFill
      style={{
        padding: 96,
        background: 'var(--ordivon-color-ink)',
        color: 'var(--ordivon-color-paper)',
        fontFamily: 'var(--ordivon-font-sans)',
      }}
    >
      <div style={{opacity: titleOpacity}}>
        <p style={{margin: 0, color: 'var(--ordivon-color-accent)', fontFamily: 'var(--ordivon-font-mono)', fontSize: 20, letterSpacing: '0.12em', textTransform: 'uppercase'}}>
          Ordivon Runtime
        </p>
        <h1 style={{margin: '18px 0 52px', fontSize: 78, fontWeight: 520, letterSpacing: '-0.055em', lineHeight: 0.96}}>
          Durable execution,<br />visible as a system.
        </h1>
      </div>
      <RuntimeFlow activeStage={runtimeStages[stageIndex]?.id ?? 'recovery'} progress={progress} />
      <p style={{margin: '28px 0 0 auto', color: 'var(--ordivon-color-muted)', fontFamily: 'var(--ordivon-font-mono)', fontSize: 16}}>
        Workspace → Job → Attempt → Evidence → Recovery
      </p>
    </AbsoluteFill>
  );
}
