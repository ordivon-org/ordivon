import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";

interface TreatmentResult {
  candidateId: string;
  treatmentId: string;
  lane: "wave-a" | "wave-b";
  hypothesis: string;
  baseline: string;
  falsifier: string;
  metrics: Record<string, unknown>;
  verdict: "structural-survivor" | "weakened" | "realization-eliminated" | "structural-failure";
  nextEvidence: string;
}

interface BatteryReport {
  schemaVersion: 1;
  kind: "ordivon.game.pre-g0-ds1-structural-battery";
  methodology: {
    claimBoundary: string;
    sharedMeasures: string[];
  };
  results: TreatmentResult[];
  summary: {
    structuralSurvivors: string[];
    weakened: string[];
    realizationEliminated: string[];
    structuralFailures: string[];
    foundationReopenConditionTriggered: false;
  };
}

function round(value: number, digits = 3): number {
  const factor = 10 ** digits;
  return Math.round(value * factor) / factor;
}

function mean(values: number[]): number {
  return values.length === 0 ? 0 : values.reduce((sum, value) => sum + value, 0) / values.length;
}

function entropy(counts: Map<string, number>): number {
  const total = [...counts.values()].reduce((sum, value) => sum + value, 0);
  if (total === 0) return 0;
  let value = 0;
  for (const count of counts.values()) {
    const p = count / total;
    value -= p * Math.log2(p);
  }
  return value;
}

function countBy(values: string[]): Record<string, number> {
  const counts = new Map<string, number>();
  for (const value of values) counts.set(value, (counts.get(value) ?? 0) + 1);
  return Object.fromEntries([...counts.entries()].sort(([left], [right]) => left.localeCompare(right)));
}

function hashSeed(text: string): number {
  let hash = 2166136261 >>> 0;
  for (const character of text) {
    hash ^= character.charCodeAt(0);
    hash = Math.imul(hash, 16777619) >>> 0;
  }
  return hash || 0x9e3779b9;
}

class Rng {
  private state: number;

  constructor(seed: string) {
    this.state = hashSeed(seed);
  }

  next(): number {
    let x = this.state;
    x ^= x << 13;
    x ^= x >>> 17;
    x ^= x << 5;
    this.state = x >>> 0;
    return this.state / 0x1_0000_0000;
  }

  int(maxExclusive: number): number {
    return Math.floor(this.next() * maxExclusive);
  }

  pick<T>(values: readonly T[]): T {
    const value = values[this.int(values.length)];
    if (value === undefined) throw new Error("cannot pick from empty collection");
    return value;
  }
}

// ---------------------------------------------------------------------------
// D02 — Legible Tactical Puzzle
// ---------------------------------------------------------------------------

type Point = { x: number; y: number };
type TacticalFamily = "move" | "strike" | "brace" | "wait";

interface TacticalUnit {
  id: string;
  point: Point;
  hp: number;
}

interface TacticalEnemy {
  id: string;
  point: Point;
  target: Point;
}

interface TacticalState {
  units: TacticalUnit[];
  enemies: TacticalEnemy[];
  beacon: Point;
}

interface TacticalAction {
  family: TacticalFamily;
  actorId?: string;
  target?: Point;
  enemyId?: string;
}

function pointKey(point: Point): string {
  return `${point.x},${point.y}`;
}

function adjacent(left: Point, right: Point): boolean {
  return Math.abs(left.x - right.x) + Math.abs(left.y - right.y) === 1;
}

function tacticalActions(state: TacticalState): TacticalAction[] {
  const actions: TacticalAction[] = [{ family: "wait" }];
  const occupied = new Set(state.units.map((unit) => pointKey(unit.point)));
  for (const unit of state.units) {
    actions.push({ family: "brace", actorId: unit.id });
    for (const delta of [{ x: 1, y: 0 }, { x: -1, y: 0 }, { x: 0, y: 1 }, { x: 0, y: -1 }]) {
      const target = { x: unit.point.x + delta.x, y: unit.point.y + delta.y };
      if (target.x < 0 || target.y < 0 || target.x >= 6 || target.y >= 6) continue;
      if (occupied.has(pointKey(target))) continue;
      actions.push({ family: "move", actorId: unit.id, target });
    }
    for (const enemy of state.enemies) {
      if (adjacent(unit.point, enemy.point)) actions.push({ family: "strike", actorId: unit.id, enemyId: enemy.id });
    }
  }
  return actions;
}

function tacticalScore(state: TacticalState, action: TacticalAction): number {
  const units = state.units.map((unit) => ({ ...unit, point: { ...unit.point } }));
  let enemies = state.enemies.map((enemy) => ({ ...enemy, point: { ...enemy.point }, target: { ...enemy.target } }));
  const acting = action.actorId ? units.find((unit) => unit.id === action.actorId) : undefined;
  let kills = 0;
  if (action.family === "move" && acting && action.target) acting.point = { ...action.target };
  if (action.family === "strike" && action.enemyId) {
    const before = enemies.length;
    enemies = enemies.filter((enemy) => enemy.id !== action.enemyId);
    kills = before - enemies.length;
  }
  const braced = action.family === "brace" ? action.actorId : null;
  let beaconHits = 0;
  for (const enemy of enemies) {
    const victim = units.find((unit) => pointKey(unit.point) === pointKey(enemy.target));
    if (victim) {
      victim.hp -= victim.id === braced ? 1 : 2;
    } else if (pointKey(enemy.target) === pointKey(state.beacon)) {
      beaconHits += 1;
    }
  }
  const alive = units.filter((unit) => unit.hp > 0).length;
  const totalHp = units.reduce((sum, unit) => sum + Math.max(0, unit.hp), 0);
  return kills * 7 + alive * 5 + totalHp * 1.5 - beaconHits * 9;
}

function randomDistinctPoint(rng: Rng, used: Set<string>): Point {
  for (let attempt = 0; attempt < 100; attempt += 1) {
    const point = { x: rng.int(6), y: rng.int(6) };
    const key = pointKey(point);
    if (!used.has(key)) {
      used.add(key);
      return point;
    }
  }
  throw new Error("failed to generate distinct tactical point");
}

function tacticalState(seed: number): TacticalState {
  const rng = new Rng(`d02:${seed}`);
  const used = new Set<string>();
  const units = Array.from({ length: 3 }, (_, index) => ({ id: `u${index}`, point: randomDistinctPoint(rng, used), hp: 2 + rng.int(2) }));
  const enemies = Array.from({ length: 3 }, (_, index) => ({ id: `e${index}`, point: randomDistinctPoint(rng, used), target: { x: 0, y: 0 } }));
  const beacon = randomDistinctPoint(rng, used);
  for (const enemy of enemies) {
    const targetPool: Point[] = [...units.map((unit) => unit.point), beacon, { x: rng.int(6), y: rng.int(6) }];
    enemy.target = { ...rng.pick(targetPool) };
  }
  return { units, enemies, beacon };
}

function bestTactical(state: TacticalState): { best: TacticalAction[]; bestScore: number; nearOptimalCount: number } {
  const scored = tacticalActions(state).map((action) => ({ action, score: tacticalScore(state, action) }));
  const bestScore = Math.max(...scored.map((entry) => entry.score));
  const best = scored.filter((entry) => Math.abs(entry.score - bestScore) < 1e-9).map((entry) => entry.action);
  const nearOptimalCount = scored.filter((entry) => entry.score >= bestScore - 2).length;
  return { best, bestScore, nearOptimalCount };
}

function runD02(): TreatmentResult {
  const familySelections: string[] = [];
  const nearCounts: number[] = [];
  let intentSensitive = 0;
  const states = 320;
  for (let seed = 0; seed < states; seed += 1) {
    const state = tacticalState(seed);
    const original = bestTactical(state);
    familySelections.push(original.best[0]?.family ?? "none");
    nearCounts.push(original.nearOptimalCount);
    const changed = structuredClone(state);
    const enemy = changed.enemies[0];
    if (enemy) enemy.target = { x: (enemy.target.x + 2) % 6, y: (enemy.target.y + 3) % 6 };
    const counterfactual = bestTactical(changed);
    const originalSet = new Set(original.best.map((action) => `${action.family}:${action.actorId ?? ""}:${action.enemyId ?? ""}:${action.target ? pointKey(action.target) : ""}`));
    if (counterfactual.best.some((action) => !originalSet.has(`${action.family}:${action.actorId ?? ""}:${action.enemyId ?? ""}:${action.target ? pointKey(action.target) : ""}`))) {
      intentSensitive += 1;
    }
  }
  const counts = new Map<string, number>();
  for (const family of familySelections) counts.set(family, (counts.get(family) ?? 0) + 1);
  const familyEntropy = entropy(counts);
  const intentSensitivity = intentSensitive / states;
  const dominantRate = Math.max(...counts.values()) / states;
  const metrics = {
    generatedStates: states,
    bestActionFamilies: countBy(familySelections),
    bestFamilyEntropyBits: round(familyEntropy),
    dominantFamilyRate: round(dominantRate),
    telegraphCounterfactualChangesBestActionRate: round(intentSensitivity),
    meanNearOptimalActionsWithinTwoPoints: round(mean(nearCounts)),
  };
  const pass = familyEntropy >= 1.1 && dominantRate <= 0.78 && intentSensitivity >= 0.3;
  return {
    candidateId: "D02",
    treatmentId: "d02-grid-telegraph-v1",
    lane: "wave-a",
    hypothesis: "Readable telegraphed threats can create state-sensitive tactical decisions without opponent cognition.",
    baseline: "One-step deterministic 6x6 board with three units, three telegraphed enemies and no Agent calls.",
    falsifier: "Fail if one action family dominates most states or changing visible enemy intent rarely changes the best response.",
    metrics,
    verdict: pass ? "structural-survivor" : "realization-eliminated",
    nextEvidence: pass ? "Human graybox play should test whether the legible decisions feel like planning rather than arithmetic." : "Delete or redesign this tactical realization before any presentation investment; do not infer that the whole tactical GameForm is falsified by one micro-ruleset.",
  };
}

// ---------------------------------------------------------------------------
// D03 — Epistemic Mystery / Knowledge Exploration
// ---------------------------------------------------------------------------

interface Hypothesis {
  culprit: number;
  motive: number;
}

const hypotheses: Hypothesis[] = Array.from({ length: 6 }, (_, culprit) => Array.from({ length: 3 }, (_, motive) => ({ culprit, motive }))).flat();

const clues: Array<(hypothesis: Hypothesis) => string> = [
  (h) => `parity:${h.culprit % 2}`,
  (h) => `district:${h.culprit < 3 ? 0 : 1}`,
  (h) => `motive:${h.motive}`,
  (h) => `trace:${(h.culprit + h.motive) % 3}`,
  (h) => `route:${h.culprit % 3}`,
  (h) => `witness:${(h.culprit * 2 + h.motive) % 4}`,
  (h) => `timing:${(h.culprit + 2 * h.motive) % 5}`,
  (h) => `signature:${(h.culprit * 3 + h.motive * 2) % 7}`,
];

function partitionEntropy(candidates: Hypothesis[], clueIndex: number): number {
  const groups = new Map<string, number>();
  for (const candidate of candidates) {
    const value = clues[clueIndex]!(candidate);
    groups.set(value, (groups.get(value) ?? 0) + 1);
  }
  const total = candidates.length;
  let expected = 0;
  for (const size of groups.values()) expected += (size / total) * Math.log2(size);
  return Math.log2(total) - expected;
}

function filterHypotheses(candidates: Hypothesis[], clueIndex: number, truth: Hypothesis): Hypothesis[] {
  const observed = clues[clueIndex]!(truth);
  return candidates.filter((candidate) => clues[clueIndex]!(candidate) === observed);
}

function greedyMystery(truth: Hypothesis, budget: number): { remaining: number; sequence: number[]; information: number } {
  let candidates = [...hypotheses];
  const unused = new Set(clues.map((_, index) => index));
  const sequence: number[] = [];
  let information = 0;
  for (let step = 0; step < budget && candidates.length > 1; step += 1) {
    let bestIndex = -1;
    let bestGain = -Infinity;
    for (const clueIndex of unused) {
      const gain = partitionEntropy(candidates, clueIndex);
      if (gain > bestGain + 1e-12) {
        bestGain = gain;
        bestIndex = clueIndex;
      }
    }
    if (bestIndex < 0) break;
    unused.delete(bestIndex);
    sequence.push(bestIndex);
    const before = Math.log2(candidates.length);
    candidates = filterHypotheses(candidates, bestIndex, truth);
    information += before - Math.log2(candidates.length);
  }
  return { remaining: candidates.length, sequence, information };
}

function fixedMystery(truth: Hypothesis, clueOrder: number[], budget: number): number {
  let candidates = [...hypotheses];
  for (const clueIndex of clueOrder.slice(0, budget)) candidates = filterHypotheses(candidates, clueIndex, truth);
  return candidates.length;
}

function mysteryBudgetMetrics(budget: number): Record<string, unknown> {
  const greedy = hypotheses.map((truth) => greedyMystery(truth, budget));
  const fixedRemaining = hypotheses.map((truth) => fixedMystery(truth, [0, 1, 2, 3, 4, 5, 6, 7], budget));
  const rng = new Rng(`d03-random:${budget}`);
  const randomRemaining: number[] = [];
  for (const truth of hypotheses) {
    for (let replica = 0; replica < 50; replica += 1) {
      const order = clues.map((_, index) => index);
      for (let index = order.length - 1; index > 0; index -= 1) {
        const swap = rng.int(index + 1);
        [order[index], order[swap]] = [order[swap]!, order[index]!];
      }
      randomRemaining.push(fixedMystery(truth, order, budget));
    }
  }
  const solvedRate = greedy.filter((entry) => entry.remaining === 1).length / greedy.length;
  const greedyRemaining = mean(greedy.map((entry) => entry.remaining));
  const fixedMean = mean(fixedRemaining);
  const randomMean = mean(randomRemaining);
  return {
    clueBudget: budget,
    greedySolvedRate: round(solvedRate),
    meanRemainingHypotheses: {
      greedy: round(greedyRemaining),
      fixedOrder: round(fixedMean),
      randomOrder: round(randomMean),
    },
    meanGreedyInformationBits: round(mean(greedy.map((entry) => entry.information))),
    adaptiveGreedySequenceCount: new Set(greedy.map((entry) => entry.sequence.join("-"))).size,
    greedyFirstClueDistribution: countBy(greedy.map((entry) => String(entry.sequence[0] ?? -1))),
    greedySecondClueDistribution: countBy(greedy.map((entry) => String(entry.sequence[1] ?? -1))),
  };
}

function runD03(): TreatmentResult {
  const scarce = mysteryBudgetMetrics(2);
  const generous = mysteryBudgetMetrics(4);
  const scarceRemaining = scarce.meanRemainingHypotheses as { greedy: number; fixedOrder: number; randomOrder: number };
  const scarceSolvedRate = scarce.greedySolvedRate as number;
  const scarceAdaptiveSequences = scarce.adaptiveGreedySequenceCount as number;
  const generousRemaining = generous.meanRemainingHypotheses as { greedy: number; fixedOrder: number; randomOrder: number };
  const scarcityCreatesChoice = scarceSolvedRate >= 0.9 && scarceRemaining.greedy < scarceRemaining.fixedOrder * 0.4 && scarceRemaining.greedy < scarceRemaining.randomOrder * 0.5 && scarceAdaptiveSequences >= 2;
  const generosityCollapsesChoice = Math.abs(generousRemaining.greedy - generousRemaining.fixedOrder) <= 0.05;
  const metrics = {
    hypotheses: hypotheses.length,
    clues: clues.length,
    scarceBudget: scarce,
    generousBudgetAblation: generous,
    scarcityCreatesAdaptiveAdvantage: scarcityCreatesChoice,
    generousBudgetCollapsesAdaptiveAdvantage: generosityCollapsesChoice,
  };
  return {
    candidateId: "D03",
    treatmentId: "d03-evidence-scarcity-ablation-v2",
    lane: "wave-a",
    hypothesis: "Knowledge acquisition becomes gameplay when evidence selection is scarce enough that choosing what to inspect changes the reachable hypothesis state.",
    baseline: "Eighteen hidden histories and eight deterministic clues tested under both a scarce two-inspection budget and an over-generous four-inspection ablation.",
    falsifier: "Fail if adaptive evidence choice does not outperform fixed/random inspection under scarcity. Treat parity under a generous budget as evidence that excess information destroys the decision problem.",
    metrics,
    verdict: scarcityCreatesChoice ? "structural-survivor" : "realization-eliminated",
    nextEvidence: scarcityCreatesChoice ? "Retain D03 with a hard design constraint: information access must stay scarce/branching enough to preserve hypothesis choice. Build one human-readable case and test model revision versus clue-checklist behavior." : "Redesign the information topology; this realization does not make evidence selection causally valuable.",
  };
}

// ---------------------------------------------------------------------------
// D04 — Combinatorial Roguelike Buildcraft
// ---------------------------------------------------------------------------

type Card = "strike" | "poison" | "block" | "draw" | "strength" | "dexterity";
type Encounter = "rush" | "armor" | "attrition" | "burst" | "swarm";

const cards: readonly Card[] = ["strike", "poison", "block", "draw", "strength", "dexterity"];
const encounters: readonly Encounter[] = ["rush", "armor", "attrition", "burst", "swarm"];

function buildScore(build: Record<Card, number>, encounter: Encounter): number {
  const frontload = build.strike * (2 + 0.7 * build.strength);
  const poison = build.poison * (1.5 + 0.55 * build.draw);
  const defense = build.block * (1.8 + 0.6 * build.dexterity);
  const cycle = build.draw * 0.9 + Math.min(build.draw, build.strike + build.poison) * 0.45;
  const scaling = build.strength * (1 + 0.3 * build.strike) + build.dexterity * (0.8 + 0.25 * build.block);
  const encounterWeights: Record<Encounter, [number, number, number, number, number]> = {
    rush: [1.5, 0.5, 0.9, 0.5, 0.4],
    armor: [0.7, 1.5, 0.8, 0.8, 1.0],
    attrition: [0.7, 1.0, 1.5, 0.8, 1.1],
    burst: [1.1, 0.5, 1.4, 0.4, 0.5],
    swarm: [1.0, 1.1, 0.7, 1.5, 0.5],
  };
  const [wf, wp, wd, wc, ws] = encounterWeights[encounter];
  return frontload * wf + poison * wp + defense * wd + cycle * wc + scaling * ws;
}

function emptyBuild(): Record<Card, number> {
  return { strike: 1, poison: 0, block: 1, draw: 0, strength: 0, dexterity: 0 };
}

function addCard(build: Record<Card, number>, card: Card): Record<Card, number> {
  return { ...build, [card]: build[card] + 1 };
}

function buildRun(seed: number): { offers: Card[][]; encounters: Encounter[] } {
  const rng = new Rng(`d04:${seed}`);
  const offers = Array.from({ length: 6 }, () => {
    const selected = new Set<Card>();
    while (selected.size < 3) selected.add(rng.pick(cards));
    return [...selected];
  });
  const runEncounters = Array.from({ length: 5 }, () => rng.pick(encounters));
  return { offers, encounters: runEncounters };
}

function totalBuildScore(build: Record<Card, number>, runEncounters: Encounter[]): number {
  return runEncounters.reduce((sum, encounter) => sum + buildScore(build, encounter), 0);
}

function optimalBuild(run: { offers: Card[][]; encounters: Encounter[] }): { score: number; choices: Card[]; build: Record<Card, number> } {
  let best = { score: -Infinity, choices: [] as Card[], build: emptyBuild() };
  function search(step: number, build: Record<Card, number>, choices: Card[]): void {
    if (step >= run.offers.length) {
      const score = totalBuildScore(build, run.encounters);
      if (score > best.score) best = { score, choices: [...choices], build };
      return;
    }
    for (const card of run.offers[step]!) search(step + 1, addCard(build, card), [...choices, card]);
  }
  search(0, emptyBuild(), []);
  return best;
}

function greedyBuild(run: { offers: Card[][]; encounters: Encounter[] }): { score: number; choices: Card[] } {
  let build = emptyBuild();
  const choices: Card[] = [];
  for (const offer of run.offers) {
    let bestCard = offer[0]!;
    let bestScore = -Infinity;
    for (const card of offer) {
      const next = addCard(build, card);
      const score = totalBuildScore(next, run.encounters);
      if (score > bestScore) {
        bestScore = score;
        bestCard = card;
      }
    }
    build = addCard(build, bestCard);
    choices.push(bestCard);
  }
  return { score: totalBuildScore(build, run.encounters), choices };
}

function runD04(): TreatmentResult {
  const replicas = 180;
  const uplifts: number[] = [];
  const optimalChoices: Card[] = [];
  const signatures: string[] = [];
  for (let seed = 0; seed < replicas; seed += 1) {
    const run = buildRun(seed);
    const optimal = optimalBuild(run);
    const greedy = greedyBuild(run);
    uplifts.push((optimal.score - greedy.score) / Math.max(1, greedy.score));
    optimalChoices.push(...optimal.choices);
    const signature = cards
      .map((card) => [card, optimal.build[card]] as const)
      .sort((left, right) => right[1] - left[1] || left[0].localeCompare(right[0]))
      .slice(0, 2)
      .map(([card]) => card)
      .join("+");
    signatures.push(signature);
  }
  const choiceCounts = countBy(optimalChoices);
  const maximumChoiceRate = Math.max(...Object.values(choiceCounts)) / optimalChoices.length;
  const meanUplift = mean(uplifts);
  const distinctSignatures = new Set(signatures).size;
  const metrics = {
    simulatedRuns: replicas,
    optimalVsGreedyMeanScoreUplift: round(meanUplift),
    optimalVsGreedyPositiveUpliftRate: round(uplifts.filter((value) => value > 0.02).length / uplifts.length),
    distinctTopTwoBuildSignatures: distinctSignatures,
    optimalCardChoiceDistribution: choiceCounts,
    maximumSingleCardChoiceRate: round(maximumChoiceRate),
  };
  const pass = meanUplift >= 0.035 && distinctSignatures >= 6 && maximumChoiceRate <= 0.55;
  return {
    candidateId: "D04",
    treatmentId: "d04-six-pick-synergy-v1",
    lane: "wave-a",
    hypothesis: "Combinatorial synergies and changing encounter demands can create path-dependent build decisions rather than raw-power selection.",
    baseline: "Six draft choices from three-card offers across five encounter archetypes, solved exhaustively against a greedy immediate-score policy.",
    falsifier: "Fail if greedy selection is nearly optimal, one card dominates optimal picks, or best builds collapse to one signature across seeds.",
    metrics,
    verdict: pass ? "structural-survivor" : "realization-eliminated",
    nextEvidence: pass ? "A tiny playable run should test whether players can perceive the synergies and whether risk/uncertainty improves rather than obscures build planning." : "Delete or rebalance this combinatorial realization before adding procedural content; one failed parameterization does not falsify the whole form.",
  };
}

// ---------------------------------------------------------------------------
// D05 — Automation / Logistics Engineering
// ---------------------------------------------------------------------------

type Machine = "ironMiner" | "copperMiner" | "ironSmelter" | "copperSmelter" | "gear" | "wire" | "lab" | "press" | "assembler";
const machines: readonly Machine[] = ["ironMiner", "copperMiner", "ironSmelter", "copperSmelter", "gear", "wire", "lab", "press", "assembler"];

interface Allocation extends Record<Machine, number> {}

function allocationThroughput(allocation: Allocation): { science: number; ammo: number; circuit: number } {
  const ironPlate = Math.min(allocation.ironMiner * 2, allocation.ironSmelter * 2);
  const copperPlate = Math.min(allocation.copperMiner * 2, allocation.copperSmelter * 2);
  const gear = Math.min(ironPlate / 2, allocation.gear * 2);
  const wire = Math.min(copperPlate * 2, allocation.wire * 4);
  return {
    science: Math.min(gear, wire, allocation.lab * 1.5),
    ammo: Math.min(ironPlate / 2, gear, allocation.press * 2),
    circuit: Math.min(ironPlate, wire / 2, allocation.assembler * 2),
  };
}

function enumerateAllocations(totalMachines: number): Allocation[] {
  const result: Allocation[] = [];
  const current = Object.fromEntries(machines.map((machine) => [machine, 0])) as Allocation;
  function recurse(index: number, remaining: number): void {
    if (index === machines.length - 1) {
      current[machines[index]!] = remaining;
      result.push({ ...current });
      return;
    }
    const machine = machines[index]!;
    for (let count = 0; count <= remaining; count += 1) {
      current[machine] = count;
      recurse(index + 1, remaining - count);
    }
  }
  recurse(0, totalMachines);
  return result;
}

function allocationSignature(allocation: Allocation): string {
  return machines.map((machine) => `${machine}:${allocation[machine]}`).join("|");
}

function runD05(): TreatmentResult {
  const totalMachines = 12;
  const allocations = enumerateAllocations(totalMachines);
  const scored = allocations.map((allocation) => ({ allocation, throughput: allocationThroughput(allocation) }));
  const objectives = ["science", "ammo", "circuit"] as const;
  const bestByObjective: Record<string, { value: number; count: number; example: string }> = {};
  const bestSets = new Map<string, Set<string>>();
  for (const objective of objectives) {
    const best = scored.reduce((maximum, entry) => Math.max(maximum, entry.throughput[objective]), -Infinity);
    const winners = scored.filter((entry) => Math.abs(entry.throughput[objective] - best) < 1e-9);
    const signatures = new Set(winners.map((entry) => allocationSignature(entry.allocation)));
    bestSets.set(objective, signatures);
    bestByObjective[objective] = { value: round(best), count: winners.length, example: [...signatures][0] ?? "" };
  }
  let universalWinners = new Set(bestSets.get(objectives[0]) ?? []);
  for (const objective of objectives.slice(1)) universalWinners = new Set([...universalWinners].filter((signature) => bestSets.get(objective)?.has(signature)));
  const mixed = scored.map((entry) => ({
    entry,
    normalized: objectives.map((objective) => entry.throughput[objective] / (bestByObjective[objective]?.value || 1)),
  }));
  const balanced = mixed
    .map(({ entry, normalized }) => ({ signature: allocationSignature(entry.allocation), score: Math.cbrt(Math.max(0, normalized[0]!) * Math.max(0, normalized[1]!) * Math.max(0, normalized[2]!)) }))
    .sort((left, right) => right.score - left.score);
  const topBalanced = balanced.slice(0, 20);
  const pairOverlap: Record<string, number> = {};
  for (let left = 0; left < objectives.length; left += 1) {
    for (let right = left + 1; right < objectives.length; right += 1) {
      const a = bestSets.get(objectives[left]!) ?? new Set();
      const b = bestSets.get(objectives[right]!) ?? new Set();
      const intersection = [...a].filter((value) => b.has(value)).length;
      const union = new Set([...a, ...b]).size;
      pairOverlap[`${objectives[left]}:${objectives[right]}`] = union === 0 ? 0 : round(intersection / union);
    }
  }
  const metrics = {
    machineBudget: totalMachines,
    allocationsEnumerated: allocations.length,
    bestByObjective,
    bestSetJaccardOverlap: pairOverlap,
    universalBestAllocationCount: universalWinners.size,
    bestBalancedGeometricMean: round(topBalanced[0]?.score ?? 0),
    distinctTop20BalancedAllocations: new Set(topBalanced.map((entry) => entry.signature)).size,
  };
  const maximumOverlap = Math.max(...Object.values(pairOverlap));
  const pass = universalWinners.size === 0 && maximumOverlap <= 0.35 && (topBalanced[0]?.score ?? 0) >= 0.45;
  return {
    candidateId: "D05",
    treatmentId: "d05-machine-budget-v1",
    lane: "wave-a",
    hypothesis: "Automation becomes a decision game when different output goals force materially different bottleneck allocations and no universal layout wins.",
    baseline: "Twelve-machine allocation across mining, smelting and production chains; exhaustive steady-state search with no spatial art or Agents.",
    falsifier: "Fail if one allocation is optimal across objectives or objective-specific winner sets substantially coincide.",
    metrics,
    verdict: pass ? "structural-survivor" : "realization-eliminated",
    nextEvidence: pass ? "Add transport/topology constraints in a tiny interactive grid and test whether debugging bottlenecks is legible and satisfying rather than spreadsheet-only optimization." : "Delete this realization; its production chains do not yet create distinct planning questions. Do not infer a form-level failure from one allocation model.",
  };
}

// ---------------------------------------------------------------------------
// D15 — Incremental / Delegation Optimizer
// ---------------------------------------------------------------------------

type Upgrade = "generator" | "efficiency" | "research" | "automation" | "storage";
const upgrades: readonly Upgrade[] = ["generator", "efficiency", "research", "automation", "storage"];

interface IncrementalScenario {
  id: string;
  horizon: number;
  volatilityTick: number | null;
  volatilityFactor: number;
  storageBonus: number;
}

const incrementalScenarios: IncrementalScenario[] = [
  { id: "short-stable", horizon: 8, volatilityTick: null, volatilityFactor: 1, storageBonus: 0.1 },
  { id: "medium-stable", horizon: 13, volatilityTick: null, volatilityFactor: 1, storageBonus: 0.18 },
  { id: "long-stable", horizon: 22, volatilityTick: null, volatilityFactor: 1, storageBonus: 0.28 },
  { id: "early-shock", horizon: 14, volatilityTick: 5, volatilityFactor: 0.55, storageBonus: 0.2 },
  { id: "late-boom", horizon: 18, volatilityTick: 10, volatilityFactor: 1.6, storageBonus: 0.22 },
  { id: "short-boom", horizon: 10, volatilityTick: 4, volatilityFactor: 1.5, storageBonus: 0.12 },
];

const upgradeCost: Record<Upgrade, number> = { generator: 8, efficiency: 9, research: 12, automation: 11, storage: 7 };

function permutations<T>(values: readonly T[]): T[][] {
  if (values.length <= 1) return [values.slice()];
  return values.flatMap((value, index) => permutations([...values.slice(0, index), ...values.slice(index + 1)]).map((rest) => [value, ...rest]));
}

function evaluateUpgradeOrder(order: Upgrade[], scenario: IncrementalScenario): number {
  let cash = 10;
  let baseIncome = 2;
  let efficiency = 1;
  let researchMultiplier = 1;
  let automationMultiplier = 1;
  let storage = 0;
  let nextUpgrade = 0;
  for (let tick = 0; tick < scenario.horizon; tick += 1) {
    const shock = scenario.volatilityTick !== null && tick >= scenario.volatilityTick ? scenario.volatilityFactor : 1;
    const lateResearch = tick >= 8 ? researchMultiplier : 1;
    const storageProtection = shock < 1 ? 1 + storage * scenario.storageBonus : 1;
    cash += baseIncome * efficiency * lateResearch * automationMultiplier * shock * storageProtection;
    const upgrade = order[nextUpgrade];
    if (upgrade && cash >= upgradeCost[upgrade]) {
      cash -= upgradeCost[upgrade];
      nextUpgrade += 1;
      if (upgrade === "generator") baseIncome += 1.4;
      if (upgrade === "efficiency") efficiency *= 1.28;
      if (upgrade === "research") researchMultiplier *= 1.75;
      if (upgrade === "automation") automationMultiplier *= 1.4;
      if (upgrade === "storage") storage += 1;
    }
  }
  return cash;
}

function runD15(): TreatmentResult {
  const orders = permutations(upgrades);
  const bestOrders: Record<string, { order: string; value: number }> = {};
  const firstChoices: string[] = [];
  const bestValues: number[] = [];
  for (const scenario of incrementalScenarios) {
    const scored = orders.map((order) => ({ order, value: evaluateUpgradeOrder(order, scenario) })).sort((left, right) => right.value - left.value);
    const best = scored[0]!;
    bestOrders[scenario.id] = { order: best.order.join(">"), value: round(best.value) };
    firstChoices.push(best.order[0]!);
    bestValues.push(best.value);
  }
  const universalOrderRegrets = orders.map((order) => {
    const normalizedRegret = incrementalScenarios.map((scenario, index) => {
      const value = evaluateUpgradeOrder(order, scenario);
      return (bestValues[index]! - value) / Math.max(1, bestValues[index]!);
    });
    return { order: order.join(">"), meanRegret: mean(normalizedRegret), maxRegret: Math.max(...normalizedRegret) };
  }).sort((left, right) => left.meanRegret - right.meanRegret);
  const bestUniversal = universalOrderRegrets[0]!;
  const distinctBestOrders = new Set(Object.values(bestOrders).map((entry) => entry.order)).size;
  const metrics = {
    scenarios: incrementalScenarios.map((scenario) => scenario.id),
    ordersEnumerated: orders.length,
    bestOrders,
    bestFirstChoiceDistribution: countBy(firstChoices),
    distinctScenarioOptimalOrders: distinctBestOrders,
    bestSingleUniversalOrder: bestUniversal.order,
    bestUniversalMeanRegret: round(bestUniversal.meanRegret),
    bestUniversalMaximumRegret: round(bestUniversal.maxRegret),
  };
  const pass = distinctBestOrders >= 4 && new Set(firstChoices).size >= 2 && bestUniversal.maxRegret >= 0.08;
  return {
    candidateId: "D15",
    treatmentId: "d15-upgrade-order-v1",
    lane: "wave-a",
    hypothesis: "Sparse incremental decisions remain meaningful when horizon and environmental change alter investment ordering enough to require re-planning.",
    baseline: "Five one-time compounding upgrades evaluated across six horizons/shock regimes with all 120 orderings enumerated.",
    falsifier: "Fail if one upgrade order is near-optimal everywhere or scenario changes rarely alter early investment decisions.",
    metrics,
    verdict: pass ? "structural-survivor" : "realization-eliminated",
    nextEvidence: pass ? "A playable treatment must test whether sparse re-planning offsets waiting and whether delegation itself creates satisfying leverage." : "Reject this incremental realization as rote ordering/passive waiting; retain the broader D15 form only as a demoted hypothesis until a cheaper second realization shows stronger state-sensitive re-planning.",
  };
}

// ---------------------------------------------------------------------------
// D14 — Constraint-Based Co-Creation (Wave B baseline contrast)
// ---------------------------------------------------------------------------

type Motif = "wonder" | "logic" | "empathy" | "humor" | "risk" | "violence";
const motifs: readonly Motif[] = ["wonder", "logic", "empathy", "humor", "risk", "violence"];

interface Persona {
  id: string;
  weights: Record<Motif, number>;
  noveltyPreference: number;
  contrastPairs: Array<[Motif, Motif]>;
}

const personas: Persona[] = [
  { id: "scholar", weights: { wonder: 1.0, logic: 1.6, empathy: 0.5, humor: 0.2, risk: 0.4, violence: -0.5 }, noveltyPreference: 0.65, contrastPairs: [["logic", "wonder"]] },
  { id: "romantic", weights: { wonder: 1.0, logic: 0.1, empathy: 1.7, humor: 0.4, risk: 0.5, violence: -0.6 }, noveltyPreference: 0.5, contrastPairs: [["empathy", "risk"]] },
  { id: "trickster", weights: { wonder: 0.5, logic: 0.1, empathy: 0.2, humor: 1.8, risk: 1.0, violence: -0.1 }, noveltyPreference: 0.8, contrastPairs: [["humor", "risk"]] },
  { id: "warrior", weights: { wonder: 0.2, logic: 0.4, empathy: 0.1, humor: -0.2, risk: 1.2, violence: 1.5 }, noveltyPreference: 0.45, contrastPairs: [["risk", "violence"]] },
  { id: "healer", weights: { wonder: 0.4, logic: 0.5, empathy: 1.8, humor: 0.3, risk: -0.2, violence: -1.2 }, noveltyPreference: 0.55, contrastPairs: [["empathy", "logic"]] },
];

function staticRubricScore(sequence: Motif[]): number {
  const weights: Record<Motif, number> = { wonder: 1, logic: 1, empathy: 1, humor: 1, risk: 1, violence: 1 };
  return sequence.reduce((sum, motif) => sum + weights[motif], 0);
}

function personaScore(sequence: Motif[], persona: Persona, adaptive: boolean): number {
  let score = 0;
  const seen = new Map<Motif, number>();
  for (let index = 0; index < sequence.length; index += 1) {
    const motif = sequence[index]!;
    const repeats = seen.get(motif) ?? 0;
    score += persona.weights[motif];
    if (adaptive) {
      score += repeats === 0 ? persona.noveltyPreference : -persona.noveltyPreference * repeats;
      const previous = sequence[index - 1];
      if (previous && persona.contrastPairs.some(([a, b]) => (previous === a && motif === b) || (previous === b && motif === a))) score += 1.1;
    }
    seen.set(motif, repeats + 1);
  }
  return score;
}

function allMotifSequences(length: number): Motif[][] {
  let sequences: Motif[][] = [[]];
  for (let step = 0; step < length; step += 1) sequences = sequences.flatMap((sequence) => motifs.map((motif) => [...sequence, motif]));
  return sequences;
}

function runD14(): TreatmentResult {
  const sequences = allMotifSequences(4);
  const personaBestStaticHidden: Record<string, { sequence: string; score: number }> = {};
  const personaBestAdaptive: Record<string, { sequence: string; score: number }> = {};
  let changedBest = 0;
  const adaptiveBestSequences: string[] = [];
  const hiddenBestSequences: string[] = [];
  for (const persona of personas) {
    const hidden = sequences.map((sequence) => ({ sequence, score: personaScore(sequence, persona, false) })).sort((left, right) => right.score - left.score)[0]!;
    const adaptive = sequences.map((sequence) => ({ sequence, score: personaScore(sequence, persona, true) })).sort((left, right) => right.score - left.score)[0]!;
    const hiddenSignature = hidden.sequence.join(">");
    const adaptiveSignature = adaptive.sequence.join(">");
    personaBestStaticHidden[persona.id] = { sequence: hiddenSignature, score: round(hidden.score) };
    personaBestAdaptive[persona.id] = { sequence: adaptiveSignature, score: round(adaptive.score) };
    hiddenBestSequences.push(hiddenSignature);
    adaptiveBestSequences.push(adaptiveSignature);
    if (hiddenSignature !== adaptiveSignature) changedBest += 1;
  }
  const rubricScores = sequences.map(staticRubricScore);
  const rubricUniqueScores = new Set(rubricScores).size;
  const adaptiveDiversity = new Set(adaptiveBestSequences).size;
  const hiddenDiversity = new Set(hiddenBestSequences).size;
  const metrics = {
    sequenceLength: 4,
    sequencesEnumerated: sequences.length,
    staticVisibleRubricUniqueScores: rubricUniqueScores,
    hiddenFixedPersonaDistinctOptimalSequences: hiddenDiversity,
    adaptivePersonaDistinctOptimalSequences: adaptiveDiversity,
    adaptiveRuleChangesOptimalSequenceRate: round(changedBest / personas.length),
    personaBestStaticHidden,
    personaBestAdaptive,
  };
  const staticRubricFails = rubricUniqueScores === 1;
  const responsiveDistinction = adaptiveDiversity >= 4 && changedBest / personas.length >= 0.6;
  const verdict: TreatmentResult["verdict"] = staticRubricFails && responsiveDistinction ? "structural-survivor" : responsiveDistinction ? "weakened" : "realization-eliminated";
  return {
    candidateId: "D14",
    treatmentId: "d14-responsive-constraint-v1",
    lane: "wave-b",
    hypothesis: "Co-creation becomes a game when the other participant has learnable, responsive constraints that make creative sequencing strategically consequential.",
    baseline: "Visible static rubric, then hidden fixed persona, then a cheaper deterministic responsive-policy persona; no model generation is used yet.",
    falsifier: "Fail if responsiveness does not change optimal creative sequences relative to a fixed hidden preference, or if one generic sequence satisfies every persona.",
    metrics,
    verdict,
    nextEvidence: responsiveDistinction ? "The responsive-other distinction survives, but expensive model cognition is not yet necessary: a deterministic responsive policy already creates the tested causal difference. Human play must first show that richer interpretation or creativity requires cognition this cheaper baseline cannot provide." : "Do not pay live-model cost; the responsive-other hypothesis did not create a distinct decision structure.",
  };
}

const results = [runD02(), runD03(), runD04(), runD05(), runD15(), runD14()];
const report: BatteryReport = {
  schemaVersion: 1,
  kind: "ordivon.game.pre-g0-ds1-structural-battery",
  methodology: {
    claimBoundary: "This battery can falsify missing decision structure, causal sensitivity, information value, path dependence or baseline delta. It cannot establish human fun, attachment, creativity, game feel or willingness to return.",
    sharedMeasures: [
      "dominant-choice pressure",
      "state/counterfactual sensitivity",
      "adaptive information gain",
      "path-dependent policy advantage",
      "strategy/build diversity",
      "cheaper-baseline parity",
    ],
  },
  results,
  summary: {
    structuralSurvivors: results.filter((result) => result.verdict === "structural-survivor").map((result) => result.candidateId),
    weakened: results.filter((result) => result.verdict === "weakened").map((result) => result.candidateId),
    realizationEliminated: results.filter((result) => result.verdict === "realization-eliminated").map((result) => result.candidateId),
    structuralFailures: results.filter((result) => result.verdict === "structural-failure").map((result) => result.candidateId),
    foundationReopenConditionTriggered: false,
  },
};

const outputPath = resolve(process.env.ORDIVON_DS1_OUTPUT ?? "evidence/pre-g0/ds1-structural-battery.json");
mkdirSync(dirname(outputPath), { recursive: true });
writeFileSync(outputPath, `${JSON.stringify(report, null, 2)}\n`);
console.log(JSON.stringify({ outputPath, summary: report.summary, results: report.results.map((result) => ({ candidateId: result.candidateId, verdict: result.verdict, metrics: result.metrics })) }, null, 2));
