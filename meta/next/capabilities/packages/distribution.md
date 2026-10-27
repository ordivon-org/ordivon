# Package profile: Distribution

Source: /root/projects/ordivon/capabilities/distribution

## Outcome and actual consumer

A delivery task needs an exact destination/account/payload and provider-owned
evidence of its result. Provider-native APIs/CLIs and IAM/OAuth are the default.
No generic Ordivon distribution engine gap is established.

The retained local cross-owner consumer is Workstation's n8n acceptance, which
reads the R7 Artifact fixture as a negative input and constructs a synthetic
blocked CloudEvent. Its separate positive branch performs GitHub GET/readback.
It does not use a Distribution admission engine or authorize publication.

The former custom approval, EffectAuthority, admission and reconciliation stack
had only its own synthetic tests and is retired. Historical provider receipts
and optional external-tool probes do not establish current delivery readiness.

## Task-local acceptance

Use the actual provider's authorization and effect identity, retain exact
payload/account binding, and obtain authoritative readback. Reconcile ambiguous
outcomes before retry unless native provider idempotency or absence evidence
makes the retry safe. Select Runtime/workflow/integration capabilities only when
the concrete task requires them.

External reference: OCI Distribution Specification for a real OCI registry use
case: https://github.com/opencontainers/distribution-spec/blob/main/spec.md
