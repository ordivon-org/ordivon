# Distribution v1 -> v2 migration R1

## Delete candidates from `ordivon-media`

- `CURRENT_CARRIER_PROFILES`: replace with provider/Postiz/runtime discovery.
- `_EFFECT_AUTHORITY_REQUIREMENTS`: replace with provider-native authorization facts presented to policy.
- provider-specific correction windows and policy prose embedded in Python: keep at provider boundary or external policy facts.
- Python `plan_delivery()` decision tree: replace with OPA decision.

## Preserve as residual semantics

- exact occurrence binding;
- exact user authority for write/destructive effects;
- provider-native truth/read-back boundary;
- explicit statement that local success does not imply external acceptance.

## Do not migrate yet

The old implementation remains intact during R1. v2 must first prove the external composition against representative cases and then run a differential audit against the old local planner. Only behaviors justified by the residual rules may migrate. Provider catalog facts are not migration candidates merely because old tests cover them.
