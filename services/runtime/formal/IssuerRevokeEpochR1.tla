------------------------ MODULE IssuerRevokeEpochR1 --------------------------
EXTENDS Naturals, TLC

\* OriginalRun/epoch aggregate: BOTH issued native Attempts must physically
\* drain before a NoFutureSpawn ACK. A one-Unit stop/observation is insufficient.
\* This is a finite design model, NOT the installed Runtime's drain protocol.
\* Independently observed real native systemd four-Unit test R35:
\* one stopped Unit quiet, other pending Unit later spawned; stopping both
\* left no pending Job/PID/cgroup and neither target started.
\*
\* Guards depend on reliable enumeration of all issued Attempts, exact
\* native Unit identity, OS readback, and a durable no-redispatch fence.
\* These are unresolved implementation proof obligations.

AttemptIds == {"a", "b"}
VARIABLES issuer, issued, nativeUnit, stopIntent, fenced, revokeAck,
          spawnedAfterAck

vars == <<issuer, issued, nativeUnit, stopIntent, fenced, revokeAck,
          spawnedAfterAck>>

Init ==
    /\ issuer = "current"
    /\ issued = {}
    /\ nativeUnit = [a \in AttemptIds |-> "absent"]
    /\ stopIntent = {}
    /\ fenced = FALSE
    /\ revokeAck = FALSE
    /\ spawnedAfterAck = FALSE

\* These two exact issued Attempt identities are known in the original epoch
\* before revocation; another model covers revocation with only one Attempt.
Issue(a) ==
    /\ issuer = "current"
    /\ ~fenced
    /\ a \in AttemptIds \ issued
    /\ nativeUnit[a] = "absent"
    /\ issued' = issued \cup {a}
    /\ nativeUnit' = [nativeUnit EXCEPT ![a] = "pending"]
    /\ UNCHANGED <<issuer, stopIntent, fenced, revokeAck,
                   spawnedAfterAck>>

CommitRevoke ==
    /\ issuer = "current"
    /\ issued = AttemptIds
    /\ issuer' = "revoked"
    /\ fenced' = TRUE
    /\ UNCHANGED <<issued, nativeUnit, stopIntent, revokeAck,
                   spawnedAfterAck>>

\* Physical systemd late launch may win AFTER revoke request COMMIT but
\* BEFORE all native Units have been stopped. That is not yet an ACK.
NativeTargetStart(a) ==
    /\ a \in issued
    /\ nativeUnit[a] = "pending"
    /\ nativeUnit' = [nativeUnit EXCEPT ![a] = "running"]
    /\ spawnedAfterAck' = (spawnedAfterAck \/ revokeAck)
    /\ UNCHANGED <<issuer, issued, stopIntent, fenced, revokeAck>>

RequestStop(a) ==
    /\ issuer = "revoked"
    /\ a \in issued \ stopIntent
    /\ nativeUnit[a] \in {"pending", "running"}
    /\ stopIntent' = stopIntent \cup {a}
    /\ UNCHANGED <<issuer, issued, nativeUnit, fenced, revokeAck,
                   spawnedAfterAck>>

\* Abstract strong observation of no pending manager Job, no PID/cgroup,
\* and no future reissue. Actual OS/root code must qualify this claim.
ObserveQuiet(a) ==
    /\ a \in stopIntent
    /\ nativeUnit[a] \in {"pending", "running"}
    /\ nativeUnit' = [nativeUnit EXCEPT ![a] = "quiescent"]
    /\ UNCHANGED <<issuer, issued, stopIntent, fenced, revokeAck,
                   spawnedAfterAck>>

PublishAck ==
    /\ issuer = "revoked"
    /\ fenced
    /\ ~revokeAck
    /\ \A a \in AttemptIds:
           nativeUnit[a] = "quiescent" /\ a \in stopIntent
    /\ revokeAck' = TRUE
    /\ UNCHANGED <<issuer, issued, nativeUnit, stopIntent, fenced,
                   spawnedAfterAck>>

Next ==
    \/ \E a \in AttemptIds: Issue(a)
    \/ CommitRevoke
    \/ \E a \in AttemptIds: NativeTargetStart(a)
    \/ \E a \in AttemptIds: RequestStop(a)
    \/ \E a \in AttemptIds: ObserveQuiet(a)
    \/ PublishAck

Spec == Init /\ [][Next]_vars

TypeOK ==
    /\ issuer \in {"current", "revoked"}
    /\ issued \subseteq AttemptIds
    /\ nativeUnit \in [AttemptIds -> {"absent", "pending", "running", "quiescent"}]
    /\ stopIntent \subseteq AttemptIds
    /\ fenced \in BOOLEAN
    /\ revokeAck \in BOOLEAN
    /\ spawnedAfterAck \in BOOLEAN

NoSpawnAfterAck == ~spawnedAfterAck
AckRequiresAllIssuedQuiescent ==
    revokeAck => (fenced /\ issuer = "revoked" /\ issued = AttemptIds /\
                  \A a \in AttemptIds:
                      nativeUnit[a] = "quiescent" /\ a \in stopIntent)

\* Intentionally false non-vacuity control in a separate config.
AckUnreachable == ~revokeAck

=============================================================================
