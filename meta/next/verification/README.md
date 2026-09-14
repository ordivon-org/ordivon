# Verification

Verification and Validation remain domain-specific. Ordivon owns mappings and orchestration, not a universal truth engine.

A verification profile should identify:

- requirement/acceptance criterion;
- validator or evidence source;
- applicability and freshness conditions;
- required source/version/configuration identity;
- evidence produced;
- bounded verdict semantics;
- explicit claim/non-claim boundary;
- domain-owned verdict vocabulary rather than a universal Ordivon status enum;
- escalation/manual/external-authority conditions when automation is insufficient.

Keep applicability, evidence, verification, currentness, claim authority and consequence conceptually separate even if a domain chooses a compact carrier. `PINNED_NOT_LATEST`, `EXTERNAL_ASSERTION_REQUIRED`, `NOT_CLAIMED`, `DEFERRED` and similar statuses are not generic failures and must not be normalized away.

Execution success alone is never sufficient evidence of semantic completion.

See `docs/STANDARD_NATIVE_ENTERPRISE_ENVIRONMENT_R2.md` and `schemas/standard-native-profile-projection-v1.schema.json` for the thin cross-domain projection boundary.
