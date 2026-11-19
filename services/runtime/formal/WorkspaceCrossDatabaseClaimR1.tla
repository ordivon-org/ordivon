---------------- MODULE WorkspaceCrossDatabaseClaimR1 ----------------
EXTENDS TLC, FiniteSets

\* Source DESIGN model, not evidence of an installed Runtime Claim API.
\* Production Harness and Runtime can use distinct PostgreSQL databases.
\* Same numeric advisory lock keys are database-local, not a cross-DB fence.
\* This model gives Runtime sole physical Workspace claim/close authority.
\* Harness Run state is independent; its commit does not authorize a Tool.
\* All transitions are atomic abstractions: actual cross-DB handoff needs
\* idempotent claim readback and exact native OPEN/closed-tombstone tests.

RunIds == {"runA", "runB"}
ClaimStates == {"none", "reserved", "active", "released"}
RunStates == {"absent", "prepared", "ready", "finished"}

VARIABLES phase, harness, claim, published, delivered, liveJob, gitDependent

vars == <<phase, harness, claim, published, delivered, liveJob, gitDependent>>

Init ==
    /\ phase = "open"
    /\ harness = [r \in RunIds |-> "absent"]
    /\ claim = [r \in RunIds |-> "none"]
    /\ published = {}
    /\ delivered = {}
    /\ liveJob = FALSE
    /\ gitDependent = FALSE

HarnessPrepare(r) ==
    /\ phase = "open"
    /\ r \in RunIds
    /\ harness[r] = "absent"
    /\ harness' = [harness EXCEPT ![r] = "prepared"]
    /\ UNCHANGED <<phase, claim, published, delivered, liveJob, gitDependent>>

NativeReserve(r) ==
    /\ phase = "open"
    /\ r \in RunIds
    /\ harness[r] = "prepared"
    /\ claim[r] = "none"
    \* Native OPEN record+Git authority check and persistent reserve are one
    \* Runtime-DB atomic action under the existing Workspace close lock.
    /\ claim' = [claim EXCEPT ![r] = "reserved"]
    /\ UNCHANGED <<phase, harness, published, delivered, liveJob, gitDependent>>

HarnessReady(r) ==
    /\ phase = "open"
    /\ r \in RunIds
    /\ harness[r] = "prepared"
    /\ claim[r] = "reserved"
    /\ harness' = [harness EXCEPT ![r] = "ready"]
    /\ UNCHANGED <<phase, claim, published, delivered, liveJob, gitDependent>>

NativeActivate(r) ==
    /\ phase = "open"
    /\ r \in RunIds
    /\ harness[r] = "ready"
    /\ claim[r] = "reserved"
    /\ claim' = [claim EXCEPT ![r] = "active"]
    /\ UNCHANGED <<phase, harness, published, delivered, liveJob, gitDependent>>

PublishToolGrant(r) ==
    /\ phase = "open"
    /\ r \in RunIds
    /\ harness[r] = "ready"
    /\ claim[r] = "active"
    /\ r \notin published
    /\ published' = published \cup {r}
    /\ UNCHANGED <<phase, harness, claim, delivered, liveJob, gitDependent>>

HarnessFinish(r) ==
    /\ phase = "open"
    /\ r \in published
    /\ harness[r] = "ready"
    /\ harness' = [harness EXCEPT ![r] = "finished"]
    /\ UNCHANGED <<phase, claim, published, delivered, liveJob, gitDependent>>

DeliverOutput(r) ==
    /\ phase = "open"
    /\ r \in published
    /\ harness[r] = "finished"
    /\ r \notin delivered
    \* Artifact/Git output exact delivery is a distinct finalizer, not
    \* equivalent to successful Job resolution or elapsed retention time.
    /\ delivered' = delivered \cup {r}
    /\ UNCHANGED <<phase, harness, claim, published, liveJob, gitDependent>>

NativeRelease(r) ==
    /\ phase = "open"
    /\ r \in RunIds
    /\ claim[r] = "active"
    /\ harness[r] = "finished"
    /\ r \in delivered
    /\ claim' = [claim EXCEPT ![r] = "released"]
    /\ UNCHANGED <<phase, harness, published, delivered, liveJob, gitDependent>>

AbortNeverIssuedReservation(r) ==
    /\ phase = "open"
    /\ r \in RunIds
    /\ claim[r] = "reserved"
    /\ r \notin published
    \* Real code MUST prove the grant was never activated or exposed.
    \* A TTL without such proof cannot safely release an active consumer.
    /\ claim' = [claim EXCEPT ![r] = "released"]
    /\ harness' = [harness EXCEPT ![r] = "finished"]
    /\ UNCHANGED <<phase, published, delivered, liveJob, gitDependent>>

BeginJob ==
    /\ phase = "open"
    /\ ~liveJob
    /\ liveJob' = TRUE
    /\ UNCHANGED <<phase, harness, claim, published, delivered, gitDependent>>

EndJob ==
    /\ phase = "open"
    /\ liveJob
    /\ liveJob' = FALSE
    /\ UNCHANGED <<phase, harness, claim, published, delivered, gitDependent>>

AddGitDependent ==
    /\ phase = "open"
    /\ ~gitDependent
    /\ gitDependent' = TRUE
    /\ UNCHANGED <<phase, harness, claim, published, delivered, liveJob>>

RemoveGitDependent ==
    /\ phase = "open"
    /\ gitDependent
    /\ gitDependent' = FALSE
    /\ UNCHANGED <<phase, harness, claim, published, delivered, liveJob>>

Eligible ==
    /\ phase = "open"
    /\ \A r \in RunIds: claim[r] \notin {"reserved", "active"}
    /\ published \subseteq delivered
    /\ ~liveJob
    /\ ~gitDependent

NativeClose ==
    /\ Eligible
    \* Close, reserve and activate share the Runtime DB admission lock.
    /\ phase' = "closed"
    /\ UNCHANGED <<harness, claim, published, delivered, liveJob, gitDependent>>

Progress ==
    \/ \E r \in RunIds: HarnessPrepare(r)
    \/ \E r \in RunIds: NativeReserve(r)
    \/ \E r \in RunIds: HarnessReady(r)
    \/ \E r \in RunIds: NativeActivate(r)
    \/ \E r \in RunIds: PublishToolGrant(r)
    \/ \E r \in RunIds: HarnessFinish(r)
    \/ \E r \in RunIds: DeliverOutput(r)
    \/ \E r \in RunIds: NativeRelease(r)
    \/ \E r \in RunIds: AbortNeverIssuedReservation(r)
    \/ BeginJob
    \/ EndJob
    \/ AddGitDependent
    \/ RemoveGitDependent

SafeNext == Progress \/ NativeClose
SafeSpec == Init /\ [][SafeNext]_vars
FairSafeSpec == SafeSpec /\ WF_vars(NativeClose)

TypeOK ==
    /\ phase \in {"open", "closed"}
    /\ harness \in [RunIds -> RunStates]
    /\ claim \in [RunIds -> ClaimStates]
    /\ published \subseteq RunIds
    /\ delivered \subseteq RunIds
    /\ delivered \subseteq published
    /\ liveJob \in BOOLEAN
    /\ gitDependent \in BOOLEAN

ClosedHasNoOutstandingPins ==
    phase = "closed" =>
        (\A r \in RunIds: claim[r] \notin {"reserved", "active"})

UnreleasedGrantsHeld ==
    \A r \in published \ delivered: claim[r] = "active"

ClosedHasDeliveredOutputs ==
    phase = "closed" => published \subseteq delivered

ClosedHasNoPhysicalDependencies ==
    phase = "closed" => ~liveJob /\ ~gitDependent

StableEligibleEventuallyClosed ==
    (<>[]Eligible) => <> (phase = "closed")

\* This should be FALSE: prove a real close is reachable, not vacuous.
ClosedUnreachable == phase # "closed"

\* Bad production assumption: separate Harness DB advisory lock has the
\* same integer as Runtime. Native Close sees no local Job and closes,
\* while Harness has a long Run claim in its other database.
UnsafeCrossDatabaseClose ==
    /\ phase = "open"
    /\ ~liveJob
    /\ ~gitDependent
    /\ phase' = "closed"
    /\ UNCHANGED <<harness, claim, published, delivered, liveJob, gitDependent>>

UnsafeCrossDbSpec == Init /\ [][Progress \/ UnsafeCrossDatabaseClose]_vars

\* Second bad case: after native closed tombstone, another database
\* admits a claim using its own lock, never checking Runtime OPEN state.
UnsafeLateForeignClaim(r) ==
    /\ phase = "closed"
    /\ r \in RunIds
    /\ claim[r] = "none"
    /\ claim' = [claim EXCEPT ![r] = "reserved"]
    /\ UNCHANGED <<phase, harness, published, delivered, liveJob, gitDependent>>

UnsafeLateSpec ==
    Init /\ [][SafeNext \/ (\E r \in RunIds: UnsafeLateForeignClaim(r))]_vars

\* Third bad case: a Tool receives a grant based solely on Harness READY
\* without Runtime ACTIVE proof. Source-only handshake is not Tool authority.
UnsafeUnqualifiedGrant(r) ==
    /\ phase = "open"
    /\ r \in RunIds
    /\ harness[r] = "prepared"
    /\ r \notin published
    /\ published' = published \cup {r}
    /\ UNCHANGED <<phase, harness, claim, delivered, liveJob, gitDependent>>

UnsafeGrantSpec ==
    Init /\ [][SafeNext \/ (\E r \in RunIds: UnsafeUnqualifiedGrant(r))]_vars
=============================================================================
