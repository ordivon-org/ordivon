# Creative Preservation Final Engineering Closeout R10

Date: 2026-09-14
Engineering status: **CLOSEOUT_COMPLETE**

This is an engineering closeout, not a preservation maturity level or repository certification.

## Current active architecture

```text
producing domain
  -> accepted output
  -> exact authoritative bytes
       |
       +-> interoperable submission when needed
       |     -> E-ARK SIP 2.2.0
       |     -> Commons-IP 2.11.3 validation
       |
       +-> local preservation execution
             -> Archivematica 1.18 provider-native standard transfer
             -> PREMIS / METS / PRONOM / AIP
             -> Storage Service
             -> fixity / replication / recovery
```

There is no custom preservation package generator, preservation receipt ontology, preservation catalog builder, private maturity model, or custom ingest workflow engine in the active forward path.

## Boot/operational continuity closure

R10 found one real closeout defect: all nine Archivematica Docker Compose services had `restart=no`. Docker itself was enabled at boot, but a machine restart could leave the periodic Fixity timer alive while Storage Service remained down.

The Compose overlay now uses `restart: unless-stopped` for all nine services. The exact live overlay is versioned as:

`config/archivematica-preservation-r10.compose.yml`

A Docker daemon restart was then executed as a reboot-proxy acceptance test. Results:

- all 9/9 Archivematica containers automatically returned;
- Storage Service returned HTTP 302;
- Dashboard returned HTTP 302 after dependency warm-up;
- master AIP fresh local fixity = PASS;
- replica AIP fresh local fixity = PASS;
- the XADMaster `unar` override remained selected with the accepted hashes;
- the periodic Fixity timer remained enabled/active/waiting;
- the Fixity service executed successfully after daemon restart.

This closes the previously unproven daemon/boot continuity of the local stack.

## Submission/intake boundary closure

R8 proved E-ARK SIP 2.2.0 + Commons-IP against the frozen 86-file corpus. R9 removed the old custom BagIt packager. R10 clarifies that no E-ARK-to-Archivematica converter is required.

Archivematica itself exposes a provider-native `standardTransfer` path for ordinary source directories; the source code defaults unknown/standard transfer types to `standardTransfer` and copies selected source-directory contents into the active transfer area. Therefore both views are derived from the same owner-authoritative bytes:

- use **E-ARK + Commons-IP** for interoperable Producer/Archive submission packages;
- use **Archivematica standard transfer** for the current local engine intake.

Do not build a private adapter merely to make the two package shapes identical.

## Historical material retained

- R1 pilot evidence;
- R4/R5 frozen bags and receipts;
- R6 Archivematica graduation evidence;
- R7 replication/recovery/fixity evidence;
- R8 E-ARK/standards migration evidence;
- R9 implementation-retirement evidence;
- frozen 12-work / 86-file V&V corpus.

Historical `ACCEPTED_BOUNDED` labels remain engineering-history statements only.

## Open boundaries that do not block closeout

These are not current implementation defects:

1. **Independent/off-site failure domain** — not required by the present local durability scope. Reopen when real durability/risk requirements demand a separate machine, object store/region, preservation network, or external repository.
2. **Formal NDSA/DPC/CoreTrustSeal assessment** — not inferred from engineering receipts. Perform only when a program/repository-level maturity or certification decision is needed.
3. **Enduro** — not active. Reopen when recurring unattended multi-SIP ingest, durable preservation decisions/retries, or multiple preservation engines make orchestration a maintained concern.
4. **Pointer XSD/Schematron conformance** — upstream validation boundary; PREMIS replication provenance exists. Recheck on provider upgrade rather than writing a private validator.
5. **XADMaster `unar` override** — temporary compatibility extension. Remove only when a future Archivematica/Storage Service runtime passes the exact Delta+BZip2 recovery regression without it.
6. **Direct E-ARK ingestion by Archivematica** — neither claimed nor required. Evaluate only if an operational need appears for one package artifact to serve both interchange and local engine intake.

## Reopen policy

Do not reopen Preservation for architectural cleanliness. Reopen only when a real workload triggers one of:

- new accepted object needs preservation;
- independent/off-site durability is required;
- repeated preservation ingest orchestration appears;
- provider upgrade changes a proven boundary;
- formal external maturity/certification assessment is requested;
- a current external provider fails on the frozen regression corpus or a new real object.

Until then, Preservation is a stable standard-native capability package, not an active subsystem-development track.
