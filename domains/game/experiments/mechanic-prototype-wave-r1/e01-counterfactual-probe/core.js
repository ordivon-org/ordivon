export const FAULTS = Object.freeze({
  BLOCKAGE: 'blockage',
  DEPLETION: 'depletion',
});

export const ACTIONS = Object.freeze({
  INSPECT_THERMAL: 'inspect-thermal',
  INSPECT_PRESSURE: 'inspect-pressure',
  PURGE: 'purge',
  PRIME: 'prime',
});

const FAULT_MODEL = Object.freeze({
  [FAULTS.BLOCKAGE]: Object.freeze({
    thermal: 'high',
    pressure: 'normal',
    repair: ACTIONS.PURGE,
  }),
  [FAULTS.DEPLETION]: Object.freeze({
    thermal: 'normal',
    pressure: 'low',
    repair: ACTIONS.PRIME,
  }),
});

export function createState(fault) {
  if (!FAULT_MODEL[fault]) throw new Error(`unknown fault: ${fault}`);
  return {
    fault,
    publicSignal: 'flow-instability',
    inspectionsLeft: 1,
    inspectionCost: 0,
    observations: [],
    terminal: false,
    success: false,
    repair: null,
    consequence: 'diagnose',
    turns: 0,
  };
}

export function publicView(state) {
  return {
    publicSignal: state.publicSignal,
    inspectionsLeft: state.inspectionsLeft,
    inspectionCost: state.inspectionCost,
    observations: state.observations.map(({ channel, value }) => ({ channel, value })),
    terminal: state.terminal,
    success: state.success,
    repair: state.repair,
    consequence: state.consequence,
    turns: state.turns,
  };
}

export function step(state, action) {
  if (state.terminal) return publicView(state);
  state.turns += 1;

  if (action === ACTIONS.INSPECT_THERMAL || action === ACTIONS.INSPECT_PRESSURE) {
    if (state.inspectionsLeft <= 0) {
      state.consequence = 'inspection-unavailable';
      return publicView(state);
    }
    const channel = action === ACTIONS.INSPECT_THERMAL ? 'thermal' : 'pressure';
    state.inspectionsLeft -= 1;
    state.inspectionCost += 1;
    state.observations.push({ channel, value: FAULT_MODEL[state.fault][channel] });
    state.consequence = 'inspection-revealed';
    return publicView(state);
  }

  if (action === ACTIONS.PURGE || action === ACTIONS.PRIME) {
    state.terminal = true;
    state.repair = action;
    state.success = FAULT_MODEL[state.fault].repair === action;
    state.consequence = state.success ? 'system-stabilized' : 'wrong-repair-shutdown';
    return publicView(state);
  }

  state.consequence = 'illegal-action';
  return publicView(state);
}

export function runPolicy(fault, policy) {
  const state = createState(fault);
  const trace = [{ action: null, view: publicView(state) }];
  for (let i = 0; i < 4 && !state.terminal; i += 1) {
    const action = policy(publicView(state));
    trace.push({ action, view: step(state, action) });
  }
  return { fault, trace, final: publicView(state) };
}

export function noInspectionPurgePolicy() {
  return ACTIONS.PURGE;
}

export function noInspectionPrimePolicy() {
  return ACTIONS.PRIME;
}

export function informedThermalPolicy(view) {
  if (view.observations.length === 0) return ACTIONS.INSPECT_THERMAL;
  const thermal = view.observations.find((x) => x.channel === 'thermal')?.value;
  return thermal === 'high' ? ACTIONS.PURGE : ACTIONS.PRIME;
}

export function runWitnesses() {
  const initialBlockage = publicView(createState(FAULTS.BLOCKAGE));
  const initialDepletion = publicView(createState(FAULTS.DEPLETION));
  const purgeBlockage = runPolicy(FAULTS.BLOCKAGE, noInspectionPurgePolicy);
  const purgeDepletion = runPolicy(FAULTS.DEPLETION, noInspectionPurgePolicy);
  const primeBlockage = runPolicy(FAULTS.BLOCKAGE, noInspectionPrimePolicy);
  const primeDepletion = runPolicy(FAULTS.DEPLETION, noInspectionPrimePolicy);
  const informedBlockage = runPolicy(FAULTS.BLOCKAGE, informedThermalPolicy);
  const informedDepletion = runPolicy(FAULTS.DEPLETION, informedThermalPolicy);

  const initialViewsMatch = JSON.stringify(initialBlockage) === JSON.stringify(initialDepletion);
  const fixedRepairCannotSolveBoth =
    (purgeBlockage.final.success !== purgeDepletion.final.success) &&
    (primeBlockage.final.success !== primeDepletion.final.success);
  const inspectionSeparatesFaults =
    informedBlockage.trace[1].view.observations[0]?.value !==
    informedDepletion.trace[1].view.observations[0]?.value;
  const informedSolvesBoth = informedBlockage.final.success && informedDepletion.final.success;
  const boundedInspection =
    informedBlockage.final.inspectionCost === 1 && informedDepletion.final.inspectionCost === 1;

  return {
    schemaVersion: 1,
    kind: 'ordivon.game.mechanic-prototype-r1.e01-counterfactual-probe',
    intendedConsequence: 'one bounded inspection reveals information that changes which corrective action succeeds',
    initialViewsMatch,
    fixedRepairCannotSolveBoth,
    inspectionSeparatesFaults,
    informedSolvesBoth,
    boundedInspection,
    pass: initialViewsMatch && fixedRepairCannotSolveBoth && inspectionSeparatesFaults && informedSolvesBoth && boundedInspection,
    traces: { purgeBlockage, purgeDepletion, primeBlockage, primeDepletion, informedBlockage, informedDepletion },
    claimBoundary: 'MECHANICAL_INFORMATION_TO_ACTION_CAUSALITY_ONLY_NO_HUMAN_VALUE_CLAIM',
  };
}
