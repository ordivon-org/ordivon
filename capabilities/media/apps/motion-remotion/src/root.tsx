import {Composition} from 'remotion';
import {RuntimeFlowComposition} from './runtime-flow-composition.tsx';

export function StudioMotionRoot() {
  return (
    <Composition
      id="runtime-flow"
      component={RuntimeFlowComposition}
      durationInFrames={210}
      fps={30}
      width={1920}
      height={1080}
    />
  );
}
