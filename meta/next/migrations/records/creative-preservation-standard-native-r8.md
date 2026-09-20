# Creative Preservation — standard-native replacement R8

Date: 2026-09-14

## Trigger

R6/R7 proved that mature preservation systems could generate/store/fix/replicate/recover the real frozen corpus. R8 asks a narrower question: which remaining Ordivon preservation semantics can now be deleted or demoted in favor of authoritative external standards and mature providers?

## Dispositions

| Historical/local element | Disposition | Forward owner |
| --- | --- | --- |
| `R4/R5/R6/R7` preservation maturity meaning | **DELETE as maturity ontology**; retain as engineering history | NDSA Levels 2.1 / DPC RAM v3 / CoreTrustSeal 2026–2028 |
| `ACCEPTED_BOUNDED` as preservation-program standing | **DELETE / REPLACE_STANDARD_NATIVE** | external assessment framework; no score inferred automatically |
| owner-approved output decision | **RETAIN_DOMAIN_ONLY** | producing domain |
| exact Git/CAS byte resolver | **RETAIN_DOMAIN_ONLY** | producing domain adapter |
| custom handoff/package semantics | **REPLACE_STANDARD_NATIVE** | E-ARK SIP 2.2.0 + CSIP 2.2.0 |
| custom package validation | **DELETE** | Commons-IP 2.11.3 |
| BagIt as canonical preservation model | **DEMOTE** | transport/current Archivematica engine adapter |
| R4-R7 receipt schemas | **RETAIN_HISTORICAL_EVIDENCE / DEMOTE_TO_EVIDENCE_INDEX** | provider-native PREMIS/METS/FixityLog + thin references |
| custom preservation ingest glue | **FREEZE / NO_NEW_CODE** | Enduro first candidate when repeated orchestration need appears |
| custom preservation workflow engine | **DELETE as concept** | Enduro/Temporal/provider-native workflows |
| custom pointer-validator work | **STOP** | upstream E-ARK/provider validators; historical defect evidence only |
| frozen 12-work / 86-file corpus | **RETAIN_AS_VV_FIXTURE** | local V&V asset, not production semantic authority |

## E-ARK substitution proof

One real E-ARK SIP 2.2.0 was generated and validated with Commons-IP 2.11.3. Commons-IP reported `VALID`, zero validation errors and zero failed MUST requirements. After accounting for Commons-IP's preserved source-directory prefix, all 86 source files are byte-identical and all three hidden files survive.

This is sufficient to move forward package/interchange semantics out of Ordivon.

## Enduro non-activation

Enduro v0.34.1 is registered but not installed as a live preservation workflow stack. Upstream currently uses Temporal and a Kubernetes/Tilt-oriented development environment. No repeated local workload currently justifies adding that substrate. The migration rule is workload-triggered: pilot Enduro before any new custom preservation ingest orchestration is written.

## Non-claims

- no NDSA Level is assigned;
- no DPC RAM score is assigned;
- no CoreTrustSeal certification or conformance is claimed;
- the existing Archivematica intake is not claimed to accept E-ARK SIP directly;
- historical R6/R7 evidence remains valid for what was mechanically tested.
