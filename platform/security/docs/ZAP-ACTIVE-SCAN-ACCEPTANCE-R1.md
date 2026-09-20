# OWASP ZAP authorized active-scan acceptance R1

Date: 2026-09-12
Standing: `AUTHORIZED_ACTIVE_SCAN_VERIFIED` for the exact local acceptance profile only.

## Provider

OWASP ZAP `2.17.0` was acquired from the official GitHub release. The Linux archive SHA-256 was verified against the published release value:

`efe799aaa3627db683b43f00c9c210aea0b75c00cc8f0a0f0434d12bb3ddde5a`

ZAP remains an external provider. This acceptance does not install it into Workstation and does not make ZAP an authority owner.

## Authority fence

The active scan reuses `policies/effect_admission.rego`; no DAST-specific authorization service was created.

The admitted request is bound to:

- actor: `actor:security-operator`;
- authority: `security-authority:zap-local-r1`;
- exact zone/target: `http://127.0.0.1:18080`;
- capability: `security.active_scan`;
- effect type: `owasp-zap.active-scan`.

A reachable target or available credential is not sufficient to run the active scan.

## Bounded target and scan

The target is an ephemeral loopback-only Python fixture owned by this acceptance. It deliberately reflects the `q` query parameter without escaping.

The ZAP Automation Framework plan:

- spiders only the exact local context;
- disables all active-scan rules by default;
- enables only rule `40012` (Reflected XSS) at Low threshold/strength;
- emits a provider-native `traditional-json` report;
- uses an isolated ZAP home and bounded 150-second execution window;
- kills the target process on exit.

## Observed R1 result

The successful acceptance run observed:

- OPA decision: `admitted=true`;
- spider URLs: 5;
- HTTP requests observed by the owned target: 12;
- ZAP report version: `2.17.0`;
- sites: 1;
- active acceptance alert: exactly one rule `40012`, `Cross Site Scripting (Reflected)`, High risk / Medium confidence;
- the repo-native replay produced 5 total provider alerts because bundled passive rules also reported response/header findings; total passive-alert count is not an acceptance invariant;
- ZAP Automation Framework exit code: 0.

Retained run digests from the acceptance episode:

- admission input: `sha256:af29674dbd5cb18fa442b432e4710d3e2ef4c154302efefe4f97769a57e8923e`;
- admission decision: `sha256:8cbbefed64bf48c7f9817e0a227cb096b3e6eca38e30ab40976f3ac7c8f58924`;
- plan: `sha256:9f942a2f0d3c24ec0cf2cedf7efde771a8f1b7f3454a678c1ba719f001486673`;
- ZAP JSON report: `sha256:a126ef828131d52970122bd2cc56ca012a9252de7ce4b112d3597c61d7fb4fbb`;
- target request log: `sha256:4925f2e3d015940b0fcb329394db61dc3c38a56b9da4ab189b94f200c807b9be`.

The repo-native smoke script regenerates fresh evidence and verifies the same semantic conditions rather than treating these historical digests as current truth.

## Failures retained during acceptance

Two failed attempts were useful and were not promoted to success:

1. ZAP default proxy port 8080 was already occupied; ZAP terminated before scanning the target.
2. YAML 1.1 parsed unquoted `Off` as boolean `false`; ZAP completed a scan but returned a plan warning/exit 2. Quoting threshold/strength values produced the clean run above.

These failures are provider/configuration facts, not Security authorization failures.

## Repo-native replay

`scripts/smoke_zap_authorized_local.sh` replays the exact authority fence and bounded local scan. The first canonical replay after adding the script produced 12 target requests, exactly one rule-40012 reflected-XSS finding, and standing `AUTHORIZED_ACTIVE_SCAN_VERIFIED`. Its provider report contained four additional passive findings; these remain provider-native evidence and are deliberately not normalized into a Security-specific finding model.
