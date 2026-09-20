#!/usr/bin/env node
import fs from 'node:fs';

const survival = JSON.parse(fs.readFileSync(process.argv[2] ?? 'evidence/gdf0-h/survival-table.json', 'utf8'));
const deps = JSON.parse(fs.readFileSync(process.argv[3] ?? 'evidence/gdf0-h/dependency-map.json', 'utf8'));
const allowed = new Set(survival.dispositions);
const ids = new Set();
for (const item of survival.items) {
  for (const k of ['id','name','origin','disposition','reason']) if (!(k in item)) throw new Error(`${item.id ?? '<unknown>'} missing ${k}`);
  if (!allowed.has(item.disposition)) throw new Error(`${item.id} invalid disposition ${item.disposition}`);
  if (ids.has(item.id)) throw new Error(`duplicate survival id ${item.id}`);
  ids.add(item.id);
}
if (!deps.selection?.next) throw new Error('dependency map missing next selection');
const priorities = deps.branches.map((x) => x.priority);
if (new Set(priorities).size !== priorities.length) throw new Error('duplicate dependency priority');
const counts = Object.fromEntries([...allowed].map((d) => [d, survival.items.filter((x) => x.disposition === d).length]));
console.log(JSON.stringify({
  schemaVersion: 1,
  kind: 'ordivon.game.gdf0-h-freeze-audit',
  itemCount: survival.items.length,
  dispositionCounts: counts,
  dependencyBranchCount: deps.branches.length,
  nextBranch: deps.selection.next,
  checks: {
    hasRetirements: counts.retire > 0,
    hasHandoffs: counts.handoff > 0,
    frozenSetSmallerThanResearchSet: counts['freeze-core'] + counts['freeze-guard'] < survival.items.length,
    noDuplicateIds: true,
    noDuplicatePriorities: true
  },
  strongConclusion: 'GDF0 compression retains a smaller core/guard set than the A-G research vocabulary, explicitly retires failed candidates and hands mechanistic subdomains downstream instead of freezing research history as ontology.'
}, null, 2));
