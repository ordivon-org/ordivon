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
