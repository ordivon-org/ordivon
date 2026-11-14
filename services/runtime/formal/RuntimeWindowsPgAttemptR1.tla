--------------------- MODULE RuntimeWindowsPgAttemptR1 ---------------------
EXTENDS Naturals
\* Bounded MODEL of one PG Windows Attempt, not a proof of Rust/Win32 behavior.
\* "OsExited" is a trusted external observation of PID + creation FILETIME.
\* A target-writable result.json alone NEVER establishes OsExited.
VARIABLES job, bundle, launch, witness, osOwner, result, writer
Vars == <<job, bundle, launch, witness, osOwner, result, writer>>

Init ==
    /\ job = "accepted"
    /\ bundle = FALSE
    /\ launch = FALSE
    /\ witness = "none"
    /\ osOwner = "unknown"
    /\ result = FALSE
    /\ writer = TRUE

CommitImmutableBundle ==
    /\ job = "accepted"
    /\ ~bundle
    /\ bundle' = TRUE
    /\ UNCHANGED <<job, launch, witness, osOwner, result, writer>>

IssueOnce ==
    /\ job = "accepted"
    /\ bundle
    /\ writer
    /\ ~launch
    /\ job' = "starting"
    /\ launch' = TRUE
    /\ UNCHANGED <<bundle, witness, osOwner, result, writer>>

ObserveLauncher ==
    /\ job = "starting"
    /\ launch
    /\ witness = "none"
    /\ osOwner = "unknown"
    /\ witness' = "launcher"
    /\ osOwner' = "alive"
    /\ UNCHANGED <<job, bundle, launch, result, writer>>

ObserveTarget ==
    /\ witness = "launcher"
    /\ job = "starting"
    /\ witness' = "target"
    /\ UNCHANGED <<job, bundle, launch, osOwner, result, writer>>

ObserveResult ==
    /\ job = "starting"
    /\ witness = "target"
    /\ ~result
    /\ result' = TRUE
    /\ witness' = "result"
    /\ UNCHANGED <<job, bundle, launch, osOwner, writer>>

OsExited ==
    /\ job = "starting"
    /\ osOwner = "alive"
    /\ osOwner' = "exited"
    /\ UNCHANGED <<job, bundle, launch, witness, result, writer>>

OsPidReused ==
    /\ job = "starting"
    /\ osOwner = "alive"
    /\ osOwner' = "identity_conflict"
    /\ UNCHANGED <<job, bundle, launch, witness, result, writer>>

OsObservationLost ==
    /\ job = "starting"
    /\ osOwner = "alive"
    /\ osOwner' = "unknown"
    /\ UNCHANGED <<job, bundle, launch, witness, result, writer>>

RevokeWriter ==
    /\ job # "terminal"
    /\ writer
    /\ writer' = FALSE
    /\ UNCHANGED <<job, bundle, launch, witness, osOwner, result>>

CommitPgTerminal ==
    /\ job = "starting"
    /\ writer
    /\ bundle
    /\ launch
    /\ witness = "result"
    /\ result
    /\ osOwner = "exited"
    /\ job' = "terminal"
    /\ UNCHANGED <<bundle, launch, witness, osOwner, result, writer>>

Next == \/ CommitImmutableBundle \/ IssueOnce \/ ObserveLauncher
     \/ ObserveTarget \/ ObserveResult \/ OsExited
     \/ OsPidReused \/ OsObservationLost \/ RevokeWriter
     \/ CommitPgTerminal

TypeOK ==
    /\ job \in {"accepted", "starting", "terminal"}
    /\ bundle \in BOOLEAN /\ launch \in BOOLEAN /\ result \in BOOLEAN
    /\ writer \in BOOLEAN
    /\ witness \in {"none", "launcher", "target", "result"}
    /\ osOwner \in {"unknown", "alive", "exited", "identity_conflict"}

LaunchRequiresCommittedBundle == launch => bundle
TerminalRequiresExactOsExit ==
    job = "terminal" => (osOwner = "exited" /\ witness = "result" /\ result)
NoTerminalOnUnknownOrReusedPid ==
    osOwner \in {"unknown", "identity_conflict"} => job # "terminal"
\* Anti-vacuity: this should FAIL in a valid model with a reachable terminal.
NeverTerminal == job # "terminal"
Spec == Init /\ [][Next]_Vars
=============================================================================
