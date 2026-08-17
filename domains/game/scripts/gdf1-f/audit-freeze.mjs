#!/usr/bin/env node
import fs from 'node:fs';

const survival = JSON.parse(fs.readFileSync(process.argv[2] ?? 'evidence/gdf1-f/survival-table.json', 'utf8'));
const handoff = JSON.parse(fs.readFileSync(process.argv[3] ?? 'evidence/gdf1-f/handoff-map.json', 'utf8'));

const allowed = new Set(survival.allowedDispositions);
const ids = new Set();
const names = new Set();
for (const item of survival.items) {
  if (!item.id || !item.name || !item.reason) throw new Error(`invalid survival item ${JSON.stringify(item)}`);
  if (!allowed.has(item.disposition)) throw new Error(`${item.id}: invalid disposition ${item.disposition}`);
  if (ids.has(item.id)) throw new Error(`duplicate id ${item.id}`);
  if (names.has(item.name)) throw new Error(`duplicate name ${item.name}`);
  ids.add(item.id); names.add(item.name);
  if (item.disposition === 'handoff' && !item.owner) throw new Error(`${item.id}: handoff missing owner`);
}
const counts = Object.fromEntries([...allowed].map((d) => [d, survival.items.filter((x) => x.disposition === d).length]));
const frozenCount = counts['freeze-core'] + counts['freeze-guard'];
const compressionRatio = frozenCount / survival.items.length;

const requiredCore = ['GameActionContract','ControlMapping','ControlLocus','SkillProfile','SkillRelevantVariableSet','ProbeTransformation'];
for (const name of requiredCore) {
  const item = survival.items.find((x) => x.name === name);
  if (!item || item.disposition !== 'freeze-core') throw new Error(`required core ${name} missing/not core`);
}
const forbiddenCore = ['EmbodimentSingleConstruct','ActionCouplingProfile','TechniqueFamily','EntryRequirementRegion','SkillExpressionEnvelope','SaturationAttribution'];
for (const name of forbiddenCore) {
  const item = survival.items.find((x) => x.name === name);
  if (item?.disposition === 'freeze-core') throw new Error(`overfreezing ${name}`);
}
if (compressionRatio >= 0.5) throw new Error(`frozen vocabulary insufficiently compressed: ${compressionRatio}`);
if (handoff.nextBranch !== 'GDF2 Challenge / Difficulty / Failure / Mastery') throw new Error('unexpected next branch');
if (!handoff.handoffs.some((x) => x.owner.startsWith('GDF2'))) throw new Error('missing GDF2 handoff');

console.log(JSON.stringify({
  schemaVersion: 1,
  kind: 'ordivon.game.gdf1-f-freeze-audit',
  researchedItemCount: survival.items.length,
  counts,
  frozenCount,
  compressionRatio,
  requiredCore,
  nextBranch: handoff.nextBranch,
  strongestConclusion: 'GDF1 freezes a six-responsibility Action/Control/Skill core plus evidence/anti-collapse guards. Embodiment, technique, access/coupling projections and challenge/ceiling constructs do not become ontology core; lower Human mechanisms and downstream Challenge/Game Feel/Space research are explicitly handed off.'
}, null, 2));
