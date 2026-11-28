# Security Policy

## Private vulnerability reports

Do not publish vulnerability details, credentials, exploit steps, confidential logs, or production state in a public Issue or pull request.

Use this repository's enabled [GitHub private vulnerability reporting](https://github.com/ordivon-org/ordivon/security/advisories/new). Specify affected commit and installed version when known, entry point, expected versus observed authority, reproducibility and effect or persisted-state impact. The maintainer will coordinate triage and any disclosure through the private advisory.

Runtime and Harness may also be distributed independently; their existing [Runtime security policy](services/runtime/SECURITY.md) and [Harness security policy](services/harness/SECURITY.md) document owner-specific trust boundaries. The reporting destination above is for this monorepo.

## Supported state and trust boundary

Security claims are scoped to exact current source and supported deployed versions, not every historical Git revision. No blanket LTS or backport promise is made. Historic data or binaries remain relevant where they are still consumed for replay, recovery or rollback.

Ordivon combines trusted-local execution, external Provider calls and persisted Agent/Host state. Runtime success is not domain completion; a model, Tool output or external caller does not acquire authority by describing itself as trusted. Explicitly identify the owner, identity/fence and state transitions relevant to a report.

Follow the relevant module's secret-handling and privacy guidance before sharing traces, runtime output, databases, artifacts or evidence.
