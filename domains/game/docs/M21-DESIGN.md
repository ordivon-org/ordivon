# M2.1 — goal-directed strategy semantics

## Problem

M2 proved Host authority, persistence, admission, verification, replay, and Provider interchangeability. Its three live runs nevertheless failed because the Operation frontier described local post-action state without expressing whether an action advanced or regressed the terminal rescue Goal.

The failure was not that models selected invented or stale actions. They selected legal Operations that were locally non-terminal but globally poor: disabling already-satisfied prerequisites, keeping cooling powered through long Skills after heat was already controlled, or sending distress before the remaining victory requirements were achievable.

## Design

M2.1 adds transparent semantic analysis to every canonical Context and Operation Candidate.

### Goal dependency graph

The Context names eight terminal victory requirements:

- cooling operational;
- hull breach sealed;
- life support operational;
- life support powered;
- crew stabilized;
- distress sent;
- oxygen at least 35%;
- reactor heat at most 80%.

Communications operational and powered are explicit prerequisites for distress transmission. After distress is sent, those prerequisites no longer need to remain satisfied.

### Threat horizons

The Host derives finite Tick horizons for reactor meltdown, station asphyxiation, crew loss, Engineer incapacitation, battery exhaustion, and mission timeout. These are projections under the current unchanged control state, not claims that the world will remain unchanged.

### Candidate semantics

Each Operation exposes newly satisfied requirements, persistent requirements regressed, threats improved or worsened, urgent mitigation prerequisites advanced, battery consumed, projected power draw, an optimistic primitive-step lower bound, remaining Tick slack, a transparent strategic score and rank, and whether it projects victory, failure, or time infeasibility.

Oxygen and reactor thresholds are dynamic safety conditions. Temporarily crossing one is not mislabeled as irreversible structural regression; projected threat and remaining-requirement fields carry that information instead.

### Safe control semantics

Power-off Operations are not removed globally.

Cooling shutdown is marked advantageous only when current reactor heat plus six degrees per optimistic remaining Goal step still stays at or below the victory threshold. Communications shutdown is advantageous after distress has already been transmitted. Life-support shutdown before victory remains an explicit Goal regression.

### Bounded lookahead

The frontier performs exactly one additional strategic expansion for each Candidate. It reports whether the Candidate enables a projected-victory Operation on the next decision and identifies the preferred next Candidate under the same public score.

This is not full state-space search, a retained plan, or automatic execution. The initial full-search prototype exceeded 20,000 nodes and one minute, so it was rejected as incompatible with a thin low-latency Host.

## Decision policy

The Context asks a Provider to apply these rules in order:

1. choose a projected-victory Operation immediately;
2. avoid immediate failure or lower-bound time infeasibility while a feasible alternative exists;
3. preserve satisfied victory requirements and active distress prerequisites;
4. address the shortest active threat horizon;
5. use strategic rank as the transparent default, deviating only for a concrete reason present in the Context.

Rank is advisory. Admission still accepts any exact current Candidate selected by the Provider. No Fixture, hidden policy, or scripted correction replaces a valid model Decision.

## Compatibility

- World rules and frozen M1/M2 digests are unchanged.
- The original Fixture recovery policy still wins in 25 Ticks with the frozen digest.
- A rank-one semantic baseline, without Fixture or model calls, follows a different route and wins in 26 Ticks.
- Context schema is version 2 and remains capped at 16 KiB. Recent Facts are trimmed before Goal semantics or Candidate semantics.
- Old persisted Context Artifacts remain readable by digest; new Attempts write `agent-context-v2`.
