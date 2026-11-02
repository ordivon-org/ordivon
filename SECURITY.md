# Security policy

## Private reporting

Do **not** disclose a suspected vulnerability, exploit, secret or sensitive proof of concept in a public GitHub Issue, Discussion or pull request.

For issues affecting this Monorepo, use the repository's [private vulnerability reporting entry](https://github.com/ordivon-org/ordivon/security/advisories/new) when it is enabled. If that entry is unavailable, open a public issue **without vulnerability details** requesting a private contact channel from repository maintainers. Do not attach secrets or exploit material to that public request.

For original stand-alone source repositories, preserve the affected owner's reporting guidance where applicable: [Runtime](services/runtime/SECURITY.md) and [Harness](services/harness/SECURITY.md). These links do not imply separate Monorepo workflow execution.

A useful private report identifies the affected Git source commit, actual installed/release identity if known, entrypoint, reproducible conditions, expected and observed authority boundary, and whether credentials, persisted state, external effects, process trees or Agent/Provider inputs are involved. Evidence should be minimized and sensitive data redacted.

## Scope and evidence

The Monorepo includes separate trust and authority boundaries. Source code, CI, Formal models, a deployed binary and a current provider acceptance receipt establish different claims; one does not substitute for another. Current production qualification depends on the exact affected owner and environment. Historical deployments are relevant when they remain current recovery, rollback or migration consumers.

Security tests, CodeQL, dependency audits and secret scans are risk controls, not a guarantee of safety. Avoid assuming that a compiled or tested subsystem is an untrusted-code sandbox. Follow the applicable owner's documented isolation and execution-authority rules.

Do not publish credentials, raw runtime registries, private Agent transcripts, recovery artifacts, token-bearing environment files or user data in bug reports or CI logs.

For source-level contribution and verification procedures, see [CONTRIBUTING.md](CONTRIBUTING.md).
