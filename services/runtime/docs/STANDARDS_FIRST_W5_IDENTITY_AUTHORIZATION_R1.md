# Standards-First W5 — Identity / Authorization / Policy R1

Date: 2026-09-19
Status: FIRST_DELETE_DUPLICATE_SLICE

## Decision

Ordivon will not own a universal identity/authorization ontology.

The removed Runtime shadow-authority stack had no production enforcement role and combined
separate security concerns into one data structure. That is now prohibited.

## Ownership map

| Concern | Preferred owner |
|---|---|
| workload identity | SPIFFE/SPIRE when required |
| delegated HTTP authorization | OAuth + current security BCPs |
| policy decision | OPA or another explicit PDP |
| policy enforcement | the natural PEP at the effect boundary |
| Linux/Windows execution privilege | Runtime provider/OS contract |
| resource conflict/concurrency | resource/execution coordinator |
| domain semantic ownership | bounded context/domain owner |
| budget | budget/resource owner |
| telemetry | OpenTelemetry-compatible path where adopted |
| evidence/provenance | their standards-first owners |

## Deleted local model

Removed from Runtime SPI/MCP:
- AuthorityEnforcement;
- AuthorityVector;
- AuthorityLease;
- AuthorityEffectCandidate;
- AuthorityConflictClassification;
- AuthorityShadowDecision;
- evaluate_authority_shadow;
- request-to-shadow-authority projection;
- authority-shadow JSONL telemetry;
- production/test ServerConfig shadow lease state.

This deletion does not reduce actual Runtime authorization because this model never enforced
admission and production always configured an empty lease set.

## Retained local mechanics

ExecutionProfile and WindowsAuthority remain because they select concrete provider/OS
execution mechanics and are verified at Runtime's physical boundary. They are not a
replacement for OAuth, SPIFFE, OPA or domain authorization.

AuthorityMode and ConflictMode remain temporarily only because the provider-health
proposal contract still references them. They are not accepted as a general authorization
model; reassess in a later controller-contract slice.

## Compatibility caveat

NodeDescriptor.trustDomain currently remains as a descriptive local string for compatibility.
It is explicitly not a SPIFFE trust domain, SVID, trust bundle, or cryptographic identity
claim. A later slice should rename or remove it unless a real SPIFFE deployment gives the
field standard semantics.

## Gate

Any future authorization feature must identify:
1. authenticated identity source;
2. authorization policy owner/PDP;
3. enforcement point/PEP;
4. resource/effect being authorized;
5. replay/revocation semantics;
6. why OAuth/SPIFFE/OPA/provider-native controls are insufficient.

Package presence, model intent, capability visibility, network location, and semantic ownership
must never be treated as implicit authorization.
