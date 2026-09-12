# Package: Security

Last census: 2026-09-13
Standing: **READY_FOR_REAL_WORK**

## Outcome scope

Manage cybersecurity risk and produce evidence that relevant protective, detective, response and recovery outcomes are satisfied for the current entity of interest.

## Mature external knowledge owners

- NIST Cybersecurity Framework 2.0 for outcome-oriented cybersecurity risk management: GOVERN, IDENTIFY, PROTECT, DETECT, RESPOND, RECOVER;
- NIST Secure Software Development Framework for secure software-development practices when software production is in scope;
- OWASP, OpenSSF, platform/vendor guidance and domain/regulatory standards when they are more specific to the actual workload.

The Security package selects outcomes and evidence. It does not replace these frameworks with a private security lifecycle.

## Observed local capability

Agent/skill layer:

- `security-best-practices`;
- `security-threat-model`;
- `security-review`.

Executable/provider layer observed locally or in the existing Security provider:

- Gitleaks;
- OSV-Scanner;
- Trivy;
- Syft;
- Cosign;
- OPA/Rego;
- additional provider-owned capabilities such as Semgrep, Scorecard, ZAP/fuzzing/runtime detection where activated by the Security provider.

Provider-native evidence such as SARIF/CycloneDX should remain authoritative where applicable.

## Concrete current gaps

None are globally asserted. Security tooling is threat/risk/target dependent. Do not install every scanner, IAM system, SIEM, fuzzing framework or runtime detector in advance.

## Acceptance workload

For each real task:

`entity + threat/risk context -> applicable framework outcomes -> selected controls/tools -> evidence -> residual risk/standing`

A scan completing successfully is not security acceptance by itself.
