# DW09 Compromise / Persistence / Recovery Projection R1

Status: task-local Security projection over the existing Incident Case Profile R1. No incident
service, detector platform, auto-containment controller or recovery engine is introduced.

## Purpose

DW09 keeps the compromise/recovery branch independent from protection:

```text
verified protection != compromise absence != eradication != recovery
```

Inputs are exact owner-native signals, detector-coverage evidence, owner-authored recovery
obligations and fresh requalification evidence.

## Detector coverage semantics

For each dimension (COMPROMISE, PERSISTENCE):

- a current adverse owner signal => CONFIRMED;
- historical adverse evidence => HISTORICAL_ADVERSE_REQUIRES_CURRENT_INVESTIGATION;
- no adverse signal + COMPLETE bounded detector coverage =>
  NO_*_OBSERVED_COMPLETE_COVERAGE;
- otherwise => UNKNOWN.

Even COMPLETE bounded negative evidence never emits global compromise absence.

## Recovery semantics

DW09 does not invent a universal remediation checklist. Natural owners explicitly provide
required obligations. R1 supports owner-authored classes including credential rotation, key
rotation, persistence removal, rebuild, containment release and requalification.

RECOVERY_VERIFIED requires:

1. a current adverse compromise/persistence standing;
2. every required owner-authored obligation SATISFIED; and
3. a fresh/current owner-native requalification standing SATISFIED.

A recovery action or old requalification receipt cannot self-certify recovery.

## Composition boundary

The DW06->DW09 Composition Gate is an admission seam only. SATISFIED means the exact bounded
case/subject evidence was admitted to the DW09 projection. It does not establish compromise
absence, eradication, recovery, protection or domain acceptance.

## Historical Exchange replay

The ProxyLogon replay carries the existing high-level ATT&CK T1505.003 web-shell persistence
reference as HISTORICAL_NOT_CURRENT adverse evidence. It therefore opens current investigation
uncertainty but does not claim any present Exchange host is compromised.

## Benign canary

A synthetic target with COMPLETE compromise + persistence detector coverage and no adverse
signal demonstrates bounded negative semantics. It still keeps global compromise absence false.

## Recovery canary

A synthetic current incident demonstrates credential rotation, key rotation, rebuild and
requalification obligations. The canary is mechanics-only and establishes no production
recovery truth.
