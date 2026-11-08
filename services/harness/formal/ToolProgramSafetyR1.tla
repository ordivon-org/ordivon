---- MODULE ToolProgramSafetyR1 ----
EXTENDS Naturals

(***************************************************************************)
(* Harness bounded ToolProgram: exact admitted tool surface, physical step *)
(* budget, sequential observation and stopping before later effects.       *)
(*                                                                       *)
(* Owner implementation: src/ordivon_harness/tool_program.py              *)
(*   HarnessToolProgramExecutor.execute                                   *)
(* Wire admission: src/ordivon_harness/tool_program_contract.py            *)
(* Observation shape: src/ordivon_harness/agent_tool_observation.py        *)
(*                                                                       *)
(* Abstractly counts a bridge invocation as one physical Tool Call, not   *)
(* proof that a Runtime side effect happened exactly once. The abstract   *)
(* model DOES NOT assert atomic ToolProgram rollback, real Tool delivery,  *)
(* adapter/protocol behavior, Python refinement, or domain success.       *)
(* The ToolBridge is assumed to return a status matching the invoked      *)
(* call's identity; mismatched receipts raise in the Python implementation. *)
(***************************************************************************)

CONSTANT MaxSteps
ASSUME MaxSteps \in Nat \ {0}

StopOutcomes == {"rejected", "unknown", "cancel-requested", "cancelled"}
Phases == {"offered", "rejected", "running", "awaiting_output",
           "completed", "failed", "stopped"}

VARIABLES phase, admitted, initialBudget, remainingBudget,
          issued, observed, cursor, stopAt, stopStatus

vars == <<phase, admitted, initialBudget, remainingBudget,
          issued, observed, cursor, stopAt, stopStatus>>

TypeOK ==
    /\ phase \in Phases
    /\ admitted \in BOOLEAN
    /\ initialBudget \in 0..MaxSteps
    /\ remainingBudget \in 0..MaxSteps
    /\ issued \in 0..MaxSteps
    /\ observed \in 0..MaxSteps
    /\ cursor \in 1..(MaxSteps + 1)
    /\ stopAt \in 0..MaxSteps
    /\ stopStatus \in StopOutcomes \cup {"none"}

Init ==
    /\ phase = "offered"
    /\ admitted \in BOOLEAN
    /\ initialBudget \in 0..MaxSteps
    /\ remainingBudget = initialBudget
    /\ issued = 0
    /\ observed = 0
    /\ cursor = 1
    /\ stopAt = 0
    /\ stopStatus = "none"

(* The entire validated Program is checked before the first bridge call. *)
RejectBeforeDispatch ==
    /\ phase = "offered"
    /\ (~admitted \/ initialBudget < MaxSteps)
    /\ phase' = "rejected"
    /\ UNCHANGED <<admitted, initialBudget, remainingBudget,
                   issued, observed, cursor, stopAt, stopStatus>>

AdmitProgram ==
    /\ phase = "offered"
    /\ admitted
    /\ initialBudget >= MaxSteps
    /\ phase' = "running"
    /\ UNCHANGED <<admitted, initialBudget, remainingBudget,
                   issued, observed, cursor, stopAt, stopStatus>>

(* Model a single already-admitted Tool call returning an observation. *)
IssueObserved ==
    /\ phase = "running"
    /\ cursor <= MaxSteps
    /\ remainingBudget > 0
    /\ issued' = issued + 1
    /\ observed' = observed + 1
    /\ remainingBudget' = remainingBudget - 1
    /\ cursor' = cursor + 1
    /\ phase' = IF cursor = MaxSteps THEN "awaiting_output" ELSE "running"
    /\ UNCHANGED <<admitted, initialBudget, stopAt, stopStatus>>

IssueUnobserved ==
    /\ phase = "running"
    /\ cursor <= MaxSteps
    /\ remainingBudget > 0
    /\ stopStatus' \in StopOutcomes
    /\ issued' = issued + 1
    /\ remainingBudget' = remainingBudget - 1
    /\ cursor' = cursor + 1
    /\ stopAt' = issued + 1
    /\ phase' = "stopped"
    /\ UNCHANGED <<admitted, initialBudget, observed>>

(* Output reference resolution occurs only after every step is observed; *)
(* failure to resolve returns an error without any additional Tool call.  *)
ResolveOutput ==
    /\ phase = "awaiting_output"
    /\ phase' = "completed"
    /\ UNCHANGED <<admitted, initialBudget, remainingBudget,
                   issued, observed, cursor, stopAt, stopStatus>>

RejectOutput ==
    /\ phase = "awaiting_output"
    /\ phase' = "failed"
    /\ UNCHANGED <<admitted, initialBudget, remainingBudget,
                   issued, observed, cursor, stopAt, stopStatus>>

Next ==
    \/ RejectBeforeDispatch
    \/ AdmitProgram
    \/ IssueObserved
    \/ IssueUnobserved
    \/ ResolveOutput
    \/ RejectOutput

Spec == Init /\ [][Next]_vars

(* Positive safety properties: bounded by the exact finite Model Scope.  *)
NoEffectWithoutAdmission ==
    issued > 0 => (admitted /\ initialBudget >= MaxSteps)

ConservedPhysicalBudget ==
    remainingBudget + issued = initialBudget

SequentialAccounting ==
    /\ cursor = issued + 1
    /\ observed <= issued

NoExtraEffectsAfterStop ==
    stopAt > 0 => (phase = "stopped" /\ issued = stopAt)

StoppedOnlyOnUnobserved ==
    phase = "stopped" => (stopStatus \in StopOutcomes /\ issued > observed)

OnlyObservedCanComplete ==
    phase \in {"awaiting_output", "completed", "failed"} =>
        (issued = MaxSteps /\ observed = MaxSteps)

RejectedBeforeAnyEffect ==
    phase = "rejected" => (issued = 0 /\ observed = 0)

NoAdditionalEffectFromOutput ==
    phase \in {"completed", "failed"} =>
        (issued = MaxSteps /\ remainingBudget = initialBudget - MaxSteps)

(* Intentionally false reachability oracles for independent TLC probes.   *)
UnknownStopIsUnreachable == stopStatus # "unknown"
PartialStoppedEffectIsUnreachable ==
    ~(phase = "stopped" /\ issued > 1 /\ observed > 0)
CompletedProgramIsUnreachable == phase # "completed"

=============================================================================
