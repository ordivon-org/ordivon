# Ordivon Social Fabric Signaling Specificity R3

Truth role: successor projection over historical R2 signal cuts. R2 evidence remains immutable. This layer owns no transport, routing authority, policy, scheduling, lease, security verdict, or EffectAuthority.

## SIG30 — semantic scope and propagation are separate

R2 `ordivonscope` mixed visibility/routing ideas into one field. R3 does not rewrite it; it retains it only as `legacyVisibilityScope`. Every R3 event requires explicit `semanticScope` and `propagationMode`. There is no inference from the legacy field.

Propagation modes are categorical social-visibility semantics: `self`, `direct`, `local`, `broadcast`, `environmental`. They do not cause network delivery.

## SIG31 — compartment/context

Each event carries explicit `compartmentRefs` built from existing references such as domain/resource/task/workspace identifiers. A compartment is a projection and filtering context, not a registry, ACL, process namespace, or broker topic. Broad propagation does not erase the original compartment.

## SIG32 — receptor boundary

R3 receptors remain deterministic interest filters over a fixed set of fields: event type, semantic-scope prefixes, propagation modes, compartment prefixes, subject prefixes, source, age, and evidence presence. Unknown receptor fields fail closed. There is deliberately no expression language, negation, score, weight, threshold, policy, vote, readiness rule, or arbitrary predicate DSL; complex decision logic remains OPA/owner-owned.

## SIG33 — anomaly origin

`anomalyOrigin` is optional and legal only for damage signals. Allowed values are `endogenous`, `exogenous`, `unknown`, and any supplied value requires an explicit `originSourceRef`. The projection preserves the owner-supplied description only; it cannot infer threat, maliciousness, root cause, or security class. The VHD historical dogfood uses `unknown`.

## SIG34 — attention adaptation measurement

The repository contained repeated copies of the same finding IDs across current/attention/reconciliation files. R3 therefore measures recurrence by independent source horizon, not by file count.

Current evidence:

- raw rendered documents: 5;
- independent horizons after source-digest collapse: 2;
- duplicate views collapsed: 3;
- findings in the R1 02:57 horizon: 3;
- findings in the R2 04:32:40 horizon: 3;
- stable finding IDs recurring across distinct horizons: 0.

Standing: `INSUFFICIENT_LONGITUDINAL_EVIDENCE_HOLD`. No refractory/adaptation implementation is authorized. A shared finding code is not treated as the same stimulus identity.

## VHD dogfood

The historical VHD cut now projects orthogonal semantics:

- compact/restart candidates: `maintenance:wsl-vhd`, `local`, compartments `domain:workstation` + VHD resource;
- DiskPart RPC damage: same semantic scope, `environmental`, same compartments, anomaly origin `unknown`;
- D-drive pressure: `workstation:storage-pressure`, `broadcast`, workstation + drive compartments.

The two simple receptors reproduce the intended 4 maintenance/damage matches and 1 storage-pressure match without using legacy `system` scope for R3 matching.

## Stop rules

1. Never infer R3 semantics from legacy `ordivonscope`.
2. Compartment is not a mutable registry or transport/authorization boundary.
3. Propagation mode does not itself deliver a message.
4. Receptors stay simple filters; policy/readiness belongs elsewhere.
5. Anomaly origin is owner-supplied evidence only, not threat/root-cause inference.
6. Duplicate renderings of one cut never count as repeated stimulation.
7. Attention adaptation stays HOLD until stable finding identity recurs across independent horizons and a separate promotion review authorizes behavior.
