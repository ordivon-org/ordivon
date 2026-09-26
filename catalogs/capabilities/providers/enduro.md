# Provider: Enduro

Status: **TRIGGERED REPLACEMENT CANDIDATE / NOT LOCALLY ACTIVE**
Role: preservation-domain durable ingest workflow provider above Archivematica/a3m.

## Current upstream observation — 2026-09-14

- project: `artefactual-sdps/enduro`;
- latest non-prerelease observed: `v0.34.1` (2026-08-28);
- tag commit: `548b0edb40fdd9456272fd5ab8950c6374da7c79`;
- Linux release asset SHA-256: `09facda565f48edf78f8a22288815359f8cdd36e3efa63519d0850e5b581887d`;
- upstream describes Enduro as under development while also reporting production use by several large cultural-heritage organizations;
- Temporal is a required durable-workflow dependency;
- upstream local-development flow is Kubernetes/Tilt oriented.

## Why it matters

Enduro was built to replace brittle Archivematica automation scripts and to provide preservation-domain durable workflow handling. It therefore overlaps directly with the remaining manual/custom orchestration steps around SIP receipt, workflow progression, retries and preservation-engine dispatch.

## Why it is not activated now

This workstation currently has no active Temporal service and no `kubectl`, Tilt, k3d, Kind or Minikube installation. The graduated Archivematica R6/R7 path already works. Deploying Enduro's complete development substrate solely for architectural cleanliness would add more infrastructure than it removes.

## Activation trigger

Activate/pilot Enduro before writing new custom preservation ingest orchestration when one of these becomes real and repeated:

- recurring unattended ingest of multiple SIPs;
- durable preservation workflow state/retry requirements beyond the current bounded path;
- multiple preservation engines or child workflows;
- operator queues/decisions that are becoming a maintained local integration surface.

At that point, compare Enduro against the existing graduated path using the same 86-file frozen corpus and the E-ARK SIP fixture. Do not build competing preservation workflow semantics in Ordivon.
