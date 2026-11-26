-------------------------- MODULE IssuerRevokeAckR1 ---------------------------
EXTENDS Naturals, TLC

\* Model refinement of the independent PG18.7 / native systemd R34 experiment.
\* This is a SOURCE-ONLY design obligation, not an installed Runner proof.
\*
\* "pgLockOnly": a live Runner holds original-issuer FOR SHARE until its
\* target spawn, but the PostgreSQL backend may die while the native Runner
\* remains resident. Automatic PG lock release permits revoke COMMIT first.
\*
\* "drainAck": issuer revoke COMMIT is only a REQUEST. A separate ACK is
\* emitted after the issued native Unit is stopped / quiescent, and the
\* original issuer prevents new dispatch. The actual completeness of native
\* OS observation and recovery fencing is an unproven implementation premise.
\*
\* This finite model has ONE original Run epoch and ONE issued Attempt. It
\* cannot establish cross-database OriginalRun identity, multiple Attempts,
\* Domain byte ACK, real systemd correctness, or crash recovery by itself.

CONSTANT LaunchPolicy
VARIABLES issuer, attempt, pgGuard, nativeUnit, dispatchCount,
          stopIntent, dispatchFenced, revokeAck,
          spawnedAfterCommit, spawnedAfterAck

vars == <<issuer, attempt, pgGuard, nativeUnit, dispatchCount,
          stopIntent, dispatchFenced, revokeAck,
          spawnedAfterCommit, spawnedAfterAck>>

Init ==
    /\ issuer = "current"
    /\ attempt = "none"
    /\ pgGuard = "none"
    /\ nativeUnit = "absent"
    /\ dispatchCount = 0
    /\ stopIntent = FALSE
    /\ dispatchFenced = FALSE
    /\ revokeAck = FALSE
    /\ spawnedAfterCommit = FALSE
    /\ spawnedAfterAck = FALSE

Admit ==
    /\ issuer = "current"
    /\ ~dispatchFenced
    /\ attempt = "none"
    /\ attempt' = "admitted"
    /\ UNCHANGED <<issuer, pgGuard, nativeUnit, dispatchCount,
                   stopIntent, dispatchFenced, revokeAck,
                   spawnedAfterCommit, spawnedAfterAck>>

\* PG DISPATCH_ISSUED and native systemd transient start request are not
\* already evidence that the target executable ran.
Issue ==
    /\ issuer = "current"
    /\ ~dispatchFenced
    /\ attempt = "admitted"
    /\ dispatchCount = 0
    /\ attempt' = "issued"
    /\ nativeUnit' = "pending"
    /\ dispatchCount' = 1
    /\ UNCHANGED <<issuer, pgGuard, stopIntent, dispatchFenced,
                   revokeAck, spawnedAfterCommit, spawnedAfterAck>>

AcquireGuard ==
    /\ LaunchPolicy = "pgLockOnly"
    /\ attempt = "issued"
    /\ issuer = "current"
    /\ pgGuard = "none"
    /\ pgGuard' = "held"
    /\ UNCHANGED <<issuer, attempt, nativeUnit, dispatchCount,
                   stopIntent, dispatchFenced, revokeAck,
                   spawnedAfterCommit, spawnedAfterAck>>

\* PG backend is dead and releases FOR SHARE, but native Runner may still
\* execute. The released lock is NOT a native process-cancellation token.
LosePgBackend ==
    /\ LaunchPolicy = "pgLockOnly"
    /\ pgGuard = "held"
    /\ pgGuard' = "lost"
    /\ UNCHANGED <<issuer, attempt, nativeUnit, dispatchCount,
                   stopIntent, dispatchFenced, revokeAck,
                   spawnedAfterCommit, spawnedAfterAck>>

\* In the pgLockOnly policy revoke was actually blocked while the Backend
\* held its lock, then committed after the Backend was terminated.
\* In drainAck it commits a REQUEST and fences all future PG issuances.
CommitRevoke ==
    /\ issuer = "current"
    /\ CASE LaunchPolicy = "pgLockOnly" -> pgGuard = "lost"
         [] LaunchPolicy = "drainAck" -> TRUE
    /\ issuer' = "revoked"
    /\ dispatchFenced' = TRUE
    /\ UNCHANGED <<attempt, pgGuard, nativeUnit, dispatchCount,
                   stopIntent, revokeAck, spawnedAfterCommit, spawnedAfterAck>>

\* systemd may launch a previously issued transient Unit AFTER PG revoke
\* COMMIT. It is not permitted after a native unit is truly quiescent.
NativeTargetSpawn ==
    /\ attempt = "issued"
    /\ nativeUnit = "pending"
    /\ CASE LaunchPolicy = "pgLockOnly" -> pgGuard \in {"held", "lost"}
         [] LaunchPolicy = "drainAck" -> TRUE
    /\ nativeUnit' = "running"
    /\ spawnedAfterCommit' = (issuer = "revoked")
    /\ spawnedAfterAck' = revokeAck
    /\ UNCHANGED <<issuer, attempt, pgGuard, dispatchCount,
                   stopIntent, dispatchFenced, revokeAck>>

RequestNativeStop ==
    /\ LaunchPolicy = "drainAck"
    /\ issuer = "revoked"
    /\ attempt = "issued"
    /\ ~stopIntent
    /\ stopIntent' = TRUE
    /\ UNCHANGED <<issuer, attempt, pgGuard, nativeUnit,
                   dispatchCount, dispatchFenced, revokeAck,
                   spawnedAfterCommit, spawnedAfterAck>>

\* Physical observation means NO pending systemd manager job and no
\* bound cgroup/PID (including activating/start-pre units). The source
\* implementation must independently prove these facts before using it.
\* A Manager Job can disappear while its original operation remains active.
\* This is witnessed by the native opt-in Manager handoff experiment:
\* CancelJob followed by the original executing Unit writing completion bytes.
\* Neither this transition nor an effect completed before ACK is a drain proof.
CancelRunningManagerJob ==
    /\ LaunchPolicy = "drainAck"
    /\ stopIntent
    /\ nativeUnit = "running"
    /\ nativeUnit' = "running_manager_cancelled"
    /\ UNCHANGED <<issuer, attempt, pgGuard, dispatchCount,
                   stopIntent, dispatchFenced, revokeAck,
                   spawnedAfterCommit, spawnedAfterAck>>

CompleteOriginalEffect ==
    /\ nativeUnit = "running_manager_cancelled"
    /\ nativeUnit' = IF revokeAck THEN "effect_after_ack" ELSE "effect_completed"
    /\ UNCHANGED <<issuer, attempt, pgGuard, dispatchCount,
                   stopIntent, dispatchFenced, revokeAck,
                   spawnedAfterCommit, spawnedAfterAck>>

ObserveNativeQuiescence ==
    /\ LaunchPolicy = "drainAck"
    /\ stopIntent
    /\ nativeUnit \in {"pending", "running", "running_manager_cancelled", "effect_completed"}
    /\ nativeUnit' = "quiescent"
    /\ UNCHANGED <<issuer, attempt, pgGuard, dispatchCount,
                   stopIntent, dispatchFenced, revokeAck,
                   spawnedAfterCommit, spawnedAfterAck>>

\* A strong NoFutureSpawn acknowledgment is a DIFFERENT completion point
\* from issuer-revocation transaction COMMIT. ACK can remain UNKNOWN.
PublishRevokeAck ==
    /\ LaunchPolicy = "drainAck"
    /\ issuer = "revoked"
    /\ dispatchFenced
    /\ stopIntent
    /\ nativeUnit = "quiescent"
    /\ ~revokeAck
    /\ revokeAck' = TRUE
    /\ UNCHANGED <<issuer, attempt, pgGuard, nativeUnit,
                   dispatchCount, stopIntent, dispatchFenced,
                   spawnedAfterCommit, spawnedAfterAck>>

Next ==
    \/ Admit
    \/ Issue
    \/ AcquireGuard
    \/ LosePgBackend
    \/ CommitRevoke
    \/ NativeTargetSpawn
    \/ RequestNativeStop
    \/ CancelRunningManagerJob
    \/ CompleteOriginalEffect
    \/ ObserveNativeQuiescence
    \/ PublishRevokeAck

Spec == Init /\ [][Next]_vars

TypeOK ==
    /\ LaunchPolicy \in {"pgLockOnly", "drainAck"}
    /\ issuer \in {"current", "revoked"}
    /\ attempt \in {"none", "admitted", "issued"}
    /\ pgGuard \in {"none", "held", "lost"}
    /\ nativeUnit \in {"absent", "pending", "running", "running_manager_cancelled",
                       "effect_completed", "effect_after_ack", "quiescent"}
    /\ dispatchCount \in 0..1
    /\ stopIntent \in BOOLEAN
    /\ dispatchFenced \in BOOLEAN
    /\ revokeAck \in BOOLEAN
    /\ spawnedAfterCommit \in BOOLEAN
    /\ spawnedAfterAck \in BOOLEAN

AtMostOnceDispatch == dispatchCount <= 1
NoSpawnAfterRevokeCommit == ~spawnedAfterCommit
NoSpawnAfterRevokeAck == ~spawnedAfterAck
AckRequiresPhysicalQuiescence ==
    revokeAck => (issuer = "revoked" /\ dispatchFenced /\
                  stopIntent /\ nativeUnit = "quiescent")

\* Negative-control non-vacuity: ACK and physical native target spawn are
\* reachable on legitimate paths in the drainAck design.
AckUnreachable == ~revokeAck
TargetSpawnUnreachable == nativeUnit # "running"
\* A quiet Unit may have never executed. These predicates require actual
\* running/continued-effect witnesses, not quiescence alone.
ManagerCancelEffectUnreachable == nativeUnit # "effect_completed"
NoOriginalEffectAfterAck == nativeUnit # "effect_after_ack"

=============================================================================
