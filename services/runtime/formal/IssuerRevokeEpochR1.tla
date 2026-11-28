------------------------ MODULE IssuerRevokeEpochR1 --------------------------
EXTENDS Naturals, TLC

\* R37 refinement of original R35 two-Attempt original-Run epoch model.
\* PostgreSQL DISPATCH_ISSUED is durable BEFORE systemd-run creates a Unit.
\* An already-running native launcher may create a Unit after issuer revoke.
\* These are SOURCE-ONLY finite design conditions, not installed runtime proof.
\*
\* Strong ACK requires all issued Attempts to have BOTH:
\*   (a) an operator-qualified durable scheduler fence for an unstarted launch,
\*       with no native Unit, OR
\*   (b) a completed native launch handoff and verified native Unit quiet.
\* An "inflight" launcher is deliberately not drainable merely because a
\* systemctl lookup currently reports no Unit. It can stay UNKNOWN indefinitely
\* if original native handoff/caller ownership cannot be reconciled.
\* Unit birth and physical target start are distinct actions. A real
\* implementation still must prove all-epoch issuance enumeration, the exact
\* launch ownership receipt, crash/recovery no-redispatch and Domain ACK.
\* R56: native caller crash leaves a pending OS manager handoff with no Unit
\* visible yet; only true handoff reconciliation may satisfy NoFutureSpawn.
\* R57: a separate Manager CancelJob(exact accepted start Job) can discharge
\* that one pending OS handoff AFTER the original launcher has definitely
\* stopped. R6 separates physical cancel from observing and persisting
\* the exact JobRemoved receipt. Disconnect or observer crash can lose
\* the receipt, even with no native handoff left. No replay is assumed.
\* The real Manager must establish exact-Job cancellation and no further
\* caller submit; the durable receipt path is a design obligation.
\* This remains MODEL-ONLY, not a deployed OS/PG atomicity guarantee.

AttemptIds == {"a", "b"}
VARIABLES issuer, issued, launcher, nativeUnit, stopIntent, fenced,
          revokeAck, unitBornAfterAck, spawnedAfterAck,
          nativeHandoffPending, crashedCallers

vars == <<issuer, issued, launcher, nativeUnit, stopIntent, fenced,
          revokeAck, unitBornAfterAck, spawnedAfterAck,
          nativeHandoffPending, crashedCallers>>

Init ==
    /\ issuer = "current"
    /\ issued = {}
    /\ launcher = [a \in AttemptIds |-> "not_started"]
    /\ nativeUnit = [a \in AttemptIds |-> "absent"]
    /\ stopIntent = {}
    /\ fenced = FALSE
    /\ revokeAck = FALSE
    /\ unitBornAfterAck = FALSE
    /\ spawnedAfterAck = FALSE
    /\ nativeHandoffPending = {}
    /\ crashedCallers = {}

\* Exact PG DISPATCH_ISSUED commit: DOES NOT imply a systemd Unit exists.
Issue(a) ==
    /\ issuer = "current"
    /\ ~fenced
    /\ a \in AttemptIds \ issued
    /\ launcher[a] = "not_started"
    /\ issued' = issued \cup {a}
    /\ UNCHANGED <<issuer, launcher, nativeUnit, stopIntent, fenced,
                   revokeAck, unitBornAfterAck, spawnedAfterAck,
                   nativeHandoffPending, crashedCallers>>

\* Native caller entered an already-issued launch. Revoking PG cannot undo
\* a systemd-run invocation which has not produced any observable Unit yet.
BeginNativeLaunch(a) ==
    /\ issuer = "current"
    /\ ~fenced
    /\ a \in issued
    /\ launcher[a] = "not_started"
    /\ nativeUnit[a] = "absent"
    /\ launcher' = [launcher EXCEPT ![a] = "inflight"]
    /\ nativeHandoffPending' = nativeHandoffPending \cup {a}
    /\ UNCHANGED <<issuer, issued, nativeUnit, stopIntent, fenced,
                   revokeAck, unitBornAfterAck, spawnedAfterAck, crashedCallers>>

\* Caller may crash after submitting the async systemd manager request.
\* The Unit can remain absent while the manager may still deliver it later.
CrashNativeCaller(a) ==
    /\ a \in nativeHandoffPending
    /\ launcher[a] = "inflight"
    /\ nativeUnit[a] = "absent"
    /\ launcher' = [launcher EXCEPT ![a] = "crashed_unknown"]
    /\ crashedCallers' = crashedCallers \cup {a}
    /\ UNCHANGED <<issuer, issued, nativeUnit, stopIntent, fenced,
                   revokeAck, unitBornAfterAck, spawnedAfterAck,
                   nativeHandoffPending>>

CommitRevoke ==
    /\ issuer = "current"
    \* Revoke freezes the actual issued subset, including an empty subset.
    /\ issuer' = "revoked"
    /\ fenced' = TRUE
    /\ UNCHANGED <<issued, launcher, nativeUnit, stopIntent,
                   revokeAck, unitBornAfterAck, spawnedAfterAck,
                   nativeHandoffPending, crashedCallers>>

\* A stale native caller may submit AFTER revoke commit. Safe ACK is blocked
\* until the caller has either ended or is durably fenced before launching.
NativeUnitBirth(a) ==
    /\ a \in issued
    /\ a \in nativeHandoffPending
    /\ launcher[a] \in {"inflight", "crashed_unknown", "blocked"}
    /\ nativeUnit[a] = "absent"
    /\ nativeUnit' = [nativeUnit EXCEPT ![a] = "pending"]
    /\ launcher' = [launcher EXCEPT ![a] = "delivered"]
    /\ nativeHandoffPending' = nativeHandoffPending \ {a}
    /\ unitBornAfterAck' = (unitBornAfterAck \/ revokeAck)
    /\ UNCHANGED <<issuer, issued, stopIntent, fenced,
                   revokeAck, spawnedAfterAck, crashedCallers>>

\* This is an abstract owner-qualified durable scheduler fence, NOT merely
\* a PG row update, timeout or observation that systemctl has no Unit.
\* It may only retire a caller known NEVER to have entered native launch.
FenceUnstarted(a) ==
    /\ issuer = "revoked"
    /\ a \in issued
    /\ launcher[a] = "not_started"
    /\ nativeUnit[a] = "absent"
    /\ launcher' = [launcher EXCEPT ![a] = "blocked"]
    /\ UNCHANGED <<issuer, issued, nativeUnit, stopIntent, fenced,
                   revokeAck, unitBornAfterAck, spawnedAfterAck,
                   nativeHandoffPending, crashedCallers>>

\* Only a *manager-qualified* cancellation of the EXACT queued
\* native start may retire the original attempt without target birth.
\* Preconditions: issuer fenced, submitting native caller is no longer
\* capable of issuing a new StartUnit, and systemd independently confirms
\* the original queued Job was cancelled. This action is an ABSTRACT OS
\* ownership/ack transition, not a PG event or current Unit absence.
\* The native submitter-crash path is a sufficient but not necessary
\* caller-terminal proof in this finite two-Attempt model.
ConfirmExactNativeManagerCancel(a) ==
    /\ issuer = "revoked"
    /\ fenced
    /\ a \in issued
    /\ a \in crashedCallers
    /\ a \in nativeHandoffPending
    /\ launcher[a] = "crashed_unknown"
    /\ nativeUnit[a] = "absent"
    /\ launcher' \in {
        [launcher EXCEPT ![a] = "manager_cancel_observed"],
        [launcher EXCEPT ![a] = "manager_cancel_receipt_lost"]}
    /\ nativeHandoffPending' = nativeHandoffPending \ {a}
    /\ UNCHANGED <<issuer, issued, nativeUnit, stopIntent, fenced,
                   revokeAck, unitBornAfterAck, spawnedAfterAck,
                   crashedCallers>>

LoseUnpersistedCancelSignal(a) ==
    /\ launcher[a] = "manager_cancel_observed"
    /\ launcher' = [launcher EXCEPT ![a] = "manager_cancel_receipt_lost"]
    /\ UNCHANGED <<issuer, issued, nativeUnit, stopIntent, fenced,
                   revokeAck, unitBornAfterAck, spawnedAfterAck,
                   nativeHandoffPending, crashedCallers>>

PersistExactNativeManagerCancel(a) ==
    /\ launcher[a] = "manager_cancel_observed"
    /\ a \notin nativeHandoffPending
    /\ nativeUnit[a] = "absent"
    /\ launcher' = [launcher EXCEPT ![a] = "manager_cancel_durable"]
    /\ UNCHANGED <<issuer, issued, nativeUnit, stopIntent, fenced,
                   revokeAck, unitBornAfterAck, spawnedAfterAck,
                   nativeHandoffPending, crashedCallers>>

NativeTargetStart(a) ==
    /\ a \in issued
    /\ nativeUnit[a] = "pending"
    /\ nativeUnit' = [nativeUnit EXCEPT ![a] = "running"]
    /\ spawnedAfterAck' = (spawnedAfterAck \/ revokeAck)
    /\ UNCHANGED <<issuer, issued, launcher, stopIntent, fenced,
                   revokeAck, unitBornAfterAck,
                   nativeHandoffPending, crashedCallers>>

RequestStop(a) ==
    /\ issuer = "revoked"
    /\ a \in issued \ stopIntent
    /\ nativeUnit[a] \in {"pending", "running"}
    /\ stopIntent' = stopIntent \cup {a}
    /\ UNCHANGED <<issuer, issued, launcher, nativeUnit, fenced,
                   revokeAck, unitBornAfterAck, spawnedAfterAck,
                   nativeHandoffPending, crashedCallers>>

\* Verified absence of pending systemd manager Job, PID and cgroup AFTER
\* native handoff; an inflight launcher with no Unit cannot enter here.
ObserveQuiet(a) ==
    /\ a \in stopIntent
    /\ launcher[a] = "delivered"
    /\ nativeUnit[a] \in {"pending", "running"}
    /\ nativeUnit' = [nativeUnit EXCEPT ![a] = "quiescent"]
    /\ UNCHANGED <<issuer, issued, launcher, stopIntent, fenced,
                   revokeAck, unitBornAfterAck, spawnedAfterAck,
                   nativeHandoffPending, crashedCallers>>

LaunchFinalized(a) ==
    \* A never-issued slot needs no OS drain; fencing excludes future issue.
    \/ (a \notin issued /\ launcher[a] = "not_started" /\
        nativeUnit[a] = "absent" /\ a \notin nativeHandoffPending)
    \/ (launcher[a] = "blocked" /\ nativeUnit[a] = "absent")
    \/ (launcher[a] = "manager_cancel_durable" /\ nativeUnit[a] = "absent" /\
        a \notin nativeHandoffPending)
    \/ (launcher[a] = "delivered" /\ nativeUnit[a] = "quiescent" /\
        a \in stopIntent)

\* A readback that all Units are presently absent does NOT establish this.
PublishAck ==
    /\ issuer = "revoked"
    /\ fenced
    /\ ~revokeAck
    /\ \A a \in AttemptIds: LaunchFinalized(a)
    /\ revokeAck' = TRUE
    /\ UNCHANGED <<issuer, issued, launcher, nativeUnit, stopIntent, fenced,
                   unitBornAfterAck, spawnedAfterAck,
                   nativeHandoffPending, crashedCallers>>

Next ==
    \/ \E a \in AttemptIds: Issue(a)
    \/ \E a \in AttemptIds: BeginNativeLaunch(a)
    \/ \E a \in AttemptIds: CrashNativeCaller(a)
    \/ CommitRevoke
    \/ \E a \in AttemptIds: NativeUnitBirth(a)
    \/ \E a \in AttemptIds: FenceUnstarted(a)
    \/ \E a \in AttemptIds: ConfirmExactNativeManagerCancel(a)
    \/ \E a \in AttemptIds: LoseUnpersistedCancelSignal(a)
    \/ \E a \in AttemptIds: PersistExactNativeManagerCancel(a)
    \/ \E a \in AttemptIds: NativeTargetStart(a)
    \/ \E a \in AttemptIds: RequestStop(a)
    \/ \E a \in AttemptIds: ObserveQuiet(a)
    \/ PublishAck

Spec == Init /\ [][Next]_vars

TypeOK ==
    /\ issuer \in {"current", "revoked"}
    /\ issued \subseteq AttemptIds
    /\ launcher \in [AttemptIds -> {"not_started", "inflight", "crashed_unknown",
                                      "delivered", "blocked",
                                      "manager_cancel_observed", "manager_cancel_receipt_lost",
                                      "manager_cancel_durable"}]
    /\ nativeUnit \in [AttemptIds -> {"absent", "pending", "running", "quiescent"}]
    /\ stopIntent \subseteq AttemptIds
    /\ fenced \in BOOLEAN
    /\ revokeAck \in BOOLEAN
    /\ unitBornAfterAck \in BOOLEAN
    /\ spawnedAfterAck \in BOOLEAN
    /\ nativeHandoffPending \subseteq AttemptIds
    /\ crashedCallers \subseteq AttemptIds

\* The revoke cut freezes the actual issued set, not the bounded universe.
IssuedSetStableAfterFence == [][~fenced \/ UNCHANGED issued]_vars
NoUnissuedNativeEffects ==
    \A a \in AttemptIds \ issued:
        /\ launcher[a] = "not_started"
        /\ nativeUnit[a] = "absent"
        /\ a \notin nativeHandoffPending
        /\ a \notin stopIntent

NoUnitBirthAfterAck == ~unitBornAfterAck
NoSpawnAfterAck == ~spawnedAfterAck
AckRequiresAllIssuedQuiescent ==
    revokeAck => (fenced /\ issuer = "revoked" /\
                  \A a \in AttemptIds: LaunchFinalized(a))

\* Distinguish actual manager handoff from a stale "Unit absent" snapshot.
AckRequiresNoHandoffPending == revokeAck => nativeHandoffPending = {}

\* Legitimate crash + later manager delivery + native Stop + ACK is reachable.
CrashThenAckUnreachable == ~(revokeAck /\ issued = AttemptIds /\ crashedCallers # {})

\* A different positive path uses a qualified original Manager Job cancellation
\* with no target creation. The original issuer still needs all OTHER issued
\* Attempts independently finalized before it may publish an epoch-wide ACK.
ExactCancelAckUnreachable ==
    ~(revokeAck /\ issued = AttemptIds /\ \E a \in crashedCallers:
        launcher[a] = "manager_cancel_durable")

\* Evidence safety, independent of physical NoSpawnAfterAck.
AckRequiresDurableCancellationReceipt ==
    revokeAck => \A a \in issued:
        launcher[a] \notin {"manager_cancel_observed", "manager_cancel_receipt_lost"}

DurableCancelRequiresObserved ==
    [][\A a \in AttemptIds:
        (launcher'[a] = "manager_cancel_durable" /\
         launcher[a] # "manager_cancel_durable") =>
         launcher[a] = "manager_cancel_observed"]_vars

LostReceiptUnreachable ==
    ~(\E a \in issued: launcher[a] = "manager_cancel_receipt_lost" /\
        nativeHandoffPending = {} /\ ~revokeAck)

\* Separate intentionally false positive-path reachability checks.
AckUnreachable == ~(revokeAck /\ issued = AttemptIds)
ZeroIssuedAckUnreachable == ~(revokeAck /\ issued = {})
SingleIssuedAckUnreachable ==
    ~(revokeAck /\ \E a \in AttemptIds: issued = {a})
SingleIssuedDrainAckUnreachable ==
    ~(revokeAck /\ \E a \in AttemptIds:
        issued = {a} /\ nativeUnit[a] = "quiescent")
TargetSpawnUnreachable ==
    \A a \in AttemptIds: nativeUnit[a] \notin {"running", "quiescent"}

=============================================================================
