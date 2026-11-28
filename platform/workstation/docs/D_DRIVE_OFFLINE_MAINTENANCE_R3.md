# D-Drive Offline Maintenance R3

Status: **historical SQLite carrier; not qualified for PG Runtime maintenance**.
The PG-native protocol is a candidate, not an installed replacement.

R3 addressed R2's coupling of six owners into a long-lived WSL transport
session. Preserve the independent design rationale: avoid full Runtime Doctor polling, use a monotonic deadline, a systemd transient service owned by Linux,
and temp + fsync + atomic replace for intermediate evidence. Missing READY
is not a diagnosis. Retain original receipts as historical evidence.

## Contract and authority

- [PG offline protocol](../workstation/providers/d_drive_compact/formal/PGOfflineMaintenanceR1.tla):
  independent bounded state machine, including admission closure without
  blocking existing terminal settlement, complete roots, qualified backup,
  exact authorization, detach, effect reconciliation and recovery acceptance.
- [Legacy gate](../workstation/providers/d_drive_compact/d_drive_compact_gate_r3.py):
  the old SQLite admission lock, inspector and Doctor are not PG authority.
  Its source candidate rejects unsupported authority before maintenance effects.
- [Windows runner](../workstation/providers/d_drive_compact/DDriveCompactRunR3.ps1)
  and [controller](../workstation/providers/d_drive_compact/DDriveOfflineCompactR3.ps1):
  native request ownership, offline effect and recovery; unknown results retain
  their request. Identity availability is not effect authorization.
- [Materialization status](../workstation/providers/d_drive_compact/materialize.py):
  observational exact-copy candidates, divergent/unknown files and absent
  targets. Equal bytes are not consumer release or deletion authorization.

The real PG admission and terminal writers share an advisory transaction lock;
holding that lock during drain would obstruct settlement. Runtime must own a
separate admission-closure mechanism and prove all required consumers are
settled. Workstation must qualify the actual distro/VHD identity and native
offline carrier; neither owner may infer success from the other's test PASS.
Do not stop unrelated WSL distributions or cancel other Agents' work merely
to reclaim space. Verify a recoverable backup, durable handoff, native detach
or other qualified carrier conditions, post-effect health, and independent
acceptance before reopening. The model is not proof of installed effects.

## Physical storage and operational obligations

Distinguish VHD file length, NTFS allocated bytes and D: free bytes. Sparse
and non-sparse VHDs differ; guest free space is not host reclaim. Use exact
before/after native measurements, not file-size estimates. A supported native
compact command still needs a separately qualified maintenance window and
recovery path. Do not allow default battery/AC scheduled-task policy to kill
an in-flight disk effect.

Storage-pressure policy remains owned by its existing controller. Temporary
quiescence is allowed only with explicit restoration of the previous timer
activity and enablement; never manufacture a pressure-service cycle or
enable a previously disabled timer. Failure to establish restored policy or
a terminal effect means reconciliation, not cleanup authorization.

Retire old R2/R3 operational carriers only after actual replacement and
consumer acceptance. Keep independent specifications, historical receipts,
and any unique recovery artifacts; don't recreate custom S4U launchers or
transport-session-owned fences.
