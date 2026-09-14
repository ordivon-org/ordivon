# Creative Preservation final engineering closeout R10

Date: 2026-09-14

## Decision

Preservation is closed as an active Ordivon subsystem-development track. It remains a standard-native capability package that can be invoked by real workloads.

This closeout is not an NDSA/DPC/CoreTrustSeal maturity score or repository certification.

## Active boundary

Ordivon retains only domain selection, exact-byte resolution, external profile/provider selection, and independent outcome verification.

The same owner-authoritative bytes may be used through two mature external/provider-native views:

- interoperable submission: E-ARK SIP 2.2.0 + Commons-IP 2.11.3;
- current local preservation: Archivematica 1.18 provider-native `standardTransfer`.

No E-ARK-to-Archivematica private converter is required or permitted without a concrete workload/substitution failure.

## Operational closure

The last current defect was boot continuity. Archivematica's Compose services had no restart policy even though the Fixity timer was persistent. R10 moved all nine services to Compose-native `restart: unless-stopped` and versioned the exact overlay in `workstation-lab/config/archivematica-preservation-r10.compose.yml`.

A Docker daemon restart then proved:

- 9/9 services automatically return;
- Dashboard and Storage Service recover;
- both accepted AIPs pass fresh local fixity;
- the accepted `unar` compatibility override survives;
- the systemd Fixity timer remains waiting;
- a Fixity service run after daemon restart succeeds.

## Non-blocking boundaries / reopen triggers

Do not reopen for architecture completeness. Reopen only for a real requirement:

- independent/off-site failure domain;
- formal NDSA/DPC/CoreTrustSeal assessment/certification;
- recurring unattended multi-SIP ingest or durable preservation decisions -> evaluate Enduro first;
- upstream/provider upgrade -> rerun frozen corpus and Delta+BZip2 recovery regression;
- pointer-schema provider fix/revalidation;
- actual need for direct E-ARK ingestion into the selected preservation engine.

Until one of these occurs, further Preservation-specific construction is over-engineering.
