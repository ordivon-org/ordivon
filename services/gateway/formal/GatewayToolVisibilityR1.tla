---------------- MODULE GatewayToolVisibilityR1 ----------------
EXTENDS TLC, FiniteSets

\* Process-static MCP SDK tool projection, not a PDP, Host or Runtime model.
\* Tools are registered, then SDK remove_tool is applied BEFORE publication.
\* A memorized hidden tool name must not reach its natural Owner.

CONSTANTS Tools, CoreTools, CollaborationTools, Profile
ASSUME /\ Tools # {}
       /\ CoreTools \subseteq Tools
       /\ CollaborationTools \subseteq Tools
       /\ CoreTools \subseteq CollaborationTools
       /\ Profile \in {"full", "core", "collaboration"}

ActiveTools == IF Profile = "core" THEN CoreTools
               ELSE IF Profile = "collaboration" THEN CollaborationTools
               ELSE Tools

VARIABLES listed, forwarded, rejected
vars == <<listed, forwarded, rejected>>

Init ==
    /\ listed = {}
    /\ forwarded = {}
    /\ rejected = {}

Discover ==
    /\ listed' = ActiveTools
    /\ UNCHANGED <<forwarded, rejected>>

Call(t) ==
    /\ t \in Tools
    /\ IF t \in ActiveTools
          THEN /\ forwarded' = forwarded \cup {t}
               /\ UNCHANGED rejected
          ELSE /\ rejected' = rejected \cup {t}
               /\ UNCHANGED forwarded
    /\ UNCHANGED listed

Next == Discover \/ (\E t \in Tools: Call(t))
Spec == Init /\ [][Next]_vars

TypeOK ==
    /\ listed \subseteq Tools
    /\ forwarded \subseteq Tools
    /\ rejected \subseteq Tools

ListedOnlyActive == listed \subseteq ActiveTools
ForwardedOnlyActive == forwarded \subseteq ActiveTools
RejectedOnlyHidden == rejected \subseteq (Tools \ ActiveTools)
ForwardAndRejectDisjoint == forwarded \cap rejected = {}

NeverForwarded == forwarded = {}

UnsafeCall(t) ==
    /\ t \in (Tools \ ActiveTools)
    /\ forwarded' = forwarded \cup {t}
    /\ UNCHANGED <<listed, rejected>>

UnsafeNext == Next \/ (\E t \in Tools: UnsafeCall(t))
UnsafeSpec == Init /\ [][UnsafeNext]_vars
===============================================================
