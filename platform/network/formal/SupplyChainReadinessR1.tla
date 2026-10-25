---- MODULE SupplyChainReadinessR1 ----
EXTENDS Naturals

(***************************************************************************)
(* Natural Network N03/N04 owner: one readiness attempt of real consumer  *)
(* consumers/supply-chain/ready.sh. Five allowed HTTP+CONNECT probes;     *)
(* separate disallowed CONNECT denial; shared deadline. No live-network, *)
(* DNS/VPN, privileged process, or deployment claims follow from TLC.      *)
(***************************************************************************)

CONSTANTS TotalOrigins
ASSUME TotalOrigins = 5

Stages == {"origins", "deny-probe", "ready", "failed"}
Denials == {"none", "connect-403", "connect-407", "transport-000",
            "reached-origin-403", "other"}
Failures == {"none", "origin-connect", "origin-status", "origin-transport",
             "deadline", "unknown-transport", "unknown-auth",
             "unknown-origin", "unknown-other"}

VARIABLES stage, originCount, acceptedOrigins, denial, failure, budgetExpired
vars == <<stage, originCount, acceptedOrigins, denial, failure, budgetExpired>>

TypeOK ==
    /\ stage \in Stages
    /\ originCount \in 0..TotalOrigins
    /\ acceptedOrigins \in 0..TotalOrigins
    /\ denial \in Denials
    /\ failure \in Failures
    /\ budgetExpired \in BOOLEAN

Init ==
    /\ stage = "origins"
    /\ originCount = 0
    /\ acceptedOrigins = 0
    /\ denial = "none"
    /\ failure = "none"
    /\ budgetExpired = FALSE

(* A successful required probe is exactly CONNECT=200 AND an allowed
   origin HTTP status from the SAME curl call, not mere TCP/DNS success. *)
ProbeAllowed ==
    /\ stage = "origins"
    /\ originCount < TotalOrigins
    /\ ~budgetExpired
    /\ originCount' = originCount + 1
    /\ acceptedOrigins' = acceptedOrigins + 1
    /\ stage' = IF originCount' = TotalOrigins THEN "deny-probe" ELSE "origins"
    /\ UNCHANGED <<denial, failure, budgetExpired>>

RejectRequired ==
    /\ stage = "origins"
    /\ ~budgetExpired
    /\ \E f \in {"origin-connect", "origin-status", "origin-transport"}:
           failure' = f
    /\ stage' = "failed"
    /\ UNCHANGED <<originCount, acceptedOrigins, denial, budgetExpired>>

RejectUnknown ==
    /\ stage = "deny-probe"
    /\ ~budgetExpired
    /\ \E d \in Denials \ {"none", "connect-403"}:
          /\ denial' = d
          /\ failure' =
               CASE d = "connect-407" -> "unknown-auth"
                 [] d = "transport-000" -> "unknown-transport"
                 [] d = "reached-origin-403" -> "unknown-origin"
                 [] OTHER -> "unknown-other"
    /\ stage' = "failed"
    /\ UNCHANGED <<originCount, acceptedOrigins, budgetExpired>>

AdmitExplicitPolicyDenial ==
    /\ stage = "deny-probe"
    /\ ~budgetExpired
    /\ originCount = TotalOrigins
    /\ acceptedOrigins = TotalOrigins
    /\ denial' = "connect-403"
    /\ stage' = "ready"
    /\ UNCHANGED <<originCount, acceptedOrigins, failure, budgetExpired>>

Expire ==
    /\ stage \in {"origins", "deny-probe"}
    /\ ~budgetExpired
    /\ budgetExpired' = TRUE
    /\ failure' = "deadline"
    /\ stage' = "failed"
    /\ UNCHANGED <<originCount, acceptedOrigins, denial>>

Next ==
    \/ ProbeAllowed
    \/ RejectRequired
    \/ RejectUnknown
    \/ AdmitExplicitPolicyDenial
    \/ Expire

Spec == Init /\ [][Next]_vars

ReadyImpliesAllRequiredOrigins ==
    stage = "ready" => /\ originCount = TotalOrigins
                        /\ acceptedOrigins = TotalOrigins

ReadyImpliesExplicitUnknownDenial ==
    stage = "ready" => denial = "connect-403"

ReadyWithinSharedDeadline == stage = "ready" => ~budgetExpired
ReadyHasNoFailures == stage = "ready" => failure = "none"
NoUnknownDenialBeforeAllowedOrigins ==
    denial # "none" => acceptedOrigins = TotalOrigins

(* Independent intentionally FALSE reachability assertions; require
   witness so a no-dispatch model cannot manufacture a PASS. *)
ReadyIsUnreachable == stage # "ready"
TransportLossIsUnreachable ==
    ~(stage = "failed" /\ failure = "unknown-transport")
ProxyAuthIsUnreachable ==
    ~(stage = "failed" /\ failure = "unknown-auth")
ReachedOriginForbiddenIsUnreachable ==
    ~(stage = "failed" /\ failure = "unknown-origin")
DeadlineFailureIsUnreachable == ~budgetExpired
=============================================================================
