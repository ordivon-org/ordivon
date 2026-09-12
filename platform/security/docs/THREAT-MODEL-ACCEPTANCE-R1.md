# Threat model acceptance R1

Date: 2026-09-12
Standing: `TM_BOM_SCHEMA_VALID + ARCHITECTURE_BINDING_CURRENT`; Threat Dragon UI smoke remains provider-runtime follow-up.

## Canonical artifact

`threat-models/security-v2-r1.json` is the canonical machine-readable model. The authority format is the OWASP Threat Model Library JSON schema pinned to tag `v1.0.2`, not the Threat Dragon native v2 format.

Pinned external schema:

- source: `OWASP/www-project-threat-model-library` tag `v1.0.2`, `threat-model.schema.json`;
- SHA-256: `428772fecfed799921e90bb7e7acf7ce7bb8e379128e43c4e7f4346a528539be`;
- validation: `check-jsonschema==0.34.0` after digest verification.

The upstream `v1.0.2` repository currently contains an example whose `$schema` field still names `v1.0.1`; validating that example against the `v1.0.2` schema therefore fails closed until the declaration is updated. Security v2 does not weaken schema validation to accommodate that mismatch.

## Currentness binding

The model extension `ordivon.dev/security/source-binding` binds the threat model to a deterministic architecture envelope over:

- `README.md`;
- `docs/STANDARDS-BASELINE.md`;
- `docs/TECHNOLOGY-SELECTION-R2.md`.

`ordivon_security_v2.threat_model` recomputes that envelope and returns `CURRENT` only on an exact digest match. Mutating a bound architecture file makes the same model fail as stale; path traversal/escape in the binding fails closed.

This avoids a Git-commit self-reference problem: committing the model itself does not make the model stale unless the architecture inputs change.

## Threat Dragon role

Threat Dragon remains the preferred editor/viewer because the current 2.6.2 documentation supports reading/importing TM-BOM-oriented Threat Model Library models and identifies TM-BOM as the long-term primary-format direction. It is not the authority format.

A Docker-based Threat Dragon runtime smoke was attempted but Docker Hub registry access timed out on the current host. No network settings were changed for this acceptance. UI/provider-runtime acceptance remains separate from the already-closed schema/currentness contract.
