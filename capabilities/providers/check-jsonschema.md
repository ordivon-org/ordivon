# Provider: check-jsonschema

- Upstream: `python-jsonschema/check-jsonschema`
- Installed version: `0.38.0`
- Role: standards-native JSON Schema instance validation
- Installation carrier: `uv tool`
- Local standing: **AVAILABLE / R2 PROJECTION VALIDATION PASS**

## Boundary

`check-jsonschema` validates instances against JSON Schema. It does not define the schema, own domain semantics, decide authority applicability, establish compliance, or replace domain validators.

R2 uses it only for the thin `standard-native-profile-projection-v1` bridge. Research, Runtime and Game remain the semantic owners of their profiles and verdict vocabularies.

## Local acceptance

The validator successfully checked the three R2 projections against:

```text
schemas/standard-native-profile-projection-v1.schema.json
```

The three instances were generated read-only from the current Research, Runtime and Game standard-native profiles.

## Forward rule

Prefer this mature validator over adding a custom JSON Schema implementation. Pin the tool when reproducible validation matters. Replace it if another mature validator provides a materially better fit; the JSON Schema contract remains provider-independent.
