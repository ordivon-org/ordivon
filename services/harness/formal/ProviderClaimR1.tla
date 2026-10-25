---- MODULE ProviderClaimR1 ----
EXTENDS Naturals

(***************************************************************************)
(* Harness Owner abstraction for one durable Provider Call identity.       *)
(* Owner implementation: ordivon/sqlite_run_store.py,                     *)
(* claim_provider_call / mark_provider_call_dispatching /                 *)
(* complete_provider_call, and sqlite_agent_bridge.py.                    *)
(*                                                               *)
(* It does not model arbitrary Runner executions, provider effects,       *)
(* SQLite isolation, tool authority, or the caller's semantic outcome.     *)
(***************************************************************************)

CONSTANTS Holders, Nobody

CallStates == {"none", "claimed", "dispatching", "unknown", "completed"}

VARIABLES call, holder, generation, expired, admittedHolder,
          admittedGeneration, physicalCalls, durableResult, acknowledged

vars == <<call, holder, generation, expired, admittedHolder,
          admittedGeneration, physicalCalls, durableResult, acknowledged>>

TypeOK ==
    /\ Holders # {}
    /\ Nobody \notin Holders
    /\ call \in CallStates
    /\ holder \in Holders \cup {Nobody}
    /\ generation \in 0..2
    /\ expired \in BOOLEAN
    /\ admittedHolder \in Holders \cup {Nobody}
    /\ admittedGeneration \in 0..2
    (* Value 2 is deliberately representable for falsification. *)
    /\ physicalCalls \in 0..2
    /\ durableResult \in BOOLEAN
    /\ acknowledged \in BOOLEAN

Init ==
    /\ call = "none"
    /\ holder = Nobody
    /\ generation = 0
    /\ expired = FALSE
    /\ admittedHolder = Nobody
    /\ admittedGeneration = 0
    /\ physicalCalls = 0
    /\ durableResult = FALSE
    /\ acknowledged = FALSE

Claim ==
    /\ call = "none"
    /\ \E h \in Holders:
          /\ holder' = h
          /\ generation' = 1
    /\ call' = "claimed"
    /\ UNCHANGED <<expired, admittedHolder, admittedGeneration,
                  physicalCalls, durableResult, acknowledged>>

ExpireClaim ==
    /\ call = "claimed"
    /\ ~expired
    /\ expired' = TRUE
    /\ UNCHANGED <<call, holder, generation, admittedHolder,
                  admittedGeneration, physicalCalls, durableResult, acknowledged>>

(* A CLAIMED lease may be replaced; a DISPATCHING call may not.           *)
ReplaceExpiredClaim ==
    /\ call = "claimed"
    /\ expired
    /\ generation = 1
    /\ \E h \in Holders \ {holder} : holder' = h
    /\ generation' = 2
    /\ expired' = FALSE
    /\ UNCHANGED <<call, admittedHolder, admittedGeneration,
                  physicalCalls, durableResult, acknowledged>>

AdmitDispatch ==
    /\ call = "claimed"
    /\ ~expired
    /\ call' = "dispatching"
    /\ admittedHolder' = holder
    /\ admittedGeneration' = generation
    /\ UNCHANGED <<holder, generation, expired,
                  physicalCalls, durableResult, acknowledged>>

PhysicalCall ==
    /\ call = "dispatching"
    /\ physicalCalls = 0
    /\ physicalCalls' = physicalCalls + 1
    /\ UNCHANGED <<call, holder, generation, expired, admittedHolder,
                  admittedGeneration, durableResult, acknowledged>>

(* A lost response cannot be interpreted as absence of physical effects. *)
LoseKnowledge ==
    /\ call = "dispatching"
    /\ call' = "unknown"
    /\ UNCHANGED <<holder, generation, expired, admittedHolder,
                  admittedGeneration, physicalCalls, durableResult, acknowledged>>

CommitResult ==
    /\ call = "dispatching"
    /\ physicalCalls = 1
    /\ call' = "completed"
    /\ durableResult' = TRUE
    /\ UNCHANGED <<holder, generation, expired, admittedHolder,
                  admittedGeneration, physicalCalls, acknowledged>>

DeliverAcknowledgement ==
    /\ call = "completed"
    /\ durableResult
    /\ ~acknowledged
    /\ acknowledged' = TRUE
    /\ UNCHANGED <<call, holder, generation, expired, admittedHolder,
                  admittedGeneration, physicalCalls, durableResult>>

Next ==
    \/ Claim
    \/ ExpireClaim
    \/ ReplaceExpiredClaim
    \/ AdmitDispatch
    \/ PhysicalCall
    \/ LoseKnowledge
    \/ CommitResult
    \/ DeliverAcknowledgement

Spec == Init /\ [][Next]_vars

AtMostOnePhysicalCall == physicalCalls <= 1
CommittedResultNeedsPhysicalEvidence == durableResult => physicalCalls = 1
NoAckWithoutDurableResult == acknowledged => durableResult
AdmittedTokenMustMatchCurrentClaim ==
    call \in {"dispatching", "unknown", "completed"} =>
      /\ holder = admittedHolder
      /\ generation = admittedGeneration
UnknownMustNotBeAcknowledged ==
    call = "unknown" => ~acknowledged
NoPhysicalEffectBeforeDispatch ==
    physicalCalls > 0 => call \in {"dispatching", "unknown", "completed"}

(***************************************************************************)
(* Intentionally FALSE reachability oracles. Must be falsified by TLC.     *)
(* Physical invocation != acknowledged success. Claimed expiry may rebind  *)
(* BEFORE dispatch; completion and an acknowledgment are also reachable.   *)
(***************************************************************************)
UnacknowledgedPhysicalCallIsUnreachable ==
    ~(physicalCalls = 1 /\ ~acknowledged)

ClaimReplacementIsUnreachable ==
    ~(generation = 2 /\ call = "claimed")

DeliveryIsUnreachable == ~acknowledged

=============================================================================
