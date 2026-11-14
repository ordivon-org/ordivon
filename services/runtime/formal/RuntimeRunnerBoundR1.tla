-------------------- MODULE RuntimeRunnerBoundR1 --------------------
EXTENDS Naturals

\* Narrow refinement of durable PG dispatch intent versus actual Runner start.
\* "nativeEvidence=matching" is a trusted external witness assumption:
\* real Core must independently compare Runner receipt, systemd identity,
\* kernel PID birth, exact Job/Attempt, and the current PG writer epoch.
\* This model does not prove those operating-system observations.
VARIABLES state, dispatchCount, nativeEvidence, boundCount,
          cancelIntent, nativeStop, resultEvidence, writerCurrent
vars == <<state, dispatchCount, nativeEvidence, boundCount,
          cancelIntent, nativeStop, resultEvidence, writerCurrent>>

States == {"accepted","starting","running","stopping","succeeded","cancelled"}
Evidence == {"missing","foreign","matching"}

Init ==
    /\ state = "accepted"
    /\ dispatchCount = 0
    /\ nativeEvidence = "missing"
    /\ boundCount = 0
    /\ cancelIntent = FALSE
    /\ nativeStop = FALSE
    /\ resultEvidence = "missing"
    /\ writerCurrent = TRUE

IssueDispatch ==
    /\ state = "accepted"
    /\ dispatchCount = 0
    /\ writerCurrent
    /\ ~cancelIntent
    /\ state' = "starting"
    /\ dispatchCount' = 1
    /\ UNCHANGED <<nativeEvidence,boundCount,cancelIntent,nativeStop,resultEvidence,writerCurrent>>

ObserveMatchingNative ==
    /\ state = "starting"
    /\ nativeEvidence = "missing"
    /\ nativeEvidence' = "matching"
    /\ UNCHANGED <<state,dispatchCount,boundCount,cancelIntent,nativeStop,resultEvidence,writerCurrent>>

ObserveForeignNative ==
    /\ state = "starting"
    /\ nativeEvidence = "missing"
    /\ nativeEvidence' = "foreign"
    /\ UNCHANGED <<state,dispatchCount,boundCount,cancelIntent,nativeStop,resultEvidence,writerCurrent>>

CorrectForeignNative ==
    /\ state = "starting"
    /\ nativeEvidence = "foreign"
    /\ nativeEvidence' = "matching"
    /\ UNCHANGED <<state,dispatchCount,boundCount,cancelIntent,nativeStop,resultEvidence,writerCurrent>>

RunnerBound ==
    /\ state = "starting"
    /\ dispatchCount = 1
    /\ nativeEvidence = "matching"
    /\ boundCount = 0
    /\ writerCurrent
    /\ ~cancelIntent
    /\ state' = "running"
    /\ boundCount' = 1
    /\ UNCHANGED <<dispatchCount,nativeEvidence,cancelIntent,nativeStop,resultEvidence,writerCurrent>>

RequestStop ==
    /\ state \in {"accepted","starting","running"}
    /\ ~cancelIntent
    /\ state' = "stopping"
    /\ cancelIntent' = TRUE
    /\ UNCHANGED <<dispatchCount,nativeEvidence,boundCount,nativeStop,resultEvidence,writerCurrent>>

ObserveNativeStop ==
    /\ state = "stopping"
    /\ ~nativeStop
    /\ nativeStop' = TRUE
    /\ UNCHANGED <<state,dispatchCount,nativeEvidence,boundCount,cancelIntent,resultEvidence,writerCurrent>>

CommitCancellation ==
    /\ state = "stopping"
    /\ nativeStop
    /\ writerCurrent
    /\ state' = "cancelled"
    /\ UNCHANGED <<dispatchCount,nativeEvidence,boundCount,cancelIntent,nativeStop,resultEvidence,writerCurrent>>

ObserveMatchingResult ==
    /\ state \in {"starting","running"}
    /\ resultEvidence = "missing"
    /\ resultEvidence' = "matching"
    /\ UNCHANGED <<state,dispatchCount,nativeEvidence,boundCount,cancelIntent,nativeStop,writerCurrent>>

CommitResult ==
    /\ state \in {"starting","running"}
    /\ ~cancelIntent
    /\ resultEvidence = "matching"
    /\ writerCurrent
    /\ state' = "succeeded"
    /\ UNCHANGED <<dispatchCount,nativeEvidence,boundCount,cancelIntent,nativeStop,resultEvidence,writerCurrent>>

RevokeWriter ==
    /\ writerCurrent
    /\ writerCurrent' = FALSE
    /\ UNCHANGED <<state,dispatchCount,nativeEvidence,boundCount,cancelIntent,nativeStop,resultEvidence>>

Next ==
    \/ IssueDispatch
    \/ ObserveMatchingNative
    \/ ObserveForeignNative
    \/ CorrectForeignNative
    \/ RunnerBound
    \/ RequestStop
    \/ ObserveNativeStop
    \/ CommitCancellation
    \/ ObserveMatchingResult
    \/ CommitResult
    \/ RevokeWriter

Spec == Init /\ [][Next]_vars

TypeOK ==
    /\ state \in States
    /\ dispatchCount \in 0..1
    /\ nativeEvidence \in Evidence
    /\ boundCount \in 0..2
    /\ cancelIntent \in BOOLEAN
    /\ nativeStop \in BOOLEAN
    /\ resultEvidence \in {"missing","matching"}
    /\ writerCurrent \in BOOLEAN

RunningRequiresBoundNative ==
    state = "running" =>
        /\ dispatchCount = 1
        /\ boundCount = 1
        /\ nativeEvidence = "matching"
        /\ ~cancelIntent

NoDuplicateRunnerBound == boundCount <= 1
CancelledRequiresPhysicalStop == state = "cancelled" => cancelIntent /\ nativeStop
TerminalRequiresMatchingResult == state = "succeeded" => resultEvidence = "matching"
NoSuccessAfterCancel == state = "succeeded" => ~cancelIntent

\* Deliberately false when legitimate positive native binding is reachable.
NeverBound == boundCount = 0
=============================================================================
