# Creative Preservation Operations R7 Closeout

**Standing:** `ACCEPTED_BOUNDED`

R7 graduates the **operational layer** above the R6 Archivematica AIP. The accepted path now covers native Storage Service replication, independent replica fixity, deliberate corruption detection, native AIP recovery, periodic fixity through Artefactual's Fixity client, and restart survival.

It does **not** claim an independent failure domain or off-site disaster recovery. Both accepted copies remain on the same WSL host.

## Graduated topology

```text
R6 master AIP
1593a748-703b-46b6-8114-314040f44bd8
        |
        | Archivematica Storage Service Package.replicate()
        v
RP Location f507e370-3249-4a3f-a88b-246b69ddf7d1
        |
        v
POSIX secondary store
/var/lib/ordivon/creative-preservation/r7-secondary-store
        |
        v
replica AIP
7d488fcc-c2f9-4490-a196-79885a595a1a

periodic operations:
systemd timer
    -> Artefactual Fixity 0.8.0
    -> Storage Service Check Fixity API
    -> Storage Service FixityLog
```

Master and replica are both `UPLOADED`, both are 3,027,140 bytes, and both have SHA-256:

`e08f0197821c05684cfc50b3dc6119801de6f9137dfeef1df5a43cc8a42ffbda`

## Native replication

Replication uses Archivematica Storage Service's own `Package.replicate()` and an `RP` Location. No Ordivon replication ontology or file-copy authority was introduced.

The master pointer contains a PREMIS `replication` event with outcome `success` and a derivation relationship to replica UUID `7d488fcc-c2f9-4490-a196-79885a595a1a`.

The replica pointer contains PREMIS `creation` and `validation` events with outcome `success`, including explicit evidence that master and replica SHA-256 values are equal.

Fresh replica fixity passed before the recovery drill.

## Real corruption and recovery drill

R7 performed a destructive recovery exercise against the real graduated R6 AIP, with a verified replica and verified recovery candidate already available.

The sequence was:

1. fresh-validate the independently stored replica;
2. stage exact replica bytes in the pipeline's real AIP Recovery Location;
3. fresh-validate that recovery candidate;
4. truncate the master AIP to **0 bytes**;
5. require Storage Service canonical fixity to fail;
6. call native `Package.recover_aip()`;
7. require the restored master to recover its exact original SHA-256;
8. require canonical master fixity to pass again;
9. require replica SHA-256 to remain unchanged.

Observed corrupted master:

```text
bytes     0
sha256    e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
fixity    FAIL
reason    Incorrect package checksum
```

Native `recover_aip()` returned success. No emergency rollback path was used.

After recovery:

```text
master sha256   e08f0197821c05684cfc50b3dc6119801de6f9137dfeef1df5a43cc8a42ffbda
master fixity   PASS
replica sha256  e08f0197821c05684cfc50b3dc6119801de6f9137dfeef1df5a43cc8a42ffbda
replica fixity  PASS
```

This is a real local disaster-recovery **mechanism drill**, not a claim of off-site disaster resilience.

## `unar` compatibility closure

The first recovery attempt correctly failed **before damaging the master** because Storage Service pre-validation could not extract the AIP with its packaged `unar` implementation.

The Ubuntu 24.04 package resolves to a `really1.10.1` codebase. On this Archivematica-generated 7z, `unar` reported `Wrong checksum` for `one-bell.wav`; 7-Zip 23.01 extracted the same archive successfully.

R7 did not patch Archivematica or add a private 7z fallback. Instead it built upstream **XADMaster v1.10.8** against the same Ubuntu 24.04 ABI and read-only bind-mounted only `unar` and `lsar` into Storage Service.

Accepted component hashes:

```text
unar
1c78186fff3dce0abc0b38f1df06fa7fbabaf91f09321015a0f09458fb5ab714

lsar
674c4998215f42da13b024b7ca9ed9d016150ef9db49176ed10504494dd61257
```

The exact previously failing Delta+BZip2 AIP then extracted successfully:

```text
files            104 / 104
extracted bytes  8,000,781
result           PASS
```

Archivematica Python source remained unchanged.

## Periodic fixity

R7 adopts Artefactual's own Fixity client rather than writing a custom scheduled scanner.

Pinned client:

```text
Fixity version   0.8.0
Git revision     3bf437d3d0b3d23383677f058419a7358c8f981f
```

The client aggregates AIPs and calls the Storage Service `check_fixity` API. The actual fixity check remains inside Storage Service.

A dedicated `fixity-r7` Storage Service identity was created with these properties:

- active;
- not staff;
- not superuser;
- no usable password;
- API credential stored only in `/etc/ordivon/fixity-r7.env`;
- credential file mode `0600 root:root`;
- credential value is not recorded in the R7 receipt or systemd journal.

Manual official-client `scanall --force-local` passed for both uploaded AIPs.

## systemd scheduling

The versioned source units are:

- `systemd/ordivon-preservation-fixity-r7.service`
- `systemd/ordivon-preservation-fixity-r7.timer`

The service does only one thing: execute the pinned Fixity client. systemd owns only scheduling and process sandboxing.

Current policy:

```text
base schedule      Sunday 03:17 Asia/Singapore
random delay       up to 30 minutes
Persistent         true
```

This cadence is a **local operating policy**, not claimed as a universal preservation standard.

The service was manually triggered before acceptance and again after Storage Service restart. Both runs scanned master and replica successfully. At final R7 projection:

```text
master FixityLog   7, latest = PASS
replica FixityLog  4, latest = PASS
timer              enabled / active / waiting
```

## Restart survival

Storage Service was restarted after the recovery/fixity configuration was established.

Post-restart verification proved:

- `/usr/local/bin/unar` still resolves to the accepted upstream replacement binary;
- master fresh local fixity = PASS;
- replica fresh local fixity = PASS;
- timer remains enabled and waiting;
- the scheduled systemd service still calls the Storage Service API successfully;
- master and replica physical SHA-256 values remain equal to the accepted R6 checksum.

## Rejected Windows D: carrier

R7 also tested a second storage carrier on Windows `D:` through WSL DrvFS/9p.

It was **rejected fail-closed**. Archivematica replication requires POSIX `mkdir`, `chmod`, and `rsync` behavior; the tested D: carrier did not provide the required semantics reliably. The failed replica occurrence and partial configuration were removed, and the Windows global mount policy was not changed.

Therefore the accepted R7 topology uses a second POSIX path inside WSL. This gives a second storage location for mechanism validation, but **not an independent hardware or site failure domain**.

## Pointer validation boundary

Replication provenance is present and mechanically parseable, but R7 does **not** claim pointer schema-conformance graduation.

Current `metsrw` validation can fail during XSD resolution because the xlink `simpleLink` attribute group cannot be resolved. Replica pointer creation also emitted Schematron warnings. Storage Service itself explicitly treats pointer XML schema parse/validation failures as non-fatal and returns the constructed pointer.

R7 therefore distinguishes:

```text
replication provenance          PASS
master/replica relationships    PASS
pointer availability            PASS
pointer semantic evidence       PASS
pointer schema conformance      NOT GRADUATED
```

This is recorded as a pointer validation infrastructure/schema-conformance defect, not as loss of replication provenance.

## Authority boundary

Ordivon still does not own AIP, PREMIS, METS, replication, recovery, or fixity semantics.

Mature components own those layers:

```text
Archivematica / Storage Service  -> AIP, replication, recovery, fixity
Artefactual Fixity               -> bulk/scheduled fixity client
systemd                          -> timing/process execution only
XADMaster unar                   -> archive extraction dependency
Ordivon                          -> composition, carrier choice, V&V, bounded policy, receipts
```

## Not claimed

R7 does not claim:

- off-site replication;
- an independent hardware failure domain;
- geographically separate disaster recovery;
- repository federation/deposit;
- LOCKSS-style multi-site preservation;
- universal fixity cadence;
- pointer XSD/Schematron conformance;
- Windows D: as a graduated Archivematica replica carrier.

Those claims require separate evidence and should not be inferred from this local operations graduation.

Machine-readable verdict: `artifacts/creative-preservation/operations-r7/acceptance-r7.json`.
