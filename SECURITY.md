# Security Policy

## Privately report a vulnerability

**Do not** disclose exploit details, credentials, private records, or a proof of concept in a public GitHub issue, pull request, or discussion.

Use the repository's [GitHub private vulnerability reporting](https://github.com/ordivon-org/ordivon/security/advisories/new). This channel was verified as enabled on 2026-11-02.

Include the affected exact commit/release, component and public surface, reproduction conditions, observed versus expected authority boundary, security impact, and relevant redacted evidence. For vulnerabilities affecting Runtime or Harness, also consult their local `SECURITY.md` for owner-specific threat models; those files may describe historical standalone release channels.

## Scope and support

Report issues affecting current maintained source, deployed components, extensions, dependency supply chains, and retained state still reachable through current migration, recovery, or rollback. Do not assume a model proof or green CI validates an installed service's security state. The maintainer will determine remediation, supported versions and disclosure timing in the private advisory rather than promising an unverified response SLA.

For investigations and fixes: preserve exact SourceCut, trusted authority boundary, dependency versions and redacted failure receipts. Rotate exposed credentials through their natural owner; never commit secret material or copy production state into test fixtures.
