# Bridge to Ordivon Security v2

## Existing owner truth

Production Security already owns:

```text
S01 SubjectIdentity
 -> S02 ProviderEvidence
 -> S03 Applicability
 -> S04 PolicyDecision
 -> S05 StandingProjection
```

as documented by `platform/security/planning/lego-plan-r1.json`.

The Red-Team Foundry must not create a second production security authority.

## Study-to-production flow

```text
AI Red-Team Foundry
   |
   |  provider-native attack/eval artifact
   |  + digest-bound Finding projection
   v
Security S02 ProviderEvidence
   |
Security S03 Applicability / freshness
   |
Security S04 policy / acceptance owner
   |
Security S05 standing
```

A Foundry result can therefore say:

`experimental finding reproduced under ThreatModel X against Target Y`

but cannot by itself say:

`production system is secure` or `production system is compromised`.

## Subject identity

Future production ingestion should bind a red-team finding to the exact evaluated subject:

- model provider/version;
- system/developer instruction bytes or digest when available;
- Harness revision/configuration;
- Tool schema/capability grant;
- monitor/classifier versions;
- simulated or real environment version;
- attack provider/version;
- judge provider/version.

Changing any security-relevant component may invalidate the finding's current applicability without deleting
its historical evidence.

## Threat-model ownership

Security v2 already has a canonical machine-readable threat model using the OWASP Threat Model Library and a
source-binding currentness mechanism. The Foundry's small `ThreatModel` dataclass is only an experiment
profile used to bind attacker knowledge/access/budget. It must eventually reference, not replace, the
production threat-model authority.

## Prompt injection and authority

`platform/security/docs/AGENT-ADMISSION-V0.md` already states the architecture-level invariant required here:
prompt injection may influence model intent/output but must not expand granted capability. Therefore the most
valuable production red-team tests are not merely `did the model say forbidden text?`; they are:

- did untrusted content gain instruction authority?
- did cognition gain effect authority?
- did a Tool result bypass effect admission?
- did sensitive information cross an unauthorized channel?
- did memory persistence promote untrusted content into a higher-trust future context?

These are better aligned with Ordivon's existing authority/evidence architecture than a generic jailbreak
score alone.


## Evidence boundary reuse

`docs/architecture/EVIDENCE_BOUNDARY_CENSUS_R1.md` is already authoritative for the cross-owner mechanical
waist: Ordivon must reuse owner/subject identity, revision/digest, currentness/applicability, evidence refs,
support scope, limitations/non-claims, verifier owner, and standing rather than inventing one universal
Evidence schema/database.

Accordingly, this study keeps provider-native artifacts intact and projects `ProviderArtifactRef` only onto
Security v2's existing mechanical `EvidenceRef` shape (`provider`, `format`, `path`, `sha256`, `byte_length`).
The provider-specific outcome, score, attack family, and interpretation stay in the study/provider projection;
they are not smuggled into the mechanical evidence waist as universal semantics.

The first production integration, if later admitted, should therefore be a narrow seam adapter into S02
ProviderEvidence with explicit limitations. It should not move the Foundry under `platform/security`, and it
should not make `Finding` a new production truth object.
