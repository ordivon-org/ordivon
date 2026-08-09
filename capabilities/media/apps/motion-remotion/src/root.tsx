import {Composition} from 'remotion';
import {ExactCloseComposition} from './exact-close-composition.tsx';
import {RequestReplayComposition} from './request-replay-composition.tsx';
import {RuntimeFlowComposition} from './runtime-flow-composition.tsx';
import {RuntimeResponseLossExpression} from './runtime-response-loss-expression.tsx';
import {SecurityAe0EpistemicExpression} from './security-ae0-epistemic-expression.tsx';

export function StudioMotionRoot() {
  return (
    <>
      <Composition
        id="runtime-flow"
        component={RuntimeFlowComposition}
        durationInFrames={210}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="runtime-request-replay"
        component={RequestReplayComposition}
        durationInFrames={180}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="runtime-exact-close"
        component={ExactCloseComposition}
        durationInFrames={180}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="a31-runtime-response-loss"
        component={RuntimeResponseLossExpression}
        durationInFrames={225}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="a32-security-ae0-epistemics"
        component={SecurityAe0EpistemicExpression}
        durationInFrames={270}
        fps={30}
        width={1920}
        height={1080}
      />
    </>
  );
}
