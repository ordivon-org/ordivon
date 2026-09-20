#!/usr/bin/env node
import fs from 'node:fs';

const input = process.argv[2] ?? 'evidence/gdf0-f/social-cultural-historical-evidence.json';
const data = JSON.parse(fs.readFileSync(input, 'utf8'));
const required = ['id', 'type', 'source', 'sample', 'observations', 'supports', 'limits'];
for (const e of data.evidence) {
  for (const field of required) {
    if (!(field in e)) throw new Error(`${e.id ?? '<unknown>'} missing ${field}`);
  }
  if (e.observations.length === 0 || e.supports.length === 0 || e.limits.length === 0) {
    throw new Error(`${e.id} lacks observations/supports/limits`);
  }
}
const typeCounts = {};
for (const e of data.evidence) typeCounts[e.type] = (typeCounts[e.type] ?? 0) + 1;
const audit = {
  schemaVersion: 1,
  kind: 'ordivon.game.gdf0-f-social-cultural-audit',
  evidenceCount: data.evidence.length,
  evidenceTypeCounts: typeCounts,
  candidateAudit: data.candidateAudit,
  strongConclusion:
    'social/cultural/historical evidence rejects a central-designer/exact-rulebook/mechanical-category account: game/play practices are transmitted, negotiated, institutionalized and culturally patterned; category/frame cues can causally feed back into behavior, while solitary pretense shows social negotiation is not necessary for every PlayFrame',
  epistemicBoundary:
    'this audit checks explicit evidence bookkeeping and candidate dispositions; cross-cultural and historical causal interpretation remains bounded by each source design',
};
console.log(JSON.stringify(audit, null, 2));
