export const SCENARIOS = Object.freeze({
  'route-shift': Object.freeze({
    id: 'route-shift',
    sourceCycleIndex: 0,
    executionCycleIndex: 1,
    previousArchitecture: 'route',
    lagSteps: 1,
  }),
  'source-rule': Object.freeze({
    id: 'source-rule',
    sourceCycleIndex: 1,
    executionCycleIndex: 2,
    previousArchitecture: '',
    lagSteps: 1,
  }),
});

function scenarioFor(id) {
  const scenario = SCENARIOS[id];
  if (!scenario) throw new Error(`unknown PC01+E03 scenario: ${id}`);
  return scenario;
}

function architectures(design) {
  return [...design.architectureModes];
}

function diagnostics(design, allowDiagnostics) {
  return allowDiagnostics ? [...design.diagnostics] : ['none'];
}

function observation(diagnostic, cause) {
  if (diagnostic === 'none') return 'NONE';
  return diagnostic === cause ? 'FAULT' : 'OK';
}

function priorEntries(cycle) {
  return Object.entries(cycle.causePrior).map(([cause, raw]) => [cause, Number(raw)]);
}

function switchCost(design, previousArchitecture, nextArchitecture) {
  return previousArchitecture && previousArchitecture !== nextArchitecture ? Number(design.switchCost) : 0;
}

function rewardCycleFor(design, scenario, rewardContext) {
  if (rewardContext === 'source') return design.cycles[scenario.sourceCycleIndex];
  if (rewardContext === 'execution') return design.cycles[scenario.executionCycleIndex];
  throw new Error(`unknown rewardContext: ${rewardContext}`);
}

function branchValue(design, scenario, rewardCycle, members, architecture, causePersistence) {
  const previous = scenario.previousArchitecture;
  const switching = switchCost(design, previous, architecture);
  if (causePersistence) {
    const pObs = members.reduce((sum, [, p]) => sum + p, 0);
    return members.reduce(
      (sum, [cause, p]) =>
        sum + (p / pObs) * Number(rewardCycle.rewardByCauseAndArchitecture[cause][architecture]),
      0,
    ) - switching;
  }

  const sourceCycle = design.cycles[scenario.sourceCycleIndex];
  return priorEntries(sourceCycle).reduce(
    (sum, [executionCause, p]) =>
      sum + p * Number(rewardCycle.rewardByCauseAndArchitecture[executionCause][architecture]),
    0,
  ) - switching;
}

export function evaluatePolicy(
  design,
  scenarioId,
  policy,
  { rewardContext = 'execution', causePersistence = true } = {},
) {
  const scenario = scenarioFor(scenarioId);
  const sourceCycle = design.cycles[scenario.sourceCycleIndex];
  const rewardCycle = rewardCycleFor(design, scenario, rewardContext);
  const diagnosticCost = policy.diagnostic === 'none' ? 0 : Number(design.diagnosticCost);
  let expected = -diagnosticCost;

  if (causePersistence) {
    for (const [sourceCause, pSource] of priorEntries(sourceCycle)) {
      const obs = observation(policy.diagnostic, sourceCause);
      const architecture = policy.architectureByObservation[obs];
      if (!architecture) throw new Error(`policy missing architecture for observation ${obs}`);
      expected +=
        pSource *
        (Number(rewardCycle.rewardByCauseAndArchitecture[sourceCause][architecture]) -
          switchCost(design, scenario.previousArchitecture, architecture));
    }
    return expected;
  }

  const executionPrior = priorEntries(sourceCycle);
  for (const [sourceCause, pSource] of priorEntries(sourceCycle)) {
    const obs = observation(policy.diagnostic, sourceCause);
    const architecture = policy.architectureByObservation[obs];
    if (!architecture) throw new Error(`policy missing architecture for observation ${obs}`);
    for (const [executionCause, pExecution] of executionPrior) {
      expected +=
        pSource *
        pExecution *
        (Number(rewardCycle.rewardByCauseAndArchitecture[executionCause][architecture]) -
          switchCost(design, scenario.previousArchitecture, architecture));
    }
  }
  return expected;
}

export function solvePolicy(
  design,
  scenarioId,
  {
    rewardContext = 'execution',
    causePersistence = true,
    allowDiagnostics = true,
  } = {},
) {
  const scenario = scenarioFor(scenarioId);
  const sourceCycle = design.cycles[scenario.sourceCycleIndex];
  const rewardCycle = rewardCycleFor(design, scenario, rewardContext);
  let best = null;

  for (const diagnostic of diagnostics(design, allowDiagnostics)) {
    const groups = new Map();
    for (const [cause, prior] of priorEntries(sourceCycle)) {
      const obs = observation(diagnostic, cause);
      const members = groups.get(obs) ?? [];
      members.push([cause, prior]);
      groups.set(obs, members);
    }

    const architectureByObservation = {};
    for (const [obs, members] of groups) {
      let bestBranch = null;
      for (const architecture of architectures(design)) {
        const value = branchValue(
          design,
          scenario,
          rewardCycle,
          members,
          architecture,
          causePersistence,
        );
        if (bestBranch === null || value > bestBranch.value) {
          bestBranch = { architecture, value };
        }
      }
      if (bestBranch === null) throw new Error('policy branch has no architecture');
      architectureByObservation[obs] = bestBranch.architecture;
    }

    const policy = { diagnostic, architectureByObservation };
    const expectedValue = evaluatePolicy(design, scenarioId, policy, {
      rewardContext,
      causePersistence,
    });
    if (best === null || expectedValue > best.expectedValue) {
      best = { policy, expectedValue };
    }
  }

  if (best === null) throw new Error('policy search produced no candidate');
  return best;
}

function sampleCause(cycle, random = Math.random) {
  const roll = random();
  let cumulative = 0;
  for (const [cause, prior] of priorEntries(cycle)) {
    cumulative += prior;
    if (roll <= cumulative) return cause;
  }
  return priorEntries(cycle).at(-1)[0];
}

function validateCause(design, cause) {
  if (!architectures(design).includes(cause)) throw new Error(`unknown cause: ${cause}`);
}

export function createPlayableState(
  design,
  scenarioId,
  {
    causePersistence = true,
    forecastVisible = true,
    sourceCause = null,
    executionCause = null,
    random = Math.random,
  } = {},
) {
  const scenario = scenarioFor(scenarioId);
  const sourceCycle = design.cycles[scenario.sourceCycleIndex];
  const resolvedSourceCause = sourceCause ?? sampleCause(sourceCycle, random);
  validateCause(design, resolvedSourceCause);

  let resolvedExecutionCause;
  if (causePersistence) {
    if (executionCause !== null && executionCause !== resolvedSourceCause) {
      throw new Error('executionCause cannot differ when causePersistence=true');
    }
    resolvedExecutionCause = resolvedSourceCause;
  } else {
    resolvedExecutionCause = executionCause ?? sampleCause(sourceCycle, random);
    validateCause(design, resolvedExecutionCause);
  }

  return {
    design,
    scenario,
    phase: 'decision',
    causePersistence,
    forecastVisible,
    sourceCause: resolvedSourceCause,
    executionCause: resolvedExecutionCause,
    inspection: null,
    selectedArchitecture: '',
    resolution: null,
  };
}

export function publicView(state) {
  const sourceCycle = state.design.cycles[state.scenario.sourceCycleIndex];
  const executionCycle = state.design.cycles[state.scenario.executionCycleIndex];
  return {
    schemaVersion: 1,
    kind: 'ordivon.game.pc01-e03-playable-r1-state',
    scenarioId: state.scenario.id,
    phase: state.phase,
    lagSteps: state.scenario.lagSteps,
    causePersistence: state.causePersistence,
    previousArchitecture: state.scenario.previousArchitecture,
    currentContext: {
      id: sourceCycle.id,
      operatingContext: sourceCycle.operatingContext,
      visibleSymptom: sourceCycle.visibleSymptom,
    },
    executionForecast: state.forecastVisible
      ? {
          visible: true,
          id: executionCycle.id,
          operatingContext: executionCycle.operatingContext,
          visibleSymptom: executionCycle.visibleSymptom,
        }
      : { visible: false },
    inspection: state.inspection ? { ...state.inspection } : null,
    selectedArchitecture: state.selectedArchitecture,
    resolution: state.resolution ? { ...state.resolution } : null,
  };
}

export function inspect(state, diagnostic) {
  if (state.phase !== 'decision') throw new Error('inspection requires decision phase');
  if (state.inspection) throw new Error('inspection already used');
  if (!state.design.diagnostics.includes(diagnostic) || diagnostic === 'none') {
    throw new Error(`invalid inspection diagnostic: ${diagnostic}`);
  }
  state.inspection = {
    diagnostic,
    observation: observation(diagnostic, state.sourceCause),
  };
  return publicView(state);
}

export function selectArchitecture(state, architecture) {
  if (state.phase !== 'decision') throw new Error('architecture selection requires decision phase');
  if (!architectures(state.design).includes(architecture)) {
    throw new Error(`unknown architecture: ${architecture}`);
  }
  state.selectedArchitecture = architecture;
  return publicView(state);
}

export function commit(state) {
  if (state.phase !== 'decision') throw new Error('commit requires decision phase');
  if (!state.selectedArchitecture) throw new Error('select an architecture before commit');
  const executionCycle = state.design.cycles[state.scenario.executionCycleIndex];
  const diagnostic = state.inspection?.diagnostic ?? 'none';
  const observationValue = state.inspection?.observation ?? 'NONE';
  const baseReward = Number(
    executionCycle.rewardByCauseAndArchitecture[state.executionCause][state.selectedArchitecture],
  );
  const diagnosticCost = diagnostic === 'none' ? 0 : Number(state.design.diagnosticCost);
  const switching = switchCost(
    state.design,
    state.scenario.previousArchitecture,
    state.selectedArchitecture,
  );
  state.phase = 'resolved';
  state.resolution = {
    sourceCause: state.sourceCause,
    executionCause: state.executionCause,
    currentContextId: state.design.cycles[state.scenario.sourceCycleIndex].id,
    executionContextId: executionCycle.id,
    diagnostic,
    observation: observationValue,
    architecture: state.selectedArchitecture,
    baseReward,
    diagnosticCost,
    switchCost: switching,
    net: baseReward - diagnosticCost - switching,
  };
  return publicView(state);
}

function policyChanged(a, b) {
  return JSON.stringify(a) !== JSON.stringify(b);
}

function scenarioWitness(design, scenarioId) {
  const anticipatory = solvePolicy(design, scenarioId, {
    rewardContext: 'execution',
    causePersistence: true,
    allowDiagnostics: true,
  });
  const reactive = solvePolicy(design, scenarioId, {
    rewardContext: 'source',
    causePersistence: true,
    allowDiagnostics: true,
  });
  const reactiveExecutionValue = evaluatePolicy(design, scenarioId, reactive.policy, {
    rewardContext: 'execution',
    causePersistence: true,
  });
  const noDiagnosis = solvePolicy(design, scenarioId, {
    rewardContext: 'execution',
    causePersistence: true,
    allowDiagnostics: false,
  });
  const noPersistence = solvePolicy(design, scenarioId, {
    rewardContext: 'execution',
    causePersistence: false,
    allowDiagnostics: true,
  });
  const noPersistenceNoDiagnosis = solvePolicy(design, scenarioId, {
    rewardContext: 'execution',
    causePersistence: false,
    allowDiagnostics: false,
  });
  const forecastChangesPolicy =
    policyChanged(anticipatory.policy, reactive.policy) &&
    anticipatory.expectedValue > reactiveExecutionValue;
  const diagnosisAddsValue =
    anticipatory.policy.diagnostic !== 'none' &&
    anticipatory.expectedValue > noDiagnosis.expectedValue;
  const persistenceRequiredForDiagnosisValue =
    noPersistence.policy.diagnostic === 'none' &&
    Math.abs(noPersistence.expectedValue - noPersistenceNoDiagnosis.expectedValue) <= 1e-9;

  return {
    scenarioId,
    anticipatory,
    reactive,
    reactiveExecutionValue,
    noDiagnosis,
    noPersistence,
    noPersistenceNoDiagnosis,
    forecastChangesPolicy,
    diagnosisAddsValue,
    persistenceRequiredForDiagnosisValue,
    pass: forecastChangesPolicy && diagnosisAddsValue && persistenceRequiredForDiagnosisValue,
  };
}

export function runWitnesses(design) {
  const routeShift = scenarioWitness(design, 'route-shift');
  const sourceRule = scenarioWitness(design, 'source-rule');
  return {
    schemaVersion: 1,
    kind: 'ordivon.game.pc01-e03-playable-r1-witness',
    routeShift,
    sourceRule,
    pass: routeShift.pass && sourceRule.pass,
    productSelected: false,
    g0Entered: false,
    humanOutcomeEstablished: false,
    gameCoreChanged: false,
    claimBoundary: 'PLAYABLE_MECHANICAL_COUPLING_ONLY_NO_HUMAN_VALUE_OR_PRODUCT_SELECTION_CLAIM',
  };
}
