import assert from 'node:assert/strict';
import {readFileSync,existsSync} from 'node:fs';
import test from 'node:test';
import {queryExternalKnowledge} from '../scripts/external-knowledge-query.ts';
import {queryMechanismExperiences} from '../scripts/mechanism-experience-query.ts';

const load=(p:string)=>JSON.parse(readFileSync(new URL('../'+p,import.meta.url),'utf8'));
test('Game registers actual source-bound LEGO with six responsibilities',()=>{
  const plan=load('planning/lego-plan-r1.json');
  assert.equal(plan.project.id,'ordivon-game');
  assert.equal(plan.nodes.length,6);
  assert.ok(plan.nodes.some((n: any) => n.id === 'G05' && n.kind === 'interface_adapter'));
  assert.ok(plan.nodes.some((n: any) => n.id === 'G06' && n.kind === 'verifier'));
  for(const n of plan.nodes) {
    for(const f of ['id','responsibility','inputs','outputs','behavioralContract','acceptance'])
      assert.ok(n[f]&&(!Array.isArray(n[f])||n[f].length),n.id+':'+f);
    for(const ref of n.evidence)assert.ok(existsSync(new URL('../'+ref,import.meta.url)),ref);
    assert.equal(n.state,'IMPLEMENTED');
  }
  for(const name of ['products','experiments','kits'])
    assert.equal(existsSync(new URL('../'+name,import.meta.url)),false,'retired '+name);
});
test('mature sources and mechanic LEGO are immediately consumable',()=>{
  const sources=queryExternalKnowledge({type:'sources',q:'curiosity'});
  assert.equal(sources.semanticAuthorityClaimed,false);
  assert.ok(sources.items.length>0);
  const mechanics=queryMechanismExperiences({mechanism:'knowledge-progression'});
  assert.equal(mechanics.semanticAuthorityClaimed,false);
  assert.equal(mechanics.recommendationClaimed,false);
  assert.ok(mechanics.items.length>0);
});

// Phase1 native consumer closure for the six existing Game LEGO nodes.
// This binds source-facing CLI/tests to their consumers; it does not qualify
// installed game effects, dynamic consumers, or Formal proof obligations.
function validateNativeGameConsumerClaims(plan: any): void {
  const required: Record<string, string[]> = {
    G01: ['scripts/external-knowledge-query.ts', 'test/game-external-knowledge-query.test.ts'],
    G02: ['scripts/mechanism-experience-query.ts', 'test/game-lego-catalog.test.ts'],
    G03: ['scripts/build-mechanism-relationship-graph.ts', 'test/game-mechanism-relationship-graph.test.ts'],
    G04: ['scripts/design-counterexample-query.ts', 'test/game-design-counterexample-memory.test.ts'],
    G05: ['package.json', 'scripts/mechanism-relationship-query.ts', 'scripts/counterexample-synthesis-query.ts'],
    G06: ['mise.toml', 'test/fixtures/native-godot-assembly/assert.gd', 'test/fixtures/native-godot-assembly/main.tscn'],
  };
  assert.deepEqual(plan.nodes.map((n: any) => n.id), Object.keys(required));
  for (const node of plan.nodes) {
    const declared = node.consumerEvidence;
    assert.ok(Array.isArray(declared) && declared.length, node.id + ': missing consumer declaration');
    assert.equal(new Set(declared).size, declared.length, node.id + ': duplicate declaration');
    const expected = required[node.id];
    assert.ok(expected, node.id + ': missing canonical consumer mapping');
    for (const path of expected) {
      assert.ok(declared.includes(path), node.id + ': missing actual consumer ' + path);
    }
    for (const path of declared) {
      assert.ok(typeof path === 'string' && !path.startsWith('/') && !path.includes('..'),
        node.id + ': unsafe consumer locator');
      assert.ok(existsSync(new URL('../' + path, import.meta.url)),
        node.id + ': consumer locator absent from Git checkout ' + path);
    }
    assert.notEqual(node.formalQualification, 'VERIFIED');
    assert.notEqual(node.proofReuseAdmissible, true);
  }

  // Existing mature CLI entrypoints and independent Node tests are real
  // source consumers. The tests below must fail if a route drifts.
  const scripts = load('package.json').scripts;
  assert.equal(scripts['knowledge:external'], 'node scripts/external-knowledge-query.ts');
  assert.equal(scripts['knowledge:mechanisms'], 'node scripts/mechanism-experience-query.ts');
  assert.equal(scripts['knowledge:relationships'], 'node scripts/mechanism-relationship-query.ts');
  assert.equal(scripts['knowledge:counterexamples'], 'node scripts/design-counterexample-query.ts');
  assert.equal(scripts['knowledge:counterexample-themes'], 'node scripts/counterexample-synthesis-query.ts');
  assert.equal(scripts['build:relationship-graph'], 'node scripts/build-mechanism-relationship-graph.ts');

  const externalTest = readFileSync(new URL('./game-external-knowledge-query.test.ts', import.meta.url), 'utf8');
  assert.ok(externalTest.includes('from "../scripts/external-knowledge-query.ts"'));
  const thisTest = readFileSync(new URL('./game-lego-catalog.test.ts', import.meta.url), 'utf8');
  assert.ok(thisTest.includes("from '../scripts/mechanism-experience-query.ts'"));
  const graphTest = readFileSync(new URL('./game-mechanism-relationship-graph.test.ts', import.meta.url), 'utf8');
  assert.ok(graphTest.includes('../knowledge/game_mechanism_relationship_graph_r1.json'));
  const memoryTest = readFileSync(new URL('./game-design-counterexample-memory.test.ts', import.meta.url), 'utf8');
  assert.ok(memoryTest.includes('../knowledge/game_design_counterexample_memory_r1.json'));

  // G06 is a native Godot fixture, not shipped Bevy gameplay. Its REAL
  // consumer must nevertheless run under the Game Owner verification task.
  const nativeMise = readFileSync(new URL('../mise.toml', import.meta.url), 'utf8');
  assert.ok(nativeMise.includes('godot = "4.7.2-stable"'),
    'Game native engine must be pinned to the current stable release');
  assert.ok(nativeMise.includes('&& mise run test:native'),
    'Game Owner verify must execute the native Godot consumer');
  assert.ok(nativeMise.includes('[tasks."test:native"]'));
  assert.ok(nativeMise.includes('godot --headless --path test/fixtures/native-godot-assembly --script res://assert.gd'));
  const godotTest = readFileSync(new URL('../test/fixtures/native-godot-assembly/assert.gd', import.meta.url), 'utf8');
  assert.ok(godotTest.includes('load("res://main.tscn")'));
}

test('Game native six consumer identities have actual CLI, test and fixture readers', () => {
  const plan = load('planning/lego-plan-r1.json');
  validateNativeGameConsumerClaims(plan);
});

test('missing, fabricated or duplicate Game consumer claims fail closed', () => {
  const current = load('planning/lego-plan-r1.json');
  const none = structuredClone(current);
  delete none.nodes[0].consumerEvidence;
  assert.throws(() => validateNativeGameConsumerClaims(none), /missing consumer declaration/);

  const wrong = structuredClone(current);
  wrong.nodes[2].consumerEvidence = ['test/fabricated-not-existing.test.ts'];
  assert.throws(() => validateNativeGameConsumerClaims(wrong), /missing actual consumer/);

  const duplicate = structuredClone(current);
  duplicate.nodes[3].consumerEvidence.push(duplicate.nodes[3].consumerEvidence[0]);
  assert.throws(() => validateNativeGameConsumerClaims(duplicate), /duplicate declaration/);
});
