# Interface Contract Evolution R2 — Task-local Compatibility, Currentness, and Admissibility

Date: 2026-09-22
Status: **R2 CANDIDATE / NO GLOBAL INTERFACE REGISTRY**

## Problem

R1 binds one scoped task to existing owner capabilities and cross-owner composition gates.
A consumer can still hold an interface expectation that differs from what an owner or client
actually exposes.

The observed Ordivon failure is not merely "version changed":

```text
owner/server surface = current
client/connector effective surface = older snapshot
```

R2 represents that seam without copying owner truth into a new central catalog.

## Adopted owner rules

1. MCP list/cache freshness remains client-side; server truth does not force-refresh an
   arbitrary external connector snapshot.
2. Ordivon owner source/live MCP surface remains the natural owner of server capabilities.
3. Runtime compatibility/release identity binds exact Tool catalog/schema identity; version
   numbers do not replace explicit compatibility evidence.
4. Runtime C1/C4 currentness derives retained authority currentness from projected
   AuthorityVersionRef versus live owner CURRENT AuthorityVersionRef.
5. Git, transport, timestamp, or package recency do not mint semantic currentness.

## R2 data flow

```text
exact circuit-bound interface observation
                 +
task-local consumer expectation
                 |
                 v
mechanical interface evaluator
                 |
      +----------+----------+
      |          |          |
compatibility currentness admissibility
```

The three outputs are deliberately orthogonal.

## Observation

Every observation is bound to one exact Cognitive Circuit:

```text
circuitRef:
  id
  digest
```

An observation from Circuit A cannot be reused for Circuit B merely because interface bytes
happen to match.

Observation source kinds are:

- `direct-owner-observation`;
- `client-effective-surface`;
- `retained-projection`.

Direct-owner and client-effective observations are point-in-time evidence:

```text
POINT_IN_TIME_OBSERVED
```

They are not called permanently "live".

Retained projections reuse the owner-currentness rule:

```text
projected == live owner CURRENT  => CURRENT_DECLARED
projected != live owner CURRENT  => HISTORICAL_NOT_CURRENT
live CURRENT unknown             => CURRENTNESS_UNKNOWN
```

## Compatibility

Compatibility is determined independently of currentness:

```text
interface ID differs             => MISMATCH
exact digest equals required     => EXACT_MATCH
explicit alternate + evidence    => COMPATIBLE_BY_DECLARATION
otherwise                        => MISMATCH
```

There is intentionally no SemVer inference.

A historical retained projection can therefore remain `EXACT_MATCH` while its evidence is
no longer current. R2 does not destroy that compatibility fact.

## Evidence admissibility

Evidence admissibility answers whether this exact observation may support the exact
Circuit-bound interface obligation:

```text
source kind not accepted         => INADMISSIBLE
compatibility MISMATCH           => INADMISSIBLE
HISTORICAL_NOT_CURRENT           => INADMISSIBLE
CURRENTNESS_UNKNOWN              => UNKNOWN
CURRENT_DECLARED                 => ADMISSIBLE
POINT_IN_TIME_OBSERVED           => ADMISSIBLE (point-in-time only)
```

Point-in-time admissibility is intentionally not durable freshness. A later claim requiring
new currentness requires a new observation or owner-currentness evidence.

## Why the split matters

R2 preserves:

```text
Compatibility
  != Currentness
  != Evidence Admissibility
  != Domain Acceptance
```

For example:

```text
compatibilityStanding = EXACT_MATCH
currentnessStanding = HISTORICAL_NOT_CURRENT
evidenceAdmissibility = INADMISSIBLE
```

is valid and more informative than collapsing the whole seam to UNKNOWN.

## Relationship to Cognitive Circuit R1

An R2 result emits:

```text
interface-compatibility:sha256:<result-digest>
```

A verifier-owned R1 Composition Gate may cite that evidence. R1 remains generic and does not
become an interface registry. Even an admissible exact match does not establish domain
success:

```text
domainAcceptanceEstablished = false
```

## Real dogfood

The 2026-09-22 Gateway acceptance surface contains 15 Tools while the attached ChatGPT
Gateway connector surface observed in this session contains nine, including retired
`capability.list` and omitting newer collaboration/continuity Tools.

R2 classifies that exact client observation as:

```text
compatibilityStanding = MISMATCH
currentnessStanding = POINT_IN_TIME_OBSERVED
evidenceAdmissibility = INADMISSIBLE
```

This says the client-effective surface does not satisfy the task-local owner-surface
expectation. It does not say the Gateway owner is wrong.

## Anti-growth laws

R2 does not add:

- a global interface catalog;
- a private catalog epoch;
- a copied Gateway/Host/Runtime Tool registry;
- background connector refresh;
- connector cache ownership;
- automatic SemVer compatibility;
- Git-head-as-currentness;
- universal schema migration authority;
- domain acceptance authority.

## Acceptance

R2 is accepted only when:

1. observations and expectations bind the same exact Cognitive Circuit or fail closed;
2. exact compatibility is deterministic;
3. alternate compatibility requires explicit evidence;
4. compatibility remains factual when retained evidence becomes stale;
5. stale/unknown currentness affects evidence admissibility rather than rewriting
   compatibility;
6. direct owner/client observations are point-in-time rather than permanently live;
7. Git/transport recency cannot enter currentness authority;
8. real Gateway stale-client dogfood reproduces the expected mismatch;
9. an admissible R2 result can enter an R1 verifier-owned Gate without lifting domain truth.
