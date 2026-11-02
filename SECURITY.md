# Security Policy

## Private vulnerability reports

Do not post a suspected vulnerability in a public Issue or PR.

Use the repository's [private vulnerability reporting](https://github.com/ordivon-org/ordivon/security/advisories/new).
The feature was enabled and read back on 2026-11-02. Include affected
source and installed revision, natural owner, a safe reproduction,
expected/observed authority boundaries, and possible credential or
persisted-data exposure. Never include live secrets.

## Boundaries

Gateway owns routing/authentication projections. Runtime owns physical
Job, Attempt, Workspace and Artifact truth. Harness owns its bounded
Agent Run, Provider Calls and Tool continuity. Host and domains retain
their semantic and external truth. No model output, test PASS or
execution success independently grants authority or domain completion.

Support and remediation apply to current maintained code and qualified
consumer environments; historical releases have no implied backport
commitment. Disclosure is coordinated privately.

Owner-specific policies: [Harness](services/harness/SECURITY.md),
[Runtime](services/runtime/SECURITY.md).
