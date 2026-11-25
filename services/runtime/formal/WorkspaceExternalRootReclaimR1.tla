-------------------- MODULE WorkspaceExternalRootReclaimR1 --------------------
EXTENDS TLC
\* Scoped reclaim decision contract. Physical OS root absence is only a
\* bounded observation. The owner fence must prevent new admitted consumers
\* during the modeled effect. External uncoordinated opens are an assumption,
\* not proved by a /proc scan. Refines the existing WorkspaceConsumerCloseR1.
CONSTANT OmitMappedRoot
VARIABLES phase, roots, observation, identity, release, fence
vars == <<phase, roots, observation, identity, release, fence>>
Kinds == {"cwd", "exe", "fd", "mapped"}
Init ==
  /\ phase = "open"
  /\ roots = {}
  /\ observation = "unknown"
  /\ identity = FALSE
  /\ release = FALSE
  /\ fence = FALSE
AddRoot ==
  /\ phase = "open" /\ ~fence
  /\ \E k \in Kinds \ roots: roots' = roots \cup {k}
  /\ observation' = "unknown"
  /\ UNCHANGED <<phase, identity, release, fence>>
DropRoot ==
  /\ phase = "open" /\ ~fence
  /\ \E k \in roots: roots' = roots \ {k}
  /\ observation' = "unknown"
  /\ UNCHANGED <<phase, identity, release, fence>>
AcquireFence ==
  /\ phase = "open" /\ ~fence
  /\ fence' = TRUE
  /\ observation' = "unknown"
  /\ UNCHANGED <<phase, roots, identity, release>>
LoseFence ==
  /\ phase = "open" /\ fence
  /\ fence' = FALSE
  /\ observation' = "unknown"
  /\ UNCHANGED <<phase, roots, identity, release>>
BindIdentity ==
  /\ phase = "open" /\ ~identity
  /\ identity' = TRUE
  /\ UNCHANGED <<phase, roots, observation, release, fence>>
ChangeIdentity ==
  /\ phase = "open" /\ ~fence /\ identity
  /\ identity' = FALSE /\ release' = FALSE
  /\ observation' = "unknown"
  /\ UNCHANGED <<phase, roots, fence>>
OwnerRelease ==
  /\ phase = "open" /\ identity /\ ~release
  /\ release' = TRUE
  /\ UNCHANGED <<phase, roots, observation, identity, fence>>
Observe ==
  /\ phase = "open"
  /\ observation' \in {"unknown", IF (IF OmitMappedRoot
           THEN roots \ {"mapped"} ELSE roots) = {}
           THEN "clear" ELSE "rooted"}
  /\ UNCHANGED <<phase, roots, identity, release, fence>>
Close ==
  /\ phase = "open" /\ identity /\ release /\ fence
  /\ observation = "clear"
  /\ phase' = "closed"
  /\ UNCHANGED <<roots, observation, identity, release, fence>>
Terminal == phase = "closed" /\ UNCHANGED vars
Next == AddRoot \/ DropRoot \/ AcquireFence \/ LoseFence \/ BindIdentity
        \/ ChangeIdentity \/ OwnerRelease \/ Observe \/ Close \/ Terminal
Spec == Init /\ [][Next]_vars
TypeOK ==
  /\ phase \in {"open", "closed"}
  /\ roots \subseteq Kinds
  /\ observation \in {"clear", "rooted", "unknown"}
  /\ identity \in BOOLEAN /\ release \in BOOLEAN /\ fence \in BOOLEAN
ClosedHasNoRoots == phase = "closed" => roots = {}
ClosedHasAuthority == phase = "closed" =>
  (identity /\ release /\ fence /\ observation = "clear")
ClosedUnreachable == phase # "closed"
=============================================================================
