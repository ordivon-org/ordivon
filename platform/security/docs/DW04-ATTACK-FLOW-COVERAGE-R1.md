# DW04 Attack Flow & Defensive Coverage Projection R1

Date: 2026-10-01  
Work: `work:security:dwc-r21:dw04-attackflow-coverage:20261001`

## Decision

DW04 is a task-local, effect-free projection that overlays exact DW01/DW02 subject/applicability
state with an externally referenced attack-flow structure and defensive-control evidence.

It does **not** create a second ATT&CK, Attack Flow, D3FEND, detector catalog, control registry,
scheduler, exploit runner, recommendation engine, or security verdict owner.

The central law is:

```text
MAPPED
  != IMPLEMENTED
  != OBSERVED
  != VERIFIED_EFFECTIVE
  != VERIFIED_PROTECTED
```

These states stay independently evidenced.

## External-first semantics

R1 references current external vocabularies rather than copying them:

- MITRE Center for Threat-Informed Defense Attack Flow **v4.0** supplies attack-sequence
  semantics and a machine-readable language for adversary behavior.
- MITRE ATT&CK supplies offensive technique, mitigation and detection-strategy identifiers.
- MITRE D3FEND **1.6.0** supplies defensive-technique vocabulary and published ATT&CK
  mitigation-to-D3FEND mappings.
- ATT&CK legacy Data Sources were deprecated in ATT&CK v18; R1 therefore does not build a
  new dependency on that deprecated catalog and may reference current ATT&CK Detection
  Strategies instead.

External references remain external truth. DW04 stores only exact references plus local owner
evidence.

## Input seams

DW04 requires:

1. exact DW01 `ordivon.security.dwc-subject-exposure-snapshot`;
2. exact DW02 `ordivon.security.threat-applicability-fusion` bound to that same
   case/epoch/subject/snapshot/evidence identity;
3. one bounded Attack Flow reference carrying:
   - exact source ref/digest;
   - Attack Flow version;
   - task-local action refs pointing to external technique refs;
   - explicit DAG edges;
   - explicit entry/objective refs;
4. task-local control overlays with external defensive refs and independent local standings.

Subject mismatch, dangling actions, duplicate identities, graph cycles, invalid local standings,
or locally-positive standings without evidence fail closed.

## Control evidence axes

Each control has separate axes:

### Mapping

A control names one or more exact attack actions and at least one external defensive reference:

- ATT&CK mitigation;
- D3FEND technique; and/or
- ATT&CK Detection Strategy.

Mapping requires mapping evidence, but proves no local deployment.

### Implementation

`IMPLEMENTED | NOT_IMPLEMENTED | UNKNOWN`

Any non-UNKNOWN standing requires owner evidence.

### Observation

`OBSERVED | NO_OBSERVATION_WITH_COVERAGE | UNKNOWN`

Any non-UNKNOWN standing requires observation/coverage evidence. A generic absence of an alert
does not become `NO_OBSERVATION_WITH_COVERAGE`.

### Effectiveness

`VERIFIED_EFFECTIVE | VERIFIED_INEFFECTIVE | UNKNOWN`

Any non-UNKNOWN standing requires independent effectiveness evidence. VERIFIED_EFFECTIVE or
VERIFIED_INEFFECTIVE is illegal unless the control is also IMPLEMENTED.

Even VERIFIED_EFFECTIVE at a single action does not mint global verified protection.

## Structural analysis

DW04 enumerates bounded entry-to-objective paths in the task-local DAG and exposes:

- per-action mapped / implemented / observed / verified-effective / verified-ineffective refs;
- per-path evidence presence;
- unmapped and local-evidence gaps;
- `structuralCutActionRefs`: actions present on every enumerated path.

A structural cut is a graph property only. It is **not** a recommendation, priority rank,
effect authorization, or effectiveness claim.

## DW05 demand gate

DW05 is optional.

R1 emits `authorizedValidationCandidateControlRefs` only when a control is:

1. locally `IMPLEMENTED`;
2. effectiveness is still `UNKNOWN`; and
3. it maps to a structural cut action where additional evidence could change downstream
   planning.

This produces:

`OPTIONAL_MAY_CHANGE_DOWNSTREAM_DECISION`

It does not authorize validation. DW05 must independently prove target authority, isolation,
network/persistence constraints, and observer separation before any experiment.

Mapping-only historical knowledge does **not** trigger DW05.

## Historical Exchange replay

The frozen fixture:

`platform/security/fixtures/dw04/exchange-attack-flow-replay-r1.json`

uses a deliberately high-level behavior abstraction for both ProxyLogon and ProxyShell:

```text
ATT&CK T1190 Exploit Public-Facing Application
        ↓
ATT&CK T1505.003 Server Software Component: Web Shell
```

The fixture contains no exploit payload, command sequence, vulnerability-triggering recipe, or
live target information.

External mapping examples:

- ATT&CK T1190 lists Update Software (M1051) as a mitigation.
- D3FEND's published M1051 mapping points to D3-SU Software Update.
- ATT&CK DET0394 is a current detection strategy for T1505.003 Web Shell behavior.

In the historical replay all local implementation, observation and effectiveness standings are
UNKNOWN. Therefore both flows remain mapping-only and DW05 is not triggered.

## Qualification

R1 tests cover:

- exact DW01/DW02 binding;
- attack DAG cycle rejection;
- unknown action/control mapping rejection;
- evidence required for non-UNKNOWN local standings;
- mapped != implemented != observed != verified-effective separation;
- verified-effective-at-cut remaining distinct from global verified protection;
- optional DW05 trigger only for implemented + effect-unknown structural-cut controls;
- branch/cut analysis over parallel paths;
- high-level ProxyLogon/ProxyShell replay with no exploit operational content.

## Source anchors

- Attack Flow v4.0: https://center-for-threat-informed-defense.github.io/attack-flow/
- MITRE ATT&CK T1190: https://attack.mitre.org/techniques/T1190/
- MITRE ATT&CK T1505.003: https://attack.mitre.org/techniques/T1505/003/
- MITRE ATT&CK DET0394: https://attack.mitre.org/detectionstrategies/DET0394/
- MITRE D3FEND mappings: https://d3fend.mitre.org/mappings/attack-mitigations/
- MITRE D3FEND resources/changelog: https://d3fend.mitre.org/resources/

## Truth boundary

DW04 establishes only structural and evidence-state projection for one bounded defense epoch.

It never grants authority, executes an effect, proves exploitability, proves control
effectiveness by mapping, proves absence of compromise, or closes protection/recovery.
