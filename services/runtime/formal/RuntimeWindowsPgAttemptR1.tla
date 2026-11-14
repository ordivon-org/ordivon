--------------------- MODULE RuntimeWindowsPgAttemptR1 ---------------------
EXTENDS Naturals
\* Bounded MODEL of one PG Windows Attempt, not a proof of Rust/Win32 behavior.
\* "OsExited" is a trusted external observation of PID + creation FILETIME.
\* A target-writable result.json alone NEVER establishes OsExited.
\* Win32 Job Object readback is a separately bounded kernel observation:
\* populated, empty, not_found and unknown are distinct. NotFound/Unknown
\* cannot be silently treated as an empty process tree. Even empty is only
\* a NECESSARY observation alongside the exact exited-launcher witness,
\* not a proof that the implementation CAS or installed provider is safe.
VARIABLES job, bundle, launch, witness, osOwner, jobObject, result, writer
Vars == <<job, bundle, launch, witness, osOwner, jobObject, result, writer>>

Init ==
    /\ job = "accepted"
    /\ bundle = FALSE
    /\ launch = FALSE
    /\ witness = "none"
    /\ osOwner = "unknown"
    /\ jobObject = "unknown"
    /\ result = FALSE
    /\ writer = TRUE

CommitImmutableBundle ==
    /\ job = "accepted"
    /\ ~bundle
    /\ bundle' = TRUE
    /\ UNCHANGED <<job, launch, witness, osOwner, jobObject, result, writer>>

IssueOnce ==
    /\ job = "accepted"
    /\ bundle
    /\ writer
    /\ ~launch
    /\ job' = "starting"
    /\ launch' = TRUE
    /\ UNCHANGED <<bundle, witness, osOwner, jobObject, result, writer>>

ObserveLauncher ==
    /\ job = "starting"
    /\ launch
    /\ witness = "none"
    /\ osOwner = "unknown"
    /\ witness' = "launcher"
    /\ osOwner' = "alive"
    /\ UNCHANGED <<job, bundle, launch, jobObject, result, writer>>

ObserveTarget ==
    /\ witness = "launcher"
    /\ job = "starting"
    /\ witness' = "target"
    /\ UNCHANGED <<job, bundle, launch, osOwner, jobObject, result, writer>>

ObserveResult ==
    /\ job = "starting"
    /\ witness = "target"
    /\ ~result
    /\ result' = TRUE
    /\ witness' = "result"
    /\ UNCHANGED <<job, bundle, launch, osOwner, jobObject, writer>>

OsExited ==
    /\ job = "starting"
    /\ osOwner = "alive"
    /\ osOwner' = "exited"
    /\ UNCHANGED <<job, bundle, launch, witness, jobObject, result, writer>>

OsPidReused ==
    /\ job = "starting"
    /\ osOwner = "alive"
    /\ osOwner' = "identity_conflict"
    /\ UNCHANGED <<job, bundle, launch, witness, jobObject, result, writer>>

OsObservationLost ==
    /\ job = "starting"
    /\ osOwner = "alive"
    /\ osOwner' = "unknown"
    /\ UNCHANGED <<job, bundle, launch, witness, jobObject, result, writer>>

ObserveJobObjectPopulated ==
    /\ job = "starting"
    /\ witness # "none"
    /\ jobObject' = "populated"
    /\ UNCHANGED <<job, bundle, launch, witness, osOwner, result, writer>>

ObserveJobObjectEmpty ==
    /\ job = "starting"
    /\ witness # "none"
    /\ jobObject' = "empty"
    /\ UNCHANGED <<job, bundle, launch, witness, osOwner, result, writer>>

ObserveJobObjectNotFound ==
    /\ job = "starting"
    /\ witness # "none"
    /\ jobObject' = "not_found"
    /\ UNCHANGED <<job, bundle, launch, witness, osOwner, result, writer>>

ObserveJobObjectUnknown ==
    /\ job = "starting"
    /\ witness # "none"
    /\ jobObject' = "unknown"
    /\ UNCHANGED <<job, bundle, launch, witness, osOwner, result, writer>>

RevokeWriter ==
    /\ job # "terminal"
    /\ writer
    /\ writer' = FALSE
    /\ UNCHANGED <<job, bundle, launch, witness, osOwner, jobObject, result>>

CommitPgTerminal ==
    /\ job = "starting"
    /\ writer
    /\ bundle
    /\ launch
    /\ witness = "result"
    /\ result
    /\ osOwner = "exited"
    /\ jobObject = "empty"
    /\ job' = "terminal"
    /\ UNCHANGED <<bundle, launch, witness, osOwner, jobObject, result, writer>>

Next == \/ CommitImmutableBundle \/ IssueOnce \/ ObserveLauncher
     \/ ObserveTarget \/ ObserveResult \/ OsExited
     \/ OsPidReused \/ OsObservationLost \/ ObserveJobObjectPopulated
     \/ ObserveJobObjectEmpty \/ ObserveJobObjectNotFound
     \/ ObserveJobObjectUnknown \/ RevokeWriter
     \/ CommitPgTerminal

TypeOK ==
    /\ job \in {"accepted", "starting", "terminal"}
    /\ bundle \in BOOLEAN /\ launch \in BOOLEAN /\ result \in BOOLEAN
    /\ writer \in BOOLEAN
    /\ witness \in {"none", "launcher", "target", "result"}
    /\ osOwner \in {"unknown", "alive", "exited", "identity_conflict"}
    /\ jobObject \in {"unknown", "populated", "empty", "not_found"}

LaunchRequiresCommittedBundle == launch => bundle
TerminalRequiresExactOsExit ==
    job = "terminal" => (osOwner = "exited" /\ witness = "result" /\ result)
NoTerminalOnUnknownOrReusedPid ==
    osOwner \in {"unknown", "identity_conflict"} => job # "terminal"
TerminalRequiresJobObjectEmpty ==
    job = "terminal" => jobObject = "empty"
NoTerminalOnUnknownOrMissingJobObject ==
    jobObject \in {"unknown", "not_found", "populated"} => job # "terminal"
\* Anti-vacuity: this should FAIL in a valid model with a reachable terminal.
NeverTerminal == job # "terminal"
Spec == Init /\ [][Next]_Vars
=============================================================================
