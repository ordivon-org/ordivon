// Minimal extraction of the mechanically validated PGP-A movement kernel.
// Source authority remains experiments/pre-g0/web/app.js at the PC03-F0 base revision.
export const PGP_A_KERNEL = Object.freeze({
  acceleration: 0.55,
  damping: 0.82,
  maxVx: 5,
  jumpVy: -9.5,
  gravity: 0.48,
  maxVy: 12,
  playerWidth: 24,
  playerHeight: 32,
});

export function applyPGPAControl(state, input) {
  const k = PGP_A_KERNEL;
  state.vx += (input.right ? k.acceleration : 0) - (input.left ? k.acceleration : 0);
  state.vx *= k.damping;
  state.vx = Math.max(-k.maxVx, Math.min(k.maxVx, state.vx));
  if (input.jump && state.ground) {
    state.vy = k.jumpVy;
    state.ground = false;
  }
  state.vy = Math.min(k.maxVy, state.vy + k.gravity);
}
