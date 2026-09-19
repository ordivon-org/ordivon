# ORDIVON LEGO — PROVIDER OBSERVATION R25

Date: 2026-09-19
Base: bbd95081bd87d60d022b4c95fc0cce76299908d6

## Finding

ProviderObserver is a duplicate forwarding wrapper.

Its only behavior is:
CarrierProviderAdapter.observe(placement_id)
  -> compare observation.placement_id with placement_id
  -> return observation

DesiredPlacementStore.record_observation already performs the same placement identity check before mutation.

## LEGO ownership

| LEGO | Owner | R25 |
|---|---|---|
| external placement observation | CarrierProviderAdapter | retain |
| observation/placement identity validation | DesiredPlacementStore.record_observation | retain |
| durable observed state/evidence | DesiredPlacementStore | retain |
| readiness interpretation | PlacementReconciler | retain |
| ProviderObserver | duplicate forwarding/validation wrapper | eliminate |

## Replacement flow

PlacementReconciler
  -> CarrierProviderAdapter.observe(placement.id)
  -> DesiredPlacementStore.record_observation(placement.id, observation)
  -> readiness reconciliation

## Proof obligations

1. ProviderObserver absent.
2. service.observer facade absent.
3. wrong observation.placement_id still fails before placement mutation.
4. READY/UNKNOWN transitions remain unchanged.
5. CarrierProviderAdapter remains the external observation port.
6. DesiredPlacementStore remains the identity/persistence guard.
7. no ProviderObserver replacement wrapper.
