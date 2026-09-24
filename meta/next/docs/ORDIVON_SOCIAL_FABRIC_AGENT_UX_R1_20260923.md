# Ordivon Social Fabric Agent UX R1 — 2026-09-23

Status: **WAVE 5 CANDIDATE / COMPOSITION-ONLY**

## Contract

An Agent should not consume the historical R1/R2/R3 implementation layers directly. The stable social UX is four orthogonal questions:

- `CURRENT` — what bounded owner projections currently say, including explicit freshness conflict/unknown and source horizons.
- `ATTENTION` — which owner-derived findings or Host re-entry deltas exist, grouped by source and never ranked.
- `COORDINATION` — which shadow candidates, inhibitions/conflicts, compartments, receptor deliveries, and Task re-entry coordinates exist.
- `AUTHORITY` — where natural owner/verifier/effect-owner bindings can be found; navigation only, never authorization.

## Progressive disclosure

Compact mode exposes counts, stable references, owner bindings, and source digests. Detail mode exposes exact evidence/source references and owner-native rows. Both modes bind the same `sourceSetDigest`; they are two presentations of the same bounded inputs, not different truth states.

## Visibility

`--compartment-prefix` filters only signaling presentation. It does not change Candidate standing, Host Task navigation, owner bindings, ACLs, credentials, policy, or EffectAuthority. The output carries `presentationFilterOnly=true`, `authorizationEffect=false`, and `aclEffect=false`.

## Observation horizons

The compiler never assumes all inputs are a same-cut snapshot. Every view exposes source horizons and `coherentObservationHorizon`. Mixed historical/live dogfood therefore remains visibly mixed rather than being laundered into one synthetic current instant.

## Explicit non-ownership

Agent UX owns no database, scheduler, lease, admission, priority, ranking, winner selection, causal inference, or effect authorization. Host, Runtime, Git, Security, verification owners, and domain owners retain their established authority.

## Social Preflight

`UX55 SocialPreflight` remains held until the four views are dogfooded. Preflight may later decide whether a social read is *recommended* for explicitly durable/shared/effectful/scarce work; it may not allow or deny execution.
