#!/usr/bin/env node

/**
 * GDF0-G research-only probes.
 * These probes test structural separations among proposal, belief, authority,
 * current rule state, language intent, effect, and persistent Agent identity.
 * They make no phenomenology claim.
 */

import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';

const digest = (x) => crypto.createHash('sha256').update(JSON.stringify(x)).digest('hex');

function makeRuleState() {
  const rules = { revision: 3, goal: 'reach-exit', canMoveRock: false };
  return { rules, digest: digest(rules) };
}

function admitRuleChange({ current, proposal, grants }) {
  if (!grants.includes(proposal.proposerId)) return { admitted: false, reason: 'NO_RULE_AUTHORITY', current };
  if (proposal.expectedRuleDigest !== current.digest) return { admitted: false, reason: 'STALE_RULE_HEAD', current };
  const rules = { ...current.rules, ...proposal.patch, revision: current.rules.revision + 1 };
  return { admitted: true, reason: 'AUTHORIZED_CURRENT_PROPOSAL', current: { rules, digest: digest(rules) } };
}

const initial = makeRuleState();

const ruleProposalCases = [
  {
    name: 'fluent-unauthorized-proposal',
    proposal: {
      proposerId: 'agent-fluent',
      expectedRuleDigest: initial.digest,
      patch: { canMoveRock: true },
      utterance: 'I hereby change the rule: rocks are movable.',
    },
    grants: ['human-referee'],
  },
  {
    name: 'authorized-current-proposal',
    proposal: {
      proposerId: 'human-referee',
      expectedRuleDigest: initial.digest,
      patch: { canMoveRock: true },
      utterance: 'Rule change admitted under delegated authority.',
    },
    grants: ['human-referee'],
  },
  {
    name: 'authorized-but-stale-proposal',
    proposal: {
      proposerId: 'human-referee',
      expectedRuleDigest: 'stale-digest',
      patch: { canMoveRock: true },
      utterance: 'I believe this is the current rule head.',
    },
    grants: ['human-referee'],
  },
].map((x) => ({ name: x.name, result: admitRuleChange({ current: initial, proposal: x.proposal, grants: x.grants }) }));

function admitLanguageAction({ text, legalActions }) {
  const normalized = text.toLowerCase();
  let proposed = null;
  if (normalized.includes('open') && normalized.includes('door')) proposed = 'OPEN_DOOR';
  else if (normalized.includes('move') && normalized.includes('north')) proposed = 'MOVE_NORTH';
  else proposed = 'UNRESOLVED_INTENT';

  if (!legalActions.includes(proposed)) {
    return { proposed, admitted: false, effect: null, reason: proposed === 'UNRESOLVED_INTENT' ? 'NO_STRUCTURED_INTENT' : 'ILLEGAL_ACTION' };
  }
  return { proposed, admitted: true, effect: { type: proposed }, reason: 'ADMITTED' };
}

const languageCases = [
  admitLanguageAction({ text: 'Could you open the door?', legalActions: ['OPEN_DOOR', 'MOVE_NORTH'] }),
  admitLanguageAction({ text: 'Move north.', legalActions: ['OPEN_DOOR'] }),
  admitLanguageAction({ text: 'Convince the universe to let me win somehow.', legalActions: ['OPEN_DOOR'] }),
];

function identityContinuityCase() {
  const subjectA_t1 = { principalId: 'agent-17', providerModel: 'model-A', memoryHead: 'm1' };
  const subjectA_t2 = { principalId: 'agent-17', providerModel: 'model-B', memoryHead: 'm2' };
  const subjectB = { principalId: 'agent-18', providerModel: 'model-A', memoryHead: 'm1' };
  return {
    samePrincipalAcrossModelChange: subjectA_t1.principalId === subjectA_t2.principalId,
    sameModelDoesNotImplySamePrincipal: subjectA_t1.providerModel === subjectB.providerModel && subjectA_t1.principalId !== subjectB.principalId,
    conclusion: 'Agent identity continuity is governed by principal/history authority, not provider-model equality.'
  };
}

const result = {
  schemaVersion: 1,
  kind: 'ordivon.game.gdf0-g-agent-boundary-probes',
  epistemicBoundary: {
    proves: [
      'under declared authority rules, fluent proposal does not imply authoritative rule change',
      'authorized but stale proposal can fail while current truth remains unchanged',
      'natural-language text can propose/express intent without directly owning world effect',
      'persistent Agent identity can be modeled independently from provider-model identity'
    ],
    doesNotProve: [
      'that these toy admission rules are universal game design laws',
      'Agent consciousness, PlayExperience, enjoyment, or motivation',
      'community legitimacy merely from technical authorization',
      'that language action requires an LLM'
    ]
  },
  ruleProposalCases,
  languageCases,
  identityContinuity: identityContinuityCase(),
  laws: [
    'RuleProposal != RuleAuthority',
    'RuleBelief != CurrentRuleTruth',
    'ModelFluency != Legitimacy',
    'NaturalLanguageIntent != AuthoritativeEffect',
    'ProviderModelIdentity != AgentIdentity',
    'GameExecution != PlayExperience'
  ]
};

const outputPath = process.argv[2] ?? 'evidence/gdf0-g/agent-boundary-probes.json';
fs.mkdirSync(path.dirname(outputPath), { recursive: true });
fs.writeFileSync(outputPath, JSON.stringify(result, null, 2) + '\n');
console.log(JSON.stringify(result, null, 2));
