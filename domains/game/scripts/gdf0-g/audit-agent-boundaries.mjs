#!/usr/bin/env node
import fs from 'node:fs';

const evidencePath = process.argv[2] ?? 'evidence/gdf0-g/agent-era-evidence.json';
const probePath = process.argv[3] ?? 'evidence/gdf0-g/agent-boundary-probes.json';
const evidence = JSON.parse(fs.readFileSync(evidencePath, 'utf8'));
const probes = JSON.parse(fs.readFileSync(probePath, 'utf8'));

for (const item of evidence.evidence) {
  for (const field of ['id','source','target','observations','supports','limits']) {
    if (!(field in item)) throw new Error(`${item.id ?? '<unknown>'} missing ${field}`);
  }
}

const proposalCases = probes.ruleProposalCases;
const unauthorizedRejected = proposalCases.find((x) => x.name === 'fluent-unauthorized-proposal')?.result.reason === 'NO_RULE_AUTHORITY';
const staleRejected = proposalCases.find((x) => x.name === 'authorized-but-stale-proposal')?.result.reason === 'STALE_RULE_HEAD';
const authorizedAdmitted = proposalCases.find((x) => x.name === 'authorized-current-proposal')?.result.admitted === true;
const languageSeparated = probes.languageCases.some((x) => x.proposed !== 'UNRESOLVED_INTENT' && x.admitted === false) && probes.languageCases.some((x) => x.admitted === true);

const result = {
  schemaVersion: 1,
  kind: 'ordivon.game.gdf0-g-agent-boundary-audit',
  admittedExternalEvidenceCount: evidence.evidence.length,
  protocolOnlyCount: evidence.protocolOnly.length,
  structuralTests: {
    fluentProposalWithoutAuthorityRejected: unauthorizedRejected,
    authorizedCurrentProposalAdmitted: authorizedAdmitted,
    authorizedStaleProposalRejected: staleRejected,
    naturalLanguageIntentSeparatedFromAdmission: languageSeparated,
    providerIdentitySeparatedFromAgentIdentity: probes.identityContinuity.sameModelDoesNotImplySamePrincipal && probes.identityContinuity.samePrincipalAcrossModelChange
  },
  strongConclusion:
    'Agent-era cases do not require a new Game primitive in the tested corpus; they sharpen separations among competence, experience, representation, proposal, authority, currentness, identity and legitimacy. Agent novelty is primarily a dissociation pressure on existing F1-F9 coordinates.',
  epistemicBoundary:
    'external papers support capability/behavioral claims; toy probes validate only declared Ordivon structural separations and make no phenomenology or social-legitimacy claim.'
};

console.log(JSON.stringify(result, null, 2));
