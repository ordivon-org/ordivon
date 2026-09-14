import { PGP_A_KERNEL, applyPGPAControl } from '../../pre-g0/web/pgp-a-kernel.js';

export const W = 980;
export const H = 500;
export const FLOOR_Y = 420;
export const RULE_ID = 'late-edge-jump-v1';
const PW = PGP_A_KERNEL.playerWidth;
const PH = PGP_A_KERNEL.playerHeight;

export const WORLD = Object.freeze({
  width: W,
  height: H,
  floorY: FLOOR_Y,
  controlLaw: PGP_A_KERNEL,
  rule: Object.freeze({
    id: RULE_ID,
    semantics: 'ordinary grounded jump started near the departure edge preserves enough existing horizontal motion to clear a long gap',
    authoritativeKnowledgeState: false,
  }),
  platforms: Object.freeze([
    Object.freeze({id:'floor',x:0,y:FLOOR_Y,w:W,h:80,kind:'safe'}),
    Object.freeze({id:'fast-entry',x:175,y:335,w:150,h:24,kind:'fast'}),
    Object.freeze({id:'fast-mid',x:410,y:335,w:150,h:24,kind:'fast'}),
    Object.freeze({id:'fast-turn',x:645,y:335,w:150,h:24,kind:'fast'}),
  ]),
  hazards: Object.freeze([
    Object.freeze({id:'gap-a',x:330,y:365,w:75,h:20}),
    Object.freeze({id:'gap-b',x:565,y:365,w:75,h:20}),
  ]),
  ruleWindows: Object.freeze([
    Object.freeze({id:'edge-a-out',platform:'fast-entry',direction:'right',x0:298,x1:323}),
    Object.freeze({id:'edge-b-out',platform:'fast-mid',direction:'right',x0:533,x1:558}),
    Object.freeze({id:'edge-b-back',platform:'fast-turn',direction:'left',x0:645,x1:662}),
    Object.freeze({id:'edge-a-back',platform:'fast-mid',direction:'left',x0:410,x1:434}),
  ]),
  fastTurnX: 735,
  safeTurnX: 945,
  hubReturnX: 52,
});

export const WORLD_INVARIANT = JSON.stringify(WORLD);

function hit(ax, ay, aw, ah, b) {
  return ax < b.x + b.w && ax + aw > b.x && ay < b.y + b.h && ay + ah > b.y;
}

export function freshState() {
  return {
    x: 38,
    y: FLOOR_Y - PH,
    vx: 0,
    vy: 0,
    ground: true,
    groundY: FLOOR_Y,
    phase: 'outbound',
    route: 'undecided',
    turnKind: null,
    attempt: 1,
    completedLoops: 0,
    frame: 0,
    events: [],
    failures: 0,
    ruleUses: 0,
    complete: false,
  };
}

function record(s, kind, data = {}) {
  s.events.push({frame:s.frame, kind, ...data});
  if (s.events.length > 120) s.events.shift();
}

function platformUnder(s) {
  if (!s.ground) return null;
  return WORLD.platforms.find(p => Math.abs(s.groundY - p.y) < 0.01 && s.x + PW > p.x && s.x < p.x + p.w) ?? null;
}

function inRuleWindow(s, direction) {
  const p = platformUnder(s);
  if (!p || p.kind !== 'fast') return null;
  const cx = s.x + PW / 2;
  return WORLD.ruleWindows.find(w => w.platform === p.id && w.direction === direction && cx >= w.x0 && cx <= w.x1) ?? null;
}

function resetMiss(s, reason) {
  const attempt = s.attempt + 1;
  const failures = s.failures + 1;
  const events = s.events;
  Object.assign(s, freshState(), {attempt, failures, events});
  record(s, 'retry', {reason, attempt});
}

export function physicsStep(s, input) {
  if (s.complete) return;
  s.frame += 1;
  const direction = s.phase === 'outbound' ? 'right' : 'left';
  const ruleWindow = input.jump && s.ground ? inRuleWindow(s, direction) : null;
  applyPGPAControl(s, input);
  if (ruleWindow) {
    s.ruleUses += 1;
    record(s, 'rule-use', {window:ruleWindow.id, direction, x:Number(s.x.toFixed(1))});
  }

  const prevY = s.y;
  s.x += s.vx;
  s.y += s.vy;
  s.x = Math.max(0, Math.min(W - PW, s.x));
  s.ground = false;
  s.groundY = null;
  for (const p of WORLD.platforms) {
    if (hit(s.x, s.y, PW, PH, p) && prevY + PH <= p.y + 5 && s.vy >= 0) {
      s.y = p.y - PH;
      s.vy = 0;
      s.ground = true;
      s.groundY = p.y;
      break;
    }
  }

  for (const h of WORLD.hazards) {
    if (hit(s.x, s.y, PW, PH, h)) {
      record(s, 'demanding-fail', {hazard:h.id});
      resetMiss(s, h.id);
      return;
    }
  }
  if (s.y > H + 40) {
    resetMiss(s, 'fall');
    return;
  }

  const onFast = s.ground && s.groundY < FLOOR_Y;
  if (s.route === 'undecided' && s.phase === 'outbound') {
    if (onFast && s.x >= 205) {
      s.route = 'fast';
      record(s, 'route-choice', {route:'fast'});
    } else if (s.ground && s.groundY === FLOOR_Y && s.x >= 275) {
      s.route = 'safe';
      record(s, 'route-choice', {route:'safe'});
    }
  }

  if (s.phase === 'outbound') {
    if (s.route === 'fast' && onFast && s.x >= WORLD.fastTurnX) {
      s.phase = 'return';
      s.turnKind = 'fast';
      record(s, 'turn', {turnKind:'fast', x:Number(s.x.toFixed(1))});
    } else if (s.route !== 'fast' && s.ground && s.groundY === FLOOR_Y && s.x >= WORLD.safeTurnX) {
      s.phase = 'return';
      s.turnKind = 'safe';
      if (s.route === 'undecided') s.route = 'safe';
      record(s, 'turn', {turnKind:'safe', x:Number(s.x.toFixed(1))});
    }
  } else if (s.x <= WORLD.hubReturnX && s.ground) {
    s.complete = true;
    s.completedLoops += 1;
    record(s, 'loop-complete', {route:s.route, turnKind:s.turnKind});
  }
}

function baseDirectionalInput(s) {
  return {left:s.phase === 'return', right:s.phase === 'outbound', jump:false};
}

export function policyInput(name, s, memory) {
  const input = baseDirectionalInput(s);
  if (name === 'uninformed-safe') return input;

  if (s.phase === 'outbound' && s.ground && s.groundY === FLOOR_Y && s.x >= 142 && s.x <= 176 && !memory.enteredFast) {
    input.jump = true;
    memory.enteredFast = true;
    return input;
  }

  if (name === 'informed-insensitive') {
    const p = platformUnder(s);
    if (s.phase === 'outbound' && p?.id === 'fast-entry' && s.x >= 225 && !memory.earlyA) {
      input.jump = true; memory.earlyA = true; return input;
    }
    if (s.phase === 'outbound' && p?.id === 'fast-mid' && s.x >= 455 && !memory.earlyB) {
      input.jump = true; memory.earlyB = true; return input;
    }
    return input;
  }

  if (name === 'informed-aware') {
    const direction = s.phase === 'outbound' ? 'right' : 'left';
    if (inRuleWindow(s, direction)) input.jump = true;
    return input;
  }
  return input;
}

export function simulatePolicy(name, maxFrames = 2200) {
  const s = freshState();
  const memory = {};
  let executedFrames = 0;
  for (let i = 0; i < maxFrames; i += 1) {
    physicsStep(s, policyInput(name, s, memory));
    executedFrames = i + 1;
    if (s.complete) break;
    if (name === 'informed-insensitive' && s.failures > 0) break;
  }
  return {
    policy:name,
    complete:s.complete,
    frames:executedFrames,
    route:s.route,
    turnKind:s.turnKind,
    failures:s.failures,
    ruleUses:s.ruleUses,
    attempt:s.attempt,
    routeEvents:s.events.filter(e=>e.kind==='route-choice').map(e=>e.route),
    turns:s.events.filter(e=>e.kind==='turn').map(e=>e.turnKind),
    events:s.events.slice(),
    worldInvariant:WORLD_INVARIANT,
  };
}

export function runWitnesses() {
  const uninformed = simulatePolicy('uninformed-safe');
  const insensitive = simulatePolicy('informed-insensitive');
  const aware = simulatePolicy('informed-aware');
  return {
    schemaVersion:2,
    kind:'ordivon.game.pc03-f0-interactive-witness',
    stableRule:{id:RULE_ID, authoritativeKnowledgeState:false, instances:['gap-a-out/back','gap-b-out/back']},
    uninformed,
    insensitive,
    aware,
    worldInvariant:WORLD_INVARIANT,
    mechanismLibraryModified:false,
    runtimeAgentProfile:'none',
    claimBoundary:'MECHANICS_ONLY_HUMAN_CLAIMS_UNOBSERVED_PRODUCT_SELECTION_FALSE_G0_FALSE',
  };
}
