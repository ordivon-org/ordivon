export const ACTIONS = Object.freeze({ ADVANCE: 'advance', WAIT: 'wait', JUMP: 'jump' });

export const ROUTES = Object.freeze({
  route1: Object.freeze({ id: 'route1', length: 5, launchPosition: 3, initialPhase: 1, safePhase: 1 }),
  route2: Object.freeze({ id: 'route2', length: 7, launchPosition: 5, initialPhase: 1, safePhase: 1 }),
});

export function createRouteState(routeId) {
  const route = ROUTES[routeId];
  if (!route) throw new Error(`unknown route: ${routeId}`);
  return {
    routeId,
    position: 0,
    phase: route.initialPhase,
    turns: 0,
    terminal: false,
    success: false,
    consequence: 'approach',
    attempts: 0,
  };
}

export function publicView(state) {
  const route = ROUTES[state.routeId];
  return {
    routeId: state.routeId,
    position: state.position,
    launchMarker: state.position === route.launchPosition,
    pulse: state.phase === route.safePhase ? 'green' : 'red',
    turns: state.turns,
    terminal: state.terminal,
    success: state.success,
    consequence: state.consequence,
  };
}

function tick(state) {
  state.phase = (state.phase + 1) % 3;
  state.turns += 1;
}

export function step(state, action) {
  if (state.terminal) return publicView(state);
  const route = ROUTES[state.routeId];

  if (action === ACTIONS.ADVANCE) {
    state.position = Math.min(route.launchPosition, state.position + 1);
    state.consequence = state.position === route.launchPosition ? 'at-launch-marker' : 'approach';
    tick(state);
    return publicView(state);
  }

  if (action === ACTIONS.WAIT) {
    state.consequence = 'timing-adjusted';
    tick(state);
    return publicView(state);
  }

  if (action === ACTIONS.JUMP) {
    state.attempts += 1;
    state.terminal = true;
    const relationSatisfied = state.position === route.launchPosition && state.phase === route.safePhase;
    state.success = relationSatisfied;
    state.consequence = relationSatisfied ? 'gap-cleared' : 'miss-and-reset';
    return publicView(state);
  }

  state.consequence = 'illegal-action';
  tick(state);
  return publicView(state);
}

export function relationalPolicy(view) {
  if (!view.launchMarker) return ACTIONS.ADVANCE;
  if (view.pulse !== 'green') return ACTIONS.WAIT;
  return ACTIONS.JUMP;
}

export function timingInsensitivePolicy(view) {
  if (!view.launchMarker) return ACTIONS.ADVANCE;
  return ACTIONS.JUMP;
}

export function memorizedRoute1Schedule(view) {
  if (view.turns < 3) return ACTIONS.ADVANCE;
  return ACTIONS.JUMP;
}

export function runPolicy(routeId, policy, maxTurns = 20) {
  const state = createRouteState(routeId);
  const trace = [{ action: null, view: publicView(state) }];
  for (let i = 0; i < maxTurns && !state.terminal; i += 1) {
    const action = policy(publicView(state));
    trace.push({ action, view: step(state, action) });
  }
  return { routeId, final: publicView(state), trace };
}

export function runWitnesses() {
  const relationR1 = runPolicy('route1', relationalPolicy);
  const relationR2 = runPolicy('route2', relationalPolicy);
  const insensitiveR2 = runPolicy('route2', timingInsensitivePolicy);
  const memorizedR1 = runPolicy('route1', memorizedRoute1Schedule);
  const memorizedR2 = runPolicy('route2', memorizedRoute1Schedule);

  const transferSucceeds = relationR1.final.success && relationR2.final.success;
  const timingMattersOnRoute2 = !insensitiveR2.final.success;
  const absoluteScheduleDoesNotTransfer = memorizedR1.final.success !== memorizedR2.final.success || !memorizedR2.final.success;
  const sameRuleAcrossRoutes = ROUTES.route1.safePhase === ROUTES.route2.safePhase;
  const spatiallyDistinct = ROUTES.route1.launchPosition !== ROUTES.route2.launchPosition && ROUTES.route1.length !== ROUTES.route2.length;

  return {
    schemaVersion: 1,
    kind: 'ordivon.game.mechanic-prototype-r1.e02-transfer-route',
    intendedConsequence: 'a learned relation between local launch position and timing pulse transfers to a spatially distinct route while fixed timing does not',
    transferSucceeds,
    timingMattersOnRoute2,
    absoluteScheduleDoesNotTransfer,
    sameRuleAcrossRoutes,
    spatiallyDistinct,
    noKnowledgeAuthorizationState: true,
    pass: transferSucceeds && timingMattersOnRoute2 && absoluteScheduleDoesNotTransfer && sameRuleAcrossRoutes && spatiallyDistinct,
    traces: { relationR1, relationR2, insensitiveR2, memorizedR1, memorizedR2 },
    claimBoundary: 'MECHANICAL_RULE_TRANSFER_ONLY_NO_HUMAN_LEARNING_OR_MASTERY_CLAIM',
  };
}
