export const LANES = Object.freeze([0, 1, 2]);
export const SCENARIO = Object.freeze({ startLane: 0, startDirection: 1, horizon: 4, missRecoveryCost: 2 });

export function advanceTarget(target) {
  let nextLane = target.lane + target.direction;
  let nextDirection = target.direction;
  if (nextLane > 2 || nextLane < 0) {
    nextDirection *= -1;
    nextLane = target.lane + nextDirection;
  }
  return { lane: nextLane, direction: nextDirection };
}

export function forecastTarget(target, steps) {
  let out = { ...target };
  for (let i = 0; i < steps; i += 1) out = advanceTarget(out);
  return out;
}

export function initialTarget() {
  return { lane: SCENARIO.startLane, direction: SCENARIO.startDirection };
}

export function simulateSequence(actions, lag) {
  let target = initialTarget();
  let recoveryCost = 0;
  const trace = [];
  for (let tick = 0; tick < SCENARIO.horizon; tick += 1) {
    const observation = { ...target };
    const executionTarget = forecastTarget(observation, lag);
    const action = actions[tick];
    const hit = action === executionTarget.lane;
    if (!hit) recoveryCost += SCENARIO.missRecoveryCost;
    trace.push({
      tick,
      observedLane: observation.lane,
      observedDirection: observation.direction,
      committedLane: action,
      executionLane: executionTarget.lane,
      lag,
      hit,
      consequence: hit ? 'intercepted' : 'stale-command-miss',
      recoveryCost,
    });
    target = advanceTarget(target);
  }
  return { lag, actions: actions.slice(), trace, recoveryCost, misses: trace.filter((x) => !x.hit).length };
}

export function reactiveActions() {
  let target = initialTarget();
  const actions = [];
  for (let tick = 0; tick < SCENARIO.horizon; tick += 1) {
    actions.push(target.lane);
    target = advanceTarget(target);
  }
  return actions;
}

export function anticipatoryActions(lag) {
  let target = initialTarget();
  const actions = [];
  for (let tick = 0; tick < SCENARIO.horizon; tick += 1) {
    actions.push(forecastTarget(target, lag).lane);
    target = advanceTarget(target);
  }
  return actions;
}

function enumerateSequences(length, prefix = []) {
  if (prefix.length === length) return [prefix];
  const out = [];
  for (const lane of LANES) out.push(...enumerateSequences(length, [...prefix, lane]));
  return out;
}

export function exhaustiveOptimal(lag) {
  const all = enumerateSequences(SCENARIO.horizon);
  let minCost = Infinity;
  const winners = [];
  for (const actions of all) {
    const result = simulateSequence(actions, lag);
    if (result.recoveryCost < minCost) {
      minCost = result.recoveryCost;
      winners.length = 0;
      winners.push(actions);
    } else if (result.recoveryCost === minCost) {
      winners.push(actions);
    }
  }
  return { lag, minCost, winners };
}

export function createInteractiveState(lag = 1) {
  return { lag, target: initialTarget(), tick: 0, recoveryCost: 0, misses: 0, terminal: false, last: null };
}

export function interactiveStep(state, committedLane) {
  if (state.terminal) return state;
  const observation = { ...state.target };
  const executionTarget = forecastTarget(observation, state.lag);
  const hit = committedLane === executionTarget.lane;
  if (!hit) {
    state.recoveryCost += SCENARIO.missRecoveryCost;
    state.misses += 1;
  }
  state.last = { observedLane: observation.lane, observedDirection: observation.direction, committedLane, executionLane: executionTarget.lane, hit };
  state.target = advanceTarget(state.target);
  state.tick += 1;
  state.terminal = state.tick >= SCENARIO.horizon;
  return state;
}

export function runWitnesses() {
  const reactive = reactiveActions();
  const zeroReactive = simulateSequence(reactive, 0);
  const lagReactive = simulateSequence(reactive, 1);
  const lagAnticipatory = simulateSequence(anticipatoryActions(1), 1);
  const zeroOptimal = exhaustiveOptimal(0);
  const lagOptimal = exhaustiveOptimal(1);
  const optimalTraceChangesWithLag = JSON.stringify(zeroOptimal.winners) !== JSON.stringify(lagOptimal.winners);
  const staleViewCreatesCost = lagReactive.recoveryCost > zeroReactive.recoveryCost;
  const anticipationRepairsCost = lagAnticipatory.recoveryCost < lagReactive.recoveryCost && lagAnticipatory.recoveryCost === lagOptimal.minCost;

  return {
    schemaVersion: 1,
    kind: 'ordivon.game.mechanic-prototype-r1.e03-commitment-lag',
    intendedConsequence: 'protocol-fixed action lag makes current observations stale enough that anticipatory commitment changes consequences and recovery cost',
    zeroReactive,
    lagReactive,
    lagAnticipatory,
    zeroOptimal,
    lagOptimal,
    optimalTraceChangesWithLag,
    staleViewCreatesCost,
    anticipationRepairsCost,
    pass: optimalTraceChangesWithLag && staleViewCreatesCost && anticipationRepairsCost,
    gameCoreChanged: false,
    claimBoundary: 'MECHANICAL_STALENESS_AND_ANTICIPATION_ONLY_NO_HUMAN_VALUE_CLAIM',
  };
}
