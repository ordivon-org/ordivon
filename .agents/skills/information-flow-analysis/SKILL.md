---
name: information-flow-analysis
description: "Apply information-flow and noninterference reasoning to a system when sensitive, trusted, untrusted, private, or authority-relevant information crosses components. Trace sources, transformations, stores, observers, sinks, declassification/release points, and prohibited influence. Use for credentials, prompts/context, logs, artifacts, telemetry, model/tool boundaries, multi-tenant systems, and security/privacy review. Do not confuse data visibility with execution authority or claim side-channel freedom without a formal model."
compatibility: Cross-platform. Produces information-flow/security analysis evidence; it is not a complete formal noninterference proof.
metadata:
  source-authority: information-flow security / noninterference
---

# Information Flow

Use this method when the architecture question is "what information can influence or be observed where?"

## Procedure

1. Define the protected information and the observer/adversary model.
2. Identify information sources:
   - secrets/credentials;
   - private data;
   - untrusted webpage/input content;
   - privileged internal state;
   - provenance/evidence metadata.
3. Identify transformations, stores, channels, caches, logs, prompts, artifacts, and sinks.
4. Label flows using project-native classes; simple examples are SECRET/PUBLIC or TRUSTED/UNTRUSTED, but do not impose a universal lattice.
5. Separate:
   - information flow;
   - control flow;
   - authority/delegation;
   - physical effect.
6. Mark intentional declassification/release points and who owns that decision.
7. Apply a noninterference-style question:
   - if protected/high input changes while permitted low/public inputs remain fixed, can an unauthorized observer's visible output change?
8. Inspect implicit flows:
   - branching/control decisions;
   - error messages;
   - timing/cadence;
   - identifiers/digests/metadata;
   - retries and side effects.
9. Check persistent traces:
   - database rows;
   - logs;
   - repr/debug output;
   - crash reports;
   - telemetry;
   - artifacts;
   - model context.
10. Define negative tests that prove sensitive material is absent from prohibited sinks, while preserving evidence that allowed release occurred.

## Candidate-channel qualification (CEGAR, on demand)

For cross-Agent or cross-run isolation, first project only **evidenced** `can_influence(A,R)` and `can_observe(B,R)` edges from natural-owner source, traces, and policy. The join `A -> R -> B` is a **candidate**, not a proven communication channel, privacy breach, or permission to communicate. Keep unknown edges explicitly UNKNOWN; cover stored, timing, resource-contention, control-plane, and persistent memory/training carriers only where the observer model justifies them.

Declare the protected high input H, permitted low inputs L, observer B's observation function Obs_B, authorized release/declassification D, and schedule/termination assumptions. A noninterference-style obligation compares **two executions** with the same permitted low context and different H, not merely one trace or absence of a network edge:

`LowEq(s1,s2) and SameAllowedContext(s1,s2) => Obs_B(run(s1)) == Obs_B(run(s2))`, modulo explicitly owner-authorized release D.

Use **counterexample-guided abstraction refinement (CEGAR)** only when the question has concrete model/test consumers:

1. Construct a conservative candidate graph/model tied to source revision and observer/policy scope. Check the encoded obligation using an existing owner-approved model checker or a bounded synthetic finite oracle.
2. For an abstract counterexample, require a **concrete, authorized, source-bound witness**. A path that cannot be realized is SPURIOUS, not a leak; refine only the false assumption, edge, state, or observation and recheck.
3. If the witnessed observation differs without authorized release, report the exact violated property and effect boundary to the natural owner. If concretization is unavailable, record UNKNOWN; never call absence of a witness PASS.
4. Separate this confidentiality check from integrity and authority: `PeerMessage : Data`, not `AuthorityGrant`; executable effects require independent owner-validated principal, scope, action, freshness, and provenance. A model's claimed authorization is not an actual grant.
5. Keep real isolation, cache/timing, network, and cross-tenant channel experiments outside task-local testing; use wholly synthetic states and independent consumer-level validation. Do not improve unauthorized covert communications or bypass observability.

Evidence qualification must name the encoded predicate, verifier guarantees, threat model, source/currentness, assumptions, accepted declassification, and any bridge to a real consumer property. A bounded solver PASS establishes its **model-scoped obligation only**. No guarantee of physical side-channel freedom, general protocol impossibility, or automatic authority isolation follows.

Mature references: Goguen–Meseguer noninterference; Clarkson–Schneider *Hyperproperties* (IEEE CSF 2008); Clarke et al. *Counterexample-Guided Abstraction Refinement* (CAV 2000); Ordivon `recursive-lego-calculus/references/formal-model.md`. Reuse the existing Method Router/owner checkers rather than introducing an InformationFlow registry, monitor, or separate execution service.

## Output

Produce:
- information-source inventory;
- observer/sink model;
- allowed/prohibited flow graph;
- declassification points;
- implicit-flow and persistence risks;
- negative leakage tests;
- unresolved side-channel assumptions.

## Promotion law

Promote only stable information-boundary, redaction, declassification, or storage/telemetry constraints that belong to the architecture and have a testable enforcement point.

## Non-claims

- Confidentiality does not imply integrity or authorization.
- No visible secret in one log does not prove noninterference.
- Data-flow diagrams do not prove absence of timing, resource, or covert channels.
- Information access does not equal permission to perform an effect.
- Cryptographic hashes may still carry sensitive linkage/provenance information depending on context.

## Stop condition

Stop when protected sources, permitted releases, prohibited sinks, and enforcement/tests are explicit enough to resolve the current design question.

Canonical external foundation:
- Information-flow security and Goguen-Meseguer-style noninterference; Cornell systems-security treatment.

Canonical local reference:
- docs/LEGO_THEORY_WAVE2_R1.md
