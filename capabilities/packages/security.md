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

## Active research line: browser automation dynamic defense

Agent/web automation creates a moving security-observability boundary that should be treated as a Security measurement and adaptation problem rather than a one-time browser setting.

Current external-first study: `knowledge/lessons/browser-automation-dynamic-defense-r1.md`.

The Security package should be able to support authorized laboratory workloads that produce:

- version-fenced browser/control-layer/network/profile witnesses;
- native-browser negative controls and standard-automation positive controls;
- control-attachment state (`native/unattached`, protocol-attached, WebDriver-attached, GUI/human) and transition evidence;
- cross-layer browser-identity consistency observations;
- automation-leak and detector-coverage taxonomies;
- last-known-good / first-known-bad drift records;
- time-to-detect, time-to-attribute and time-to-safe-route measurements.

Browser substrate health and security-boundary admissibility are separate states. A successful browser action, challenge interaction, or third-party detector score is not by itself Security acceptance.


## Active research line: authority, egress and effect topology

Agent Security LEGO is the current reusable security/control lens for systems with ambient authority, hidden or multiple egress planes, persistent state, delegated execution, or consequential external effects.

Canonical lens:
- `knowledge/lessons/agent-security-lego-r1.md`.

Validation:
- `knowledge/lessons/zcode-workspace-snapshot-security-lego-r1.md`;
- `knowledge/lessons/agent-security-cross-system-destroyer-r1.md`;
- `knowledge/lessons/agent-security-cross-domain-destroyer-r1.md`.

For applicable workloads, Security may derive:
- READ / WRITE / DERIVE / NETWORK / PERSIST sets;
- exact security-regime identity;
- trigger-to-effect graph;
- actuator-to-stage and policy-binding-time map;
- authority delegation/attenuation/clamping map;
- persistence-class vector;
- effect commit point and reversibility class;
- side-effect observation coverage;
- effect reconciliation oracle;
- disclosure-versus-implementation alignment.

XAS13-XAS18 are cross-domain validated analytical dimensions. They are not Agent Plugin fields, not a replacement for NIST/OWASP/provider-native controls, and not mandatory project-plan schema fields.
