# ORDIVON PROVIDER OBSERVER ELIMINATION R25

Date: 2026-09-19
Status: TWENTY_FIRST_PRODUCTION_DELETION
Parent: ORDIVON BIRTH COORDINATOR ELIMINATION R24

## Result

R25 removes ProviderObserver and the service.observer facade.

Provider observation now flows directly from CarrierProviderAdapter into PlacementReconciler and then through DesiredPlacementStore.record_observation.

## LEGO decomposition

external provider observation = CarrierProviderAdapter
observation identity validation = DesiredPlacementStore.record_observation
durable observation/evidence = DesiredPlacementStore
readiness interpretation = PlacementReconciler
ProviderObserver = duplicate forwarding/validation wrapper

## Duplicate validation removed

ProviderObserver previously checked:
observation.placement_id == placement_id

DesiredPlacementStore.record_observation already performs the same check before any UPDATE.

After R25 the fail-closed path is:

CarrierProviderAdapter.observe
  -> DesiredPlacementStore.record_observation
     -> reject placement identity mismatch before mutation
  -> PlacementReconciler interprets READY/UNKNOWN

## Dynamic facade cleanup

R25 also removes the obsolete observer name from every higher-revision composition forwarding list.

The first full Agent Service run exposed this hidden dynamic forwarding debt through semantics.py; after removing all stale observer propagation points, the full stack initializes correctly.

## Proof witness

A dedicated WrongPlacementCarrier returns ProviderObservation(placement_id='wrong-placement').

Observed behavior:
- PlacementReconciler raises ValueError('observation placement identity mismatch')
- DesiredPlacement.observed_state remains UNKNOWN
- DesiredPlacement.evidence_ref remains None

Therefore identity mismatch still fails before durable mutation.

## CORE_ZERO ratchet

R3 baseline: 171
R20: 152
R21: 151
R22: 151
R23: 150
R24: 149
R25: 148
cumulative retired top-level types: 23

Structural audit:
observed = 148
legacy ceiling = 148
unexpected = []
retired overlap = []
old ProviderObserver/facade = none
replacement observer wrappers = none

## Validation

R25 targeted chain: Ran 43 tests — OK
Structural gate: Ran 49 tests — OK
Agent Service suite: Ran 247 tests — OK (skipped=5)
Full repository suite: Ran 346 tests — OK (skipped=5)

## Interpretation

ProviderObserver was not an authority boundary. It duplicated a validation already enforced closer to the durable state mutation.

R25 therefore reduces one object/facade layer while strengthening ownership clarity.
