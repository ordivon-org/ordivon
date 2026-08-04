import {Composition} from 'remotion';
import {ExactCloseComposition} from './exact-close-composition.tsx';
import {RequestReplayComposition} from './request-replay-composition.tsx';
import {RuntimeFlowComposition} from './runtime-flow-composition.tsx';

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
    </>
  );
}
