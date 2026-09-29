# D-Drive Offline Maintenance R3

Status: CURRENT CANDIDATE / STANDARDS-FIRST REPLACEMENT FOR R2 GATE

R3 exists because the R2 compact path coupled six different owners into one long-lived `wsl.exe -> bash` session. The physical compact mechanism was not the failure. The incorrect LEGO choices were: full Runtime Doctor polling, iteration-count timeouts, transport-session-owned fencing, non-atomic intermediate evidence, and diagnosis inferred from a missing READY file.

## Authority split

- Runtime Registry `admission.lock`: authority for fencing new Linux Runtime admissions.
- `ordivon-runtime-inspect registry-status`: cheap owner-native drain projection.
- `ordivon-runtime-doctor`: one-shot integrity verification after quiescence, never the polling primitive.
- systemd transient service: durable Linux gate process owner. A Windows `wsl.exe systemd-run` call submits the service and returns; WSL transport lifetime is not gate lifetime.
- Windows Task Scheduler native S4U: user-context carrier for the user-owned WSL distro.
- R4 authorizer: binds a short-lived grant to the exact R3 READY digest, exact gate/controller digests, maintenance identity, and a still-active gate unit.
- Windows R3 controller: offline WSL transition, detached/exclusive VHD proof, one `Optimize-VHD -Mode Full`, byte-level measurement, restore, and requalification.

## State circuit

`CREATED -> PRESSURE_QUIESCED -> FENCE_ACQUIRED -> DRAINING -> QUIESCENT -> INTEGRITY_VERIFIED -> TRIMMED -> READY_HELD -> HANDOFF_HELD`.

Every normal rejection emits `gate-terminal.json` with `phase` and `reasonCode`. Drain uses a monotonic deadline; polling uses `registry-status`; full Doctor executes exactly once after zero active/held work. Canonical JSON evidence is written through temp + fsync + atomic replace. READY remains valid only while the named systemd gate unit is active and no terminal receipt exists.

The Windows controller does not infer diagnosis from a missing file. It distinguishes explicit gate terminal rejection, gate-unit disappearance, controller wait deadline, authorization timeout, WSL offline failure, VHD detach failure, compact failure, and recovery/requalification failure.

## Safety invariants

R3 does not cancel another Agent's active Runtime Job. It holds the same exclusive admission fence used by structured Runtime release and waits for already-admitted work to drain naturally. Identity availability is not effect authorization. VHD compaction is forbidden until exact READY + exact authorization + handoff acknowledgment + WSL offline + exclusive-open + `Get-VHD Attached=False` are all proven.

The compact Scheduled Task must not inherit default power semantics that can asynchronously hard-kill the transaction. Battery/AC policy is a precondition/observation concern, not an external lifecycle authority over an in-flight VHD effect.

## Retirements after acceptance

After R3 live acceptance, retire the R2 long-lived gate/controller/authorizer runner from active paths. Historical receipts remain immutable evidence. Do not reintroduce custom LSA S4U launchers, process-token duplication, full-Doctor polling, or a long-lived `wsl.exe` gate carrier.
