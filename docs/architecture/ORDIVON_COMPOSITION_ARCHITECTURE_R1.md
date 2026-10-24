# Ordivon Composition Architecture Contract R1

Date: 2026-09-21  
Status: CURRENT ARCHITECTURE CONTRACT / DEPLOYED BASELINE

Current deployed topology is projected in `CURRENT_ARCHITECTURE.md` and `deployed-architecture-r1.json`. This contract defines the durable composition laws; deployed-state claims must follow the current projection rather than historical execution plans.

## System of interest

Ordivon is a modular composition system that exposes one stable public Agent-facing Gateway while preserving independent natural owners for execution, continuity, cognition, platform substrate, reusable capabilities, domain semantics, scientific studies, and external providers.

It is **not** a universal control plane, universal workflow engine, universal registry, or universal domain model.

## Component taxonomy

| Component | Primary responsibility | Truth boundary |
| --- | --- | --- |
| Gateway | Stable northbound ABI, routing, compatibility, owner-derived projection | Non-authoritative; owns no Runtime/Host/domain truth |
| MCP | Agent-to-capability protocol | Protocol semantics only; not an Ordivon ontology |
| Agent Plugin | Portable package/composition boundary | Owns package bytes only; not component semantics |
| Agent Skill | Procedural knowledge / HOW | Advisory content; grants no execution or permission authority |
| Service | Deployment/process form | Deployment lifecycle only unless the service is also a named natural owner |
| Platform | Reusable substrate | Substrate realization/evidence, not workload semantic success |
| Capability | Reusable ability | Capability-specific correctness, not consuming-domain verdict |
| Domain | Bounded semantic context | Domain meaning, rules, and semantic success |
| App | Human/product composition surface | UX/session/use-case composition, not lower-owner truth |
| Study | Scientific authority | Protocol/data/result lineage for that study |
| External owner | Mature provider/standard authority | Provider-native truth retained externally |
| Repo mechanics | Monorepo integration/CI/navigation | Repository mechanics only |

## Composition laws

1. The default public Agent ingress is Gateway MCP.
2. Every material claim has one canonical truth owner.
3. Gateway is a rebuildable router/projection and never a semantic source of truth.
4. MCP is a protocol, not a domain or capability ontology.
5. Agent Plugin packages components but never becomes their semantic owner.
6. Agent Skill teaches procedure but never authorizes effects.
7. Domain owns semantic success.
8. Capability owns reusable ability, not consuming-domain outcome.
9. Platform owns substrate, not workload meaning.
10. App owns experience/use-case composition, not lower-owner truth.
11. Prefer mature external natural owners over local reimplementation.
12. Every cross-owner edge must be explicit and contract-bounded.

## Allowed default direction

```text
Agent Client
  ├── Agent Skills
  └── Agent Plugin
        └── Gateway MCP
              └── explicit owner adapters
                    ├── Runtime
                    ├── Host
                    └── future natural owners

Domains consume Platforms / Capabilities / Services / External Providers.
Apps compose user-facing use cases over explicit owner contracts.
Studies retain independent scientific authority.
```

## Forbidden architecture growth

The following are not part of the target architecture unless this contract is explicitly superseded by evidence:

- Gateway database;
- Gateway Task or Workflow authority;
- universal Ordivon capability registry;
- Agent Service 2.0;
- rich private Agent Plugin component schema;
- Skill authorization or permission authority;
- root shared dependency/workspace model that erases owner isolation;
- universal proxying of third-party MCPs without Ordivon-added semantics.

## Public/private MCP rule

The public default is one Gateway MCP endpoint. Runtime, Host, Harness, Skills compatibility, and future owner MCP servers may remain private/operator/internal surfaces. "One Gateway" therefore means one default public semantic waist, not one MCP server in the entire system.

Direct third-party MCPs should remain direct when Ordivon adds no irreducible routing, policy, normalization, verification, or composition value.

## Agent Plugin rule

Portable Agent Plugin composition remains upstream-standard:

```text
plugin.json
[skills/]
[mcp.json]
```

No third portable Ordivon component type is added locally. Selected Skills may be composed from canonical `.agents/skills`; bundling never transfers Skill ownership.

## Skill rule

Canonical project Skills remain under standard `.agents/skills`. Project visibility is scoped. The remote Skills MCP is compatibility projection only and may be retired per consumer when native Skill consumption is available.

## Router distinction

The **Method Router** and **Capability Router** are distinct by design:

- Method Router is the Agent Skill at `.agents/skills/method-router/SKILL.md`; it advises **how** to approach a problem and owns no execution authority.
- Capability Router is the Gateway static projection at `services/gateway/src/ordivon_gateway/routes.py`; it selects **which natural owner** serves an already-named capability and owns no method/planning semantics.

Current Gateway routes cover Linux/Windows execution, external continuity, and Runtime Artifact reads. Harness remains an independent owner and is not currently a Gateway-routed capability.

## Gateway admission rule

A new public Gateway capability is admitted only when all are true:

1. a real external Agent consumer exists;
2. a stable Ordivon semantic ABI adds value;
3. direct natural-owner access is insufficient or intentionally hidden;
4. Gateway adds routing, compatibility, policy, or projection value;
5. owner truth remains outside Gateway.

## Verification rule

Architecture documentation does not prove implementation conformance. The machine-readable LEGO graph and repository checks provide mechanical regression gates; owner-native tests and live end-to-end evidence remain required for implementation acceptance.


## LEGO 2.1 mathematical kernel (method, not new authority)

**Status:** proposed representation profile over current natural-owner contracts.
This is NOT a new deployed LEGO version, runtime registry, scheduler, or
authorization grant.

For a bounded real consumer X:

    LEGO_X = (Owner, Input, Output, Assumption, Guarantee,
              State, Transition, Effect, Dependencies, Verification)

Use only coordinates required to choose, verify, replace, or retire that LEGO.
Unknown consumers and unverified equivalence are UNKNOWN, not UNUSED.

Mature operators used instead of new algorithms:

- Types/constraints: existing Rust type checks and JSON Schema Draft 2020-12.
- Dependency partial order: Python graphlib.TopologicalSorter for finite
  declared DAGs, and reachability-antichain tests for parallel starts. Other
  DATA/OBSERVATION/state-machine graphs may contain cycles.
- Assume/guarantee: the producer's tested guarantee discharges the specific
  consumer assumption at each explicit cross-owner edge. Matching fields
  or path names alone do not constitute proof.
- State: current bounded Runtime TLA+ and owner-native replay/fault injection.
  Physical completion is not automatically semantic success.
- Substitution: retain consumer-observable effects and failure semantics
  in the specified context, or report UNKNOWN instead of deleting.

| Owner | Owned truth | Mature native verifier | Not implied |
| --- | --- | --- | --- |
| Runtime | Workspace, Job, Attempt, Artifact, effect commit | Rust types, lifecycle tests, bounded TLA+ | Domain success |
| Host | Continuity, checkpoint, handoff | owner contracts, durable state | Runtime execution result |
| Harness | Bounded Run, tool/model trajectory | run/tool contracts, replay, traces | Host Task authority |
| Network | Substrate, measured route/egress | scoped provider and protocol tests | Credential/domain success |

This root architecture graph is a read-only projection, not a universal
LEGO registry or proof of four separate Owner models. Host R3 intentionally
stores retained/retired laws rather than inventing a dependency DAG.
