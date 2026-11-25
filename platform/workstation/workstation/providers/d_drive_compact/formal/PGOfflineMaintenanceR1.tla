----------------------- MODULE PGOfflineMaintenanceR1 -----------------------
EXTENDS Integers, FiniteSets

(*
  Independent protocol specification, not a live maintenance authority.
  Roots stand for an independently complete census of real consumers.
  Epoch abstracts the exact maintenance/Runtime/VHD subject and READY cut.
  Native detach/exclusive, backup, reconciliation, health and acceptance
  actions stand for separately qualified effects/evidence, not booleans
  that an implementation may set without those witnesses.
  No long-lived PG admission lock during settlement.
*)
CONSTANTS OmitRoots, OmitEpoch, OmitDetach, OmitAccept, BlockDrain,
          OmitFresh, OmitBackup
VARIABLE s

Roots == {"job", "reservation", "run", "recovery", "other_distro"}
Phases == {"LIVE", "DRAINING", "READY", "AUTHORIZED", "HANDOFF",
           "STOPPING", "OFFLINE", "COMPACTED", "RECOVERING", "UNKNOWN",
           "ACCEPTED", "REOPENED", "ABORTED"}
BeforeEffect == {"DRAINING", "READY", "AUTHORIZED", "HANDOFF"}
AfterHandoff == {"HANDOFF", "STOPPING", "OFFLINE", "COMPACTED",
                 "RECOVERING", "UNKNOWN", "ACCEPTED", "REOPENED"}
Init ==
  s = [phase |-> "LIVE", closed |-> FALSE, roots |-> Roots,
       epoch |-> 0, readyEpoch |-> -1, authEpoch |-> -1,
       fresh |-> FALSE, backup |-> FALSE, attached |-> TRUE,
       exclusive |-> FALSE, effect |-> "none",
       healthy |-> FALSE, policy |-> FALSE, accepted |-> FALSE]

Begin ==
  /\ s.phase = "LIVE"
  /\ s' = [s EXCEPT !.phase = "DRAINING", !.closed = TRUE]

Settle(r) ==
  /\ s.phase \in {"LIVE", "DRAINING", "READY", "AUTHORIZED"}
  /\ r \in s.roots
  /\ ~(BlockDrain /\ s.phase = "DRAINING" /\ r \in {"job", "reservation"})
  /\ s' = [s EXCEPT !.roots = @ \ {r}]

Admit ==
  /\ s.phase = "LIVE" /\ ~s.closed /\ "job" \notin s.roots
  /\ s' = [s EXCEPT !.roots = @ \cup {"job"}]

\* A separate external root may appear before host handoff.
ExternalRoot(r) ==
  /\ s.phase \in {"DRAINING", "READY", "AUTHORIZED"}
  /\ r \in Roots \ {"job", "reservation"}
  /\ r \notin s.roots
  /\ s' = [s EXCEPT !.roots = @ \cup {r}]

ProveBackup ==
  /\ s.phase = "DRAINING" /\ ~s.backup
  /\ s' = [s EXCEPT !.backup = TRUE]

Ready ==
  /\ s.phase = "DRAINING" /\ s.closed /\ (OmitBackup \/ s.backup) /\ s.roots = {}
  /\ s' = [s EXCEPT !.phase = "READY", !.readyEpoch = s.epoch]

Grant ==
  /\ s.phase = "READY" /\ s.readyEpoch = s.epoch /\ s.roots = {}
  /\ s' = [s EXCEPT !.phase = "AUTHORIZED", !.authEpoch = s.readyEpoch,
                    !.fresh = TRUE]

Drift ==
  /\ s.phase \in {"READY", "AUTHORIZED"} /\ s.epoch = 0
  /\ s' = [s EXCEPT !.epoch = 1]

Expire ==
  /\ s.phase = "AUTHORIZED" /\ s.fresh
  /\ s' = [s EXCEPT !.fresh = FALSE]

Handoff ==
  /\ s.phase = "AUTHORIZED" /\ s.closed /\ (OmitBackup \/ s.backup) /\ (OmitFresh \/ s.fresh)
  /\ (OmitRoots \/ s.roots = {})
  /\ (OmitEpoch \/ (s.readyEpoch = s.epoch /\ s.authEpoch = s.epoch))
  /\ s' = [s EXCEPT !.phase = "HANDOFF"]

\* Independent Windows owner proves no effect has begun, not a timeout guess.
AbortBeforeEffect ==
  /\ s.phase \in BeforeEffect /\ s.effect = "none"
  /\ s' = [s EXCEPT !.phase = "ABORTED", !.closed = FALSE]

StartShutdown ==
  /\ s.phase = "HANDOFF"
  /\ s' = [s EXCEPT !.phase = "STOPPING", !.effect = "started"]

ConfirmDetach ==
  /\ s.phase = "STOPPING"
  /\ s' = [s EXCEPT !.phase = "OFFLINE", !.attached = FALSE]

ProveExclusive ==
  /\ s.phase = "OFFLINE" /\ ~s.attached /\ ~s.exclusive
  /\ s' = [s EXCEPT !.exclusive = TRUE]

Compact ==
  /\ IF OmitDetach THEN s.phase \in {"STOPPING", "OFFLINE"}
     ELSE s.phase = "OFFLINE" /\ ~s.attached /\ s.exclusive
  /\ s' = [s EXCEPT !.phase = "COMPACTED", !.effect = "compacted"]

Restart ==
  /\ s.phase = "COMPACTED"
  /\ s' = [s EXCEPT !.phase = "RECOVERING", !.attached = TRUE,
                    !.exclusive = FALSE]

LoseEffect ==
  /\ s.phase \in {"STOPPING", "OFFLINE", "COMPACTED", "RECOVERING"}
  /\ s' = [s EXCEPT !.phase = "UNKNOWN", !.effect = "unknown",
                    !.healthy = FALSE, !.policy = FALSE]

\* Physical effect is reconciled independently; no automatic repeat compact.
Reconcile ==
  /\ s.phase = "UNKNOWN"
  /\ s' = [s EXCEPT !.phase = "RECOVERING", !.effect = "reconciled",
                    !.attached = TRUE, !.exclusive = FALSE]

VerifyHealth ==
  /\ s.phase = "RECOVERING" /\ ~s.healthy
  /\ s' = [s EXCEPT !.healthy = TRUE]

RestorePolicy ==
  /\ s.phase = "RECOVERING" /\ ~s.policy
  /\ s' = [s EXCEPT !.policy = TRUE]

Accept ==
  /\ s.phase = "RECOVERING" /\ s.healthy /\ s.policy /\ s.roots = {}
  /\ s' = [s EXCEPT !.phase = "ACCEPTED", !.accepted = TRUE]

Reopen ==
  /\ s.phase = "ACCEPTED" \/ (OmitAccept /\ s.phase = "RECOVERING")
  /\ s' = [s EXCEPT !.phase = "REOPENED", !.closed = FALSE]

Next ==
  \/ Begin \/ Admit \/ (\E r \in Roots: Settle(r) \/ ExternalRoot(r))
  \/ ProveBackup \/ Ready \/ Grant \/ Drift \/ Expire \/ Handoff
  \/ AbortBeforeEffect \/ StartShutdown \/ ConfirmDetach \/ ProveExclusive
  \/ Compact \/ Restart \/ LoseEffect \/ Reconcile
  \/ VerifyHealth \/ RestorePolicy \/ Accept \/ Reopen

Spec == Init /\ [][Next]_s
TypeOK ==
  /\ s.phase \in Phases /\ s.roots \subseteq Roots
  /\ s.epoch \in {0, 1} /\ s.readyEpoch \in {-1, 0, 1}
  /\ s.authEpoch \in {-1, 0, 1}
  /\ s.effect \in {"none", "started", "compacted", "unknown", "reconciled"}
  /\ s.closed \in BOOLEAN /\ s.fresh \in BOOLEAN /\ s.backup \in BOOLEAN
  /\ s.attached \in BOOLEAN /\ s.exclusive \in BOOLEAN
  /\ s.healthy \in BOOLEAN /\ s.policy \in BOOLEAN /\ s.accepted \in BOOLEAN

NoLiveRootsAfterHandoff == s.phase \in AfterHandoff => s.roots = {}
ExactHandoff ==
  s.phase \in AfterHandoff =>
    s.backup /\ s.fresh /\ s.readyEpoch = s.epoch /\ s.authEpoch = s.epoch
NativeDetachBeforeCompact ==
  s.phase = "COMPACTED" => ~s.attached /\ s.exclusive
ClosedUntilReconciled ==
  s.phase \notin {"LIVE", "ABORTED", "REOPENED"} => s.closed
RecoveryBeforeReopen ==
  s.phase = "REOPENED" => s.accepted /\ s.healthy /\ s.policy
UnknownIsNotPermission == s.phase = "UNKNOWN" => s.closed /\ s.effect = "unknown"
DrainProgress ==
  s.phase = "DRAINING" =>
    \A r \in (s.roots \cap {"job", "reservation"}): ENABLED Settle(r)

NeverReopened == s.phase # "REOPENED"
=============================================================================
