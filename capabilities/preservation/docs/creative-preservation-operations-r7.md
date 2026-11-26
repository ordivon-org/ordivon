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

## 2026-10-25 currentness / CEGAR regression evidence (not an R7 historical retraction)

**Observed live FAIL**: `ordivon-preservation-fixity-r7.service` was failed, because host-native Fixity could not connect to its configured local Storage Service at `127.0.0.1:62081`. The Archivematica Storage Service container was running, but Docker inspection showed `HostConfig.PortBindings={}` and `NetworkSettings.Ports={"8000/tcp":null}`. The active container's `com.docker.compose.project.config_files` listed only the upstream Archivematica Compose and the clamav overlay, **not** this Preservation-owned R10 overlay.

**Refined owner-native contract**: the Preservation source overlay now declares `127.0.0.1:62081:8000` on `archivematica-storage-service` and its existing source verifier rejects an absent, wrong-port or all-interface mapping under both normal and `python -O` execution. Reusing Docker Compose's native port publication is preferred over a new ad hoc forwarding daemon or retry loop. The unchanged provider still owns Storage Service semantics.

**Deployment qualification is separate and presently UNKNOWN**. Source acceptance proves only that the checked overlay has the declared configuration. Recovery of the actual scheduled Fixity consumer requires the deployment owner to combine this overlay with the live upstream profile and independently verify: Docker's current bound port is precisely the loopback contract, the provider is ready at the endpoint, the actual Fixity client authenticates and scans the intended AIPs, and the timer/service records a successful owner-native run. The existing live container was **not recreated** as part of this source refinement. Do not mask a data-integrity failure by disabling the timer, skipping scans, or treating a running container as API readiness. Do not infer retention/replica safety solely from this source check.

**CEGAR scope**: a service existing in Compose is an abstraction of the service graph, but it is insufficient to establish that a host-native consumer can reach the provider. The concrete counterexample refines the producer/consumer edge to require exact bind address, port and deployed composition evidence. This does not prove that a later network change or Storage Service failure is impossible.

## 2026-11-08 R10 deployment recovery — real provider/consumer read-back

The preceding dated October 25 failure and source-only qualification remain
historically valid. This new observation **closes that specific installed
Linux-node mismatch** using the upstream Docker Compose and Artefactual
Fixity providers, not a new proxy, scanner, lease service or registry.

- The installed overlay
  `/opt/ordivon/external/archivematica/1.18.0/overlays/docker-compose.preservation-r10.yml`
  was copied from the existing Owner-tracked R10 source; both had SHA-256
  `903d18f8c16cb9612f89a898b7690d55a79f03fee73f612d7c96c33c5595d20b`.
  The installed Docker service's Compose provenance now lists the upstream
  Archivematica base, the existing ClamAV R6 overlay **and** that R10 overlay.
- A `docker compose up --no-deps --no-build -d archivematica-storage-service`
  with those three qualified files recreated **only** the Storage Service
  container. The image ID stayed
  `sha256:c87bf9bd5f51b425d9933cd37542b78f4d27d08a10e78f6348f81160c30802ea`
  and the existing staging volume stayed
  `/var/lib/docker/volumes/am_archivematica_storage_service_staging_data/_data`.
  Dashboard and MCP containers were not recreated.
- Docker now publishes **only** `127.0.0.1:62081:8000`. An actual
  `GET http://127.0.0.1:62081/api/v2/` returned HTTP 200 both immediately
  after the service update and during final read-back.
- The unchanged `ordivon-preservation-fixity-r7.service` was restarted
  using its existing systemd EnvironmentFile without reading or exposing
  credential values. systemd reported `Result=success` and
  `ExecMainStatus=0`. Its own journal reported successful Fixity checks
  for **six distinct AIPs**, summarized by `Successfully scanned 6 AIPs`;
  the existing timer remained `active/waiting`.
- The registered `mise run preservation:verify` source task remained PASS:
  9 native tests passed and the tracked=48, payload=43, services=9
  source-boundary evidence remained valid.

**Native recovery/reconfiguration procedure**: always retain **all three**
file inputs to Docker Compose for this installation. Running only the base
and ClamAV Compose files can recreate a running-but-unreachable Storage Service,
which is exactly what the former failed Fixity consumer demonstrated.
The qualified command is equivalent to:

```bash
root=/opt/ordivon/external/archivematica/1.18.0
cd "$root/src/hack"
compose_files=(
  -f "$root/src/hack/docker-compose.yml"
  -f "$root/overlays/docker-compose.clamav-r6.yml"
  -f "$root/overlays/docker-compose.preservation-r10.yml"
)
docker compose --project-name am "${compose_files[@]}" up --no-deps --no-build -d archivematica-storage-service
docker port am-archivematica-storage-service-1 8000/tcp
curl --noproxy '*' --fail --max-time 5 -s -o /dev/null http://127.0.0.1:62081/api/v2/
systemctl start ordivon-preservation-fixity-r7.service
systemctl show ordivon-preservation-fixity-r7.service --property=Result,ExecMainStatus
```

This is one date/node-scoped **installed deployment and fixity** acceptance.
It does not establish a second off-site failure domain, actual AIP
restore-from-backup rehearsal, owner retention clearance, legal/rights-based
deletion authority, active Artifact file leases, or safety of automatic GC.
An ephemeral `Artifact.stage_verified_input` observation is likewise not a
durable AIP or retention claim. AIP storage and recovery remain Archivematica
Storage Service responsibilities; no production deletion or re-ingest was
performed during this corrective run.
