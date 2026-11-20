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
    /\ issued = AttemptIds
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
    \/ (launcher[a] = "blocked" /\ nativeUnit[a] = "absent")
    \/ (launcher[a] = "delivered" /\ nativeUnit[a] = "quiescent" /\
        a \in stopIntent)

\* A readback that all Units are presently absent does NOT establish this.
PublishAck ==
    /\ issuer = "revoked"
    /\ fenced
    /\ issued = AttemptIds
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
    \/ \E a \in AttemptIds: NativeTargetStart(a)
    \/ \E a \in AttemptIds: RequestStop(a)
    \/ \E a \in AttemptIds: ObserveQuiet(a)
    \/ PublishAck

Spec == Init /\ [][Next]_vars

TypeOK ==
    /\ issuer \in {"current", "revoked"}
    /\ issued \subseteq AttemptIds
    /\ launcher \in [AttemptIds -> {"not_started", "inflight", "crashed_unknown",
                                      "delivered", "blocked"}]
    /\ nativeUnit \in [AttemptIds -> {"absent", "pending", "running", "quiescent"}]
    /\ stopIntent \subseteq AttemptIds
    /\ fenced \in BOOLEAN
    /\ revokeAck \in BOOLEAN
    /\ unitBornAfterAck \in BOOLEAN
    /\ spawnedAfterAck \in BOOLEAN
    /\ nativeHandoffPending \subseteq AttemptIds
    /\ crashedCallers \subseteq AttemptIds

NoUnitBirthAfterAck == ~unitBornAfterAck
NoSpawnAfterAck == ~spawnedAfterAck
AckRequiresAllIssuedQuiescent ==
    revokeAck => (fenced /\ issuer = "revoked" /\ issued = AttemptIds /\
                  \A a \in AttemptIds: LaunchFinalized(a))

\* Distinguish actual manager handoff from a stale "Unit absent" snapshot.
AckRequiresNoHandoffPending == revokeAck => nativeHandoffPending = {}

\* Legitimate crash + later manager delivery + native Stop + ACK is reachable.
CrashThenAckUnreachable == ~(revokeAck /\ crashedCallers # {})

\* Separate intentionally false positive-path reachability checks.
AckUnreachable == ~revokeAck
TargetSpawnUnreachable ==
    \A a \in AttemptIds: nativeUnit[a] \notin {"running", "quiescent"}

=============================================================================
