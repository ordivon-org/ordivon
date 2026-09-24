# Ordivon Social Fabric Epistemic / Constraint Boundary R1

Truth role: projection-only bridge over verification-owner standings and existing OPA commitment decisions. It owns no causal inference, policy enforcement, winner selection, execution authority, priority, lease, or EffectAuthority.

## EPI40 — sequence versus mechanism

The public standing set is intentionally small:

- `SEQUENCE_OBSERVED`: an observation owner supplies an ordered sequence with evidence. Temporal order is descriptive only.
- `MECHANISM_HYPOTHESIS`: a named hypothesis owner states a candidate mechanism; this is not causal identification.
- `MECHANISM_EVIDENCE_SUPPORTED`: an explicit verification owner supplies evidence plus an owner-native standing. Social Fabric preserves that standing and any residual open claims; it does not independently judge evidence sufficiency.

Trace links, PROV links and temporal order cannot mechanically upgrade a sequence to a supported mechanism. A supported local mechanism does not close broader causal questions.

### Dogfood

The historical VHD incident is represented twice at different epistemic ceilings: the observed restart-before-RPC-failure sequence is `SEQUENCE_OBSERVED`; the idea that service lifecycle interference contributed to DiskPart RPC unavailability remains `MECHANISM_HYPOTHESIS`. No verifier exists to upgrade it.

Browser-security R9 supplies a contrasting owner-native case: profile-restored Chromium window placement is preserved as `MECHANISM_EVIDENCE_SUPPORTED` with owner standing `PROFILE_WINDOW_PLACEMENT_ATTRIBUTED_PROVIDER_RELEVANCE_OPEN`. The projection also preserves open claims for provider relevance, historical origin of the stored placement and protected-provider challenge causality.

## EPI41 — constraint feasibility, not score

EPI41 consumes the existing R3 OPA commitment projection and maps boolean policy satisfaction into `FEASIBLE_SHADOW` / `INFEASIBLE_SHADOW`. Infeasible candidates preserve explicit unmet constraints. The following fields are fail-closed if injected into a candidate decision: `score`, `rank`, `weight`, `voteCount`, `priority`, `chemicalPotential`, `socialPressure`.

The single-candidate R3 fixture becomes one `FEASIBLE_SHADOW` candidate but `winnerSelected=false`. The historical VHD R3 fixture produces three `INFEASIBLE_SHADOW` candidates with their exact unmet constraints. Multiple feasible candidates remain a set; there is never an inferred winner or tie-break.

## Laws

1. Sequence is not mechanism.
2. Hypothesis is not identification.
3. Evidence-supported standing must name a verification owner and evidence.
4. Local mechanism support does not erase residual open causal claims.
5. Feasibility is boolean constraint satisfaction, not utility/ranking.
6. OPA satisfaction is still not enforcement or EffectAuthority.
7. Social Fabric never chooses among multiple feasible candidates.
