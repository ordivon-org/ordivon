--------------------- MODULE RuntimeWindowsPgAttemptR1 ---------------------
EXTENDS Naturals
\* One native Windows PostgreSQL Attempt. Bounded model, not proof of
\* Win32 / Rust / network implementation. A result.json is untrusted.
\* A named JobObject Empty may be observed only while the ORIGINAL Launcher
\* still holds its handle. A live bound OS pipe + PID/birth + direct kernel
\* ActiveProcesses=0 and original client PID validation are confirmed by
\* the Launcher sending Ready R; ONLY THEN is the observation recorded in
\* the EXISTING PG Journal. After COMMIT the parent sends ACK T.
\* After ACK and launcher exit, the JobObject may be NotFound. Only the
\* durable issuer-qualified positive event plus exact exited-owner permits
\* PG terminalization. Do not ever infer Empty from NotFound.
VARIABLES job, bundle, launch, witness, osOwner, jobObject, jobHandle,
          result, nativeDrainJournal, peerReady, writer
Vars == <<job, bundle, launch, witness, osOwner, jobObject, jobHandle,
          result, nativeDrainJournal, peerReady, writer>>

Init ==
    /\ job = "accepted"
    /\ bundle = FALSE
    /\ launch = FALSE
    /\ witness = "none"
    /\ osOwner = "unknown"
    /\ jobObject = "unknown"
    /\ jobHandle = "absent"
    /\ result = FALSE
    /\ nativeDrainJournal = FALSE
    /\ peerReady = FALSE
    /\ writer = TRUE

CommitImmutableBundle ==
    /\ job = "accepted"
    /\ ~bundle
    /\ bundle' = TRUE
    /\ UNCHANGED <<job, launch, witness, osOwner, jobObject, jobHandle,
                   result, nativeDrainJournal, peerReady, writer>>

IssueOnce ==
    /\ job = "accepted"
    /\ bundle
    /\ writer
    /\ ~launch
    /\ job' = "starting"
    /\ launch' = TRUE
    /\ UNCHANGED <<bundle, witness, osOwner, jobObject, jobHandle,
                   result, nativeDrainJournal, peerReady, writer>>

ObserveLauncher ==
    /\ job = "starting"
    /\ launch
    /\ witness = "none"
    /\ osOwner = "unknown"
    /\ witness' = "launcher"
    /\ osOwner' = "alive"
    /\ jobHandle' = "held"
    /\ UNCHANGED <<job, bundle, launch, jobObject,
                   result, nativeDrainJournal, peerReady, writer>>

ObserveTarget ==
    /\ witness = "launcher"
    /\ job = "starting"
    /\ witness' = "target"
    /\ UNCHANGED <<job, bundle, launch, osOwner, jobObject, jobHandle,
                   result, nativeDrainJournal, peerReady, writer>>

ObserveResult ==
    /\ job = "starting"
    /\ witness = "target"
    /\ ~result
    /\ result' = TRUE
    /\ witness' = "result"
    /\ UNCHANGED <<job, bundle, launch, osOwner, jobObject, jobHandle,
                   nativeDrainJournal, peerReady, writer>>

\* Unacknowledged launcher failure can close the last handle.
\* It must NOT transform a missing native observation into success.
OsExited ==
    /\ job = "starting"
    /\ osOwner = "alive"
    /\ ~nativeDrainJournal
    /\ osOwner' = "exited"
    /\ jobHandle' = "gone"
    /\ jobObject' = "not_found"
    /\ UNCHANGED <<job, bundle, launch, witness, result,
                   nativeDrainJournal, peerReady, writer>>

OsPidReused ==
    /\ job = "starting"
    /\ osOwner = "alive"
    /\ osOwner' = "identity_conflict"
    /\ UNCHANGED <<job, bundle, launch, witness, jobObject, jobHandle,
                   result, nativeDrainJournal, peerReady, writer>>

OsObservationLost ==
    /\ job = "starting"
    /\ osOwner = "alive"
    /\ osOwner' = "unknown"
    /\ UNCHANGED <<job, bundle, launch, witness, jobObject, jobHandle,
                   result, nativeDrainJournal, peerReady, writer>>

ObserveJobObjectPopulated ==
    /\ job = "starting"
    /\ witness # "none"
    /\ jobHandle = "held"
    /\ jobObject' = "populated"
    /\ UNCHANGED <<job, bundle, launch, witness, osOwner, jobHandle,
                   result, nativeDrainJournal, peerReady, writer>>

ObserveJobObjectEmpty ==
    /\ job = "starting"
    /\ witness # "none"
    /\ osOwner = "alive"
    /\ jobHandle = "held"
    /\ jobObject' = "empty"
    /\ UNCHANGED <<job, bundle, launch, witness, osOwner, jobHandle,
                   result, nativeDrainJournal, peerReady, writer>>

ObserveJobObjectNotFound ==
    /\ job = "starting"
    /\ witness # "none"
    /\ jobHandle = "gone"
    /\ jobObject' = "not_found"
    /\ UNCHANGED <<job, bundle, launch, witness, osOwner, jobHandle,
                   result, nativeDrainJournal, peerReady, writer>>

ObserveJobObjectUnknown ==
    /\ job = "starting"
    /\ witness # "none"
    /\ jobObject' = "unknown"
    /\ UNCHANGED <<job, bundle, launch, witness, osOwner, jobHandle,
                   result, nativeDrainJournal, peerReady, writer>>

\* Launcher-side GetNamedPipeClientProcessId must first confirm the
\* original admission-frozen parent PID, and original parent kernel checks
\* Launcher PID, creation time and real JobObject Empty. Here peerReady is
\* the bounded OS-confirmed Ready ('R') byte, NOT a JSON caller declaration.
SignalIssuerReady ==
    /\ job = "starting"
    /\ writer
    /\ witness = "result"
    /\ result
    /\ osOwner = "alive"
    /\ jobHandle = "held"
    /\ jobObject = "empty"
    /\ ~peerReady
    /\ peerReady' = TRUE
    /\ UNCHANGED <<job,bundle,launch,witness,osOwner,jobObject,jobHandle,
                   result,nativeDrainJournal,writer>>

\* The OS writer directly observes the ORIGINAL object while it exists,
\* and the existing PostgreSQL Job journal durably commits this exact event.
CommitTrustedNativeDrainJournal ==
    /\ job = "starting"
    /\ writer
    /\ witness = "result"
    /\ result
    /\ osOwner = "alive"
    /\ jobHandle = "held"
    /\ jobObject = "empty"
    /\ peerReady
    /\ ~nativeDrainJournal
    /\ nativeDrainJournal' = TRUE
    /\ UNCHANGED <<job, bundle, launch, witness, osOwner, jobObject, jobHandle,
                   result, peerReady, writer>>

\* ACK after event commit. The named object is destroyed by Windows; this
\* is NOT a negative observation and does not revoke the prior kernel proof.
AcknowledgeAndCloseOriginalLauncher ==
    /\ job = "starting"
    /\ nativeDrainJournal
    /\ jobHandle = "held"
    /\ osOwner = "alive"
    /\ jobHandle' = "gone"
    /\ osOwner' = "exited"
    /\ jobObject' = "not_found"
    /\ UNCHANGED <<job, bundle, launch, witness, result,
                   nativeDrainJournal, peerReady, writer>>

RevokeWriter ==
    /\ job # "terminal"
    /\ writer
    /\ writer' = FALSE
    /\ UNCHANGED <<job, bundle, launch, witness, osOwner, jobObject, jobHandle,
                   result, nativeDrainJournal, peerReady>>

CommitPgTerminal ==
    /\ job = "starting"
    /\ writer
    /\ bundle
    /\ launch
    /\ witness = "result"
    /\ result
    /\ osOwner = "exited"
    /\ nativeDrainJournal
    /\ jobHandle = "gone"
    /\ job' = "terminal"
    /\ UNCHANGED <<bundle, launch, witness, osOwner, jobObject, jobHandle,
                   result, nativeDrainJournal, peerReady, writer>>

Next == \/ CommitImmutableBundle \/ IssueOnce \/ ObserveLauncher
     \/ ObserveTarget \/ ObserveResult \/ OsExited
     \/ OsPidReused \/ OsObservationLost \/ ObserveJobObjectPopulated
     \/ ObserveJobObjectEmpty \/ ObserveJobObjectNotFound
     \/ ObserveJobObjectUnknown \/ SignalIssuerReady
     \/ CommitTrustedNativeDrainJournal
     \/ AcknowledgeAndCloseOriginalLauncher \/ RevokeWriter
     \/ CommitPgTerminal

TypeOK ==
    /\ job \in {"accepted", "starting", "terminal"}
    /\ bundle \in BOOLEAN /\ launch \in BOOLEAN /\ result \in BOOLEAN
    /\ writer \in BOOLEAN /\ nativeDrainJournal \in BOOLEAN
    /\ peerReady \in BOOLEAN
    /\ witness \in {"none", "launcher", "target", "result"}
    /\ osOwner \in {"unknown", "alive", "exited", "identity_conflict"}
    /\ jobObject \in {"unknown", "populated", "empty", "not_found"}
    /\ jobHandle \in {"absent", "held", "gone"}

LaunchRequiresCommittedBundle == launch => bundle
TerminalRequiresExactOsExit ==
    job = "terminal" => (osOwner = "exited" /\ witness = "result" /\ result)
NoTerminalOnUnknownOrReusedPid ==
    osOwner \in {"unknown", "identity_conflict"} => job # "terminal"
TerminalRequiresDurableNativeDrain ==
    job = "terminal" => (nativeDrainJournal /\ jobHandle = "gone")
NoTerminalWithoutDurableNativeDrain ==
    ~nativeDrainJournal => job # "terminal"
NativeDrainRequiresBoundResult ==
    nativeDrainJournal => (result /\ witness = "result")
NativeDrainRequiresIssuerReady ==
    nativeDrainJournal => peerReady
\* Anti-vacuity: MUST fail for a valid model with reachable terminal.
NeverTerminal == job # "terminal"
Spec == Init /\ [][Next]_Vars
=============================================================================
