-------------------- MODULE WorkspaceCloseReceiptBindingR1 --------------------
EXTENDS TLC
CONSTANTS IgnoreIdentity, IgnoreDisposition
\* The Runtime is the effect authority. This is a bounded consumer contract:
\* arbitrary wire receipts must not become a false exact observation.
Ids == {"original", "foreign"}
Digests == {"exact", "different"}
Dispositions == {"removed", "already_closed", "unknown"}
ExpectedId == "original"
ExpectedDigest == "exact"
VARIABLES response, standing, newlyRemoved
vars == <<response, standing, newlyRemoved>>
Responses == [id: Ids, digest: Digests, disposition: Dispositions, removed: BOOLEAN]
Init ==
    /\ response \in Responses
    /\ standing = "unobserved"
    /\ newlyRemoved = FALSE
IdentityOK == response.id = ExpectedId /\ response.digest = ExpectedDigest
DispositionOK == \/ (response.disposition = "removed" /\ response.removed)
                 \/ (response.disposition = "already_closed" /\ ~response.removed)
Qualify ==
    /\ standing = "unobserved"
    /\ standing' = IF (IdentityOK \/ IgnoreIdentity) /\ (DispositionOK \/ IgnoreDisposition)
                     THEN "observed" ELSE "unknown"
    /\ newlyRemoved' = (standing' = "observed" /\ response.removed)
    /\ UNCHANGED response
Spec == Init /\ [][Qualify]_vars
TypeOK == /\ response \in Responses
          /\ standing \in {"unobserved","observed","unknown"}
          /\ newlyRemoved \in BOOLEAN
ObservedBindsExact == standing = "observed" => IdentityOK
ObservedDispositionConsistent == standing = "observed" => DispositionOK
ReplayNotNewRemoval == response.disposition = "already_closed" => ~newlyRemoved
NoObserved == standing # "observed"
=============================================================================
