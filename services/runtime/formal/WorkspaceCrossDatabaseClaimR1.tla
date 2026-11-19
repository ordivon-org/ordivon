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
WorkspaceIds == {"wa", "wb"}
WorkspaceValues == WorkspaceIds \cup {"unknown"}
ClaimStates == {"none", "reserved", "active", "released"}
RunStates == {"absent", "prepared", "ready", "finished"}

VARIABLES phase, harness, claim, originalWorkspace, claimWorkspace, published, delivered, liveJob, gitDependent

vars == <<phase, harness, claim, originalWorkspace, claimWorkspace, published, delivered, liveJob, gitDependent>>

Init ==
    /\ phase = "open"
    /\ harness = [r \in RunIds |-> "absent"]
    /\ claim = [r \in RunIds |-> "none"]
    /\ originalWorkspace = [r \in RunIds |-> "unknown"]
    /\ claimWorkspace = [r \in RunIds |-> "unknown"]
    /\ published = {}
    /\ delivered = {}
    /\ liveJob = FALSE
    /\ gitDependent = FALSE

HarnessPrepare(r,w) ==
    /\ phase = "open"
    /\ r \in RunIds
    /\ w \in WorkspaceIds
    /\ harness[r] = "absent"
    \* Original Workspace must be frozen at the same authoritative PG Run birth,
    \* not supplied for the first time by a later Agent on open/retry.
    /\ harness' = [harness EXCEPT ![r] = "prepared"]
    /\ originalWorkspace' = [originalWorkspace EXCEPT ![r] = w]
    /\ UNCHANGED <<phase, claim, claimWorkspace, published, delivered, liveJob, gitDependent>>

LegacyPrepareWithoutOriginal(r) ==
    /\ phase = "open"
    /\ r \in RunIds
    /\ harness[r] = "absent"
    \* A historical Run with no persisted original Workspace stays UNKNOWN.
    /\ harness' = [harness EXCEPT ![r] = "prepared"]
    /\ UNCHANGED <<phase, claim, originalWorkspace, claimWorkspace, published, delivered, liveJob, gitDependent>>

NativeReserve(r,w) ==
    /\ phase = "open"
    /\ r \in RunIds
    /\ w \in WorkspaceIds
    /\ harness[r] = "prepared"
    /\ claim[r] = "none"
    /\ claimWorkspace[r] = "unknown"
    /\ originalWorkspace[r] = w
    \* Runtime owns the native OPEN/Git/source/Claim commit under its lock,
    \* but original Workspace identity must come from the immutable Run birth.
    /\ claim' = [claim EXCEPT ![r] = "reserved"]
    /\ claimWorkspace' = [claimWorkspace EXCEPT ![r] = w]
    /\ UNCHANGED <<phase, harness, originalWorkspace, published, delivered, liveJob, gitDependent>>

HarnessReady(r) ==
    /\ phase = "open"
    /\ r \in RunIds
    /\ harness[r] = "prepared"
    /\ claim[r] = "reserved"
    /\ harness' = [harness EXCEPT ![r] = "ready"]
    /\ UNCHANGED <<phase, claim, published, delivered, liveJob, gitDependent, originalWorkspace, claimWorkspace>>

NativeActivate(r) ==
    /\ phase = "open"
    /\ r \in RunIds
    /\ harness[r] = "ready"
    /\ claim[r] = "reserved"
    /\ claim' = [claim EXCEPT ![r] = "active"]
    /\ UNCHANGED <<phase, harness, published, delivered, liveJob, gitDependent, originalWorkspace, claimWorkspace>>

PublishToolGrant(r) ==
    /\ phase = "open"
    /\ r \in RunIds
    /\ harness[r] = "ready"
    /\ claim[r] = "active"
    /\ r \notin published
    /\ published' = published \cup {r}
    /\ UNCHANGED <<phase, harness, claim, delivered, liveJob, gitDependent, originalWorkspace, claimWorkspace>>

HarnessFinish(r) ==
    /\ phase = "open"
    /\ r \in published
    /\ harness[r] = "ready"
    /\ harness' = [harness EXCEPT ![r] = "finished"]
    /\ UNCHANGED <<phase, claim, published, delivered, liveJob, gitDependent, originalWorkspace, claimWorkspace>>

DeliverOutput(r) ==
    /\ phase = "open"
    /\ r \in published
    /\ harness[r] = "finished"
    /\ r \notin delivered
    \* Artifact/Git output exact delivery is a distinct finalizer, not
    \* equivalent to successful Job resolution or elapsed retention time.
    /\ delivered' = delivered \cup {r}
    /\ UNCHANGED <<phase, harness, claim, published, liveJob, gitDependent, originalWorkspace, claimWorkspace>>

NativeRelease(r) ==
    /\ phase = "open"
    /\ r \in RunIds
    /\ claim[r] = "active"
    /\ harness[r] = "finished"
    /\ r \in delivered
    /\ claim' = [claim EXCEPT ![r] = "released"]
    /\ UNCHANGED <<phase, harness, published, delivered, liveJob, gitDependent, originalWorkspace, claimWorkspace>>

AbortNeverIssuedReservation(r) ==
    /\ phase = "open"
    /\ r \in RunIds
    /\ claim[r] = "reserved"
    /\ r \notin published
    \* Real code MUST prove the grant was never activated or exposed.
    \* A TTL without such proof cannot safely release an active consumer.
    /\ claim' = [claim EXCEPT ![r] = "released"]
    /\ harness' = [harness EXCEPT ![r] = "finished"]
    /\ UNCHANGED <<phase, published, delivered, liveJob, gitDependent, originalWorkspace, claimWorkspace>>

BeginJob ==
    /\ phase = "open"
    /\ ~liveJob
    /\ liveJob' = TRUE
    /\ UNCHANGED <<phase, harness, claim, published, delivered, gitDependent, originalWorkspace, claimWorkspace>>

EndJob ==
    /\ phase = "open"
    /\ liveJob
    /\ liveJob' = FALSE
    /\ UNCHANGED <<phase, harness, claim, published, delivered, gitDependent, originalWorkspace, claimWorkspace>>

AddGitDependent ==
    /\ phase = "open"
    /\ ~gitDependent
    /\ gitDependent' = TRUE
    /\ UNCHANGED <<phase, harness, claim, published, delivered, liveJob, originalWorkspace, claimWorkspace>>

RemoveGitDependent ==
    /\ phase = "open"
    /\ gitDependent
    /\ gitDependent' = FALSE
    /\ UNCHANGED <<phase, harness, claim, published, delivered, liveJob, originalWorkspace, claimWorkspace>>

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
    /\ UNCHANGED <<harness, claim, published, delivered, liveJob, gitDependent, originalWorkspace, claimWorkspace>>

Progress ==
    \/ \E r \in RunIds: \E w \in WorkspaceIds: HarnessPrepare(r,w)
    \/ \E r \in RunIds: LegacyPrepareWithoutOriginal(r)
    \/ \E r \in RunIds: \E w \in WorkspaceIds: NativeReserve(r,w)
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
    /\ originalWorkspace \in [RunIds -> WorkspaceValues]
    /\ claimWorkspace \in [RunIds -> WorkspaceValues]
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

\* Desired contract for a long-lived Original Run; this is NOT presently
\* enforced by the installed Runtime workspace.claim.release. Native release
\* can be called by the owning Principal while Harness is still CREATED.
\* A trusted completion/abort certification is required, not a caller Boolean.
ReleaseRequiresOriginalFinalization ==
    \A r \in RunIds: claim[r] = "released" => harness[r] = "finished"

\* Domain-accepted *original bytes* are distinct from Harness COMPLETED.
\* The "delivered" set represents an INDEPENDENT recipient truth source; a
\* self-certified "accepted" Boolean or always-TRUE callback cannot enter it.
ReleaseRequiresIndependentDelivery ==
    \A r \in published: claim[r] = "released" => r \in delivered

\* A native close must not follow a prematurely released original Workspace.
ClosedHasNoPrematurelyReleasedConsumers ==
    phase = "closed" =>
        (\A r \in RunIds:
            (originalWorkspace[r] \in WorkspaceIds /\ claim[r] = "released") =>
                harness[r] = "finished")

ClosedHasDeliveredOutputs ==
    phase = "closed" => published \subseteq delivered

ClosedHasNoPhysicalDependencies ==
    phase = "closed" => ~liveJob /\ ~gitDependent

\* An original old PG Run may exist without a trusted birth Workspace.
\* A caller-selected W2 cannot be promoted into W1 merely because Claim.get
\* returns NOT_FOUND. Existing Run recovery must use original Source evidence.
ClaimBoundToOriginal ==
    \A r \in RunIds:
        claim[r] \in {"reserved", "active", "released"} =>
            (originalWorkspace[r] \in WorkspaceIds /\
             claimWorkspace[r] = originalWorkspace[r])

\* Should be FALSE: native Claims with trustworthy Workspace births are reachable.
NoOriginalClaimEver == \A r \in RunIds: claim[r] = "none"

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
    /\ UNCHANGED <<harness, claim, published, delivered, liveJob, gitDependent, originalWorkspace, claimWorkspace>>

UnsafeCrossDbSpec == Init /\ [][Progress \/ UnsafeCrossDatabaseClose]_vars

\* Second bad case: after native closed tombstone, another database
\* admits a claim using its own lock, never checking Runtime OPEN state.
UnsafeLateForeignClaim(r) ==
    /\ phase = "closed"
    /\ r \in RunIds
    /\ claim[r] = "none"
    /\ claim' = [claim EXCEPT ![r] = "reserved"]
    /\ UNCHANGED <<phase, harness, published, delivered, liveJob, gitDependent, originalWorkspace, claimWorkspace>>

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
    /\ UNCHANGED <<phase, harness, claim, delivered, liveJob, gitDependent, originalWorkspace, claimWorkspace>>

UnsafeGrantSpec ==
    Init /\ [][SafeNext \/ (\E r \in RunIds: UnsafeUnqualifiedGrant(r))]_vars

\* Falsifier of old-Run identity: an existing legacy PG Run has UNKNOWN origin,
\* but the later Agent chooses a physically valid W2 and reserves a new Claim.
\* This must violate ClaimBoundToOriginal; Runtime HELD alone is insufficient.
UnsafeCallerAdoptsLegacy(r,w) ==
    /\ phase = "open"
    /\ r \in RunIds
    /\ w \in WorkspaceIds
    /\ harness[r] = "prepared"
    /\ originalWorkspace[r] = "unknown"
    /\ claim[r] = "none"
    /\ claim' = [claim EXCEPT ![r] = "reserved"]
    /\ claimWorkspace' = [claimWorkspace EXCEPT ![r] = w]
    /\ UNCHANGED <<phase, harness, originalWorkspace, published, delivered, liveJob, gitDependent>>

UnsafeAdoptionSpec ==
    Init /\ [][SafeNext \/ (\E r \in RunIds: \E w \in WorkspaceIds:
        UnsafeCallerAdoptsLegacy(r,w))]_vars
\* Separate residual hazard: a Legacy Run with no native Claim can still
\* lose its physical Workspace. Runtime cannot infer foreign PG Run existence.
\* This MUST be falsifiable under SafeSpec, not claimed as protected.
LegacyUnclaimedRunPreserved ==
    \A r \in RunIds:
        (harness[r] = "prepared" /\ originalWorkspace[r] = "unknown") =>
            phase = "open"

\* Even a trusted original W1 is unsafe if a later caller silently changes
\* the Native Claim to W2 rather than preserving the immutable Run binding.
UnsafeCallerRebindKnown(r,w) ==
    /\ phase = "open"
    /\ r \in RunIds
    /\ w \in WorkspaceIds
    /\ harness[r] = "prepared"
    /\ originalWorkspace[r] \in WorkspaceIds
    /\ w # originalWorkspace[r]
    /\ claim[r] = "none"
    /\ claim' = [claim EXCEPT ![r] = "reserved"]
    /\ claimWorkspace' = [claimWorkspace EXCEPT ![r] = w]
    /\ UNCHANGED <<phase, harness, originalWorkspace, published, delivered, liveJob, gitDependent>>

UnsafeKnownRebindSpec ==
    Init /\ [][SafeNext \/ (\E r \in RunIds: \E w \in WorkspaceIds:
        UnsafeCallerRebindKnown(r,w))]_vars

\* Current installed-native negative counterexample (2026-11-20):
\* an authenticated original principal can directly invoke
\* workspace.claim.release(clientRequestId), bypassing Harness terminal and
\* recipient byte acknowledgment. Physical close is then admissible.
\* Do not misread SafeSpec PASS as a claim that installed Rust enforces this.
UnsafeDirectCallerRelease(r) ==
    /\ phase = "open"
    /\ r \in RunIds
    /\ originalWorkspace[r] \in WorkspaceIds
    /\ claim[r] = "reserved"
    /\ harness[r] = "prepared"
    /\ claim' = [claim EXCEPT ![r] = "released"]
    /\ UNCHANGED <<phase, harness, published, delivered, liveJob, gitDependent, originalWorkspace, claimWorkspace>>

UnsafeDirectReleaseSpec ==
    Init /\ [][SafeNext \/ (\E r \in RunIds: UnsafeDirectCallerRelease(r))]_vars

\* R29 physical RED: original Harness PG reports COMPLETED, but no separate
\* recipient received bytes. The caller manufactures an ACK using its own
\* Run receipt digest, accepted=TRUE and verifier_callback=lambda: TRUE;
\* the dedicated Claim-only principal then releases the Native claim.
\* This source action deliberately violates independent Domain acceptance
\* while passing the weaker original Harness terminal-state predicate.
UnsafeCallerForgedDeliveryRelease(r) ==
    /\ phase = "open"
    /\ r \in published
    /\ harness[r] = "finished"
    /\ claim[r] = "active"
    /\ r \notin delivered
    /\ claim' = [claim EXCEPT ![r] = "released"]
    /\ UNCHANGED <<phase, harness, published, delivered, liveJob, gitDependent, originalWorkspace, claimWorkspace>>

UnsafeForgedAckSpec ==
    Init /\ [][SafeNext \/ (\E r \in RunIds: UnsafeCallerForgedDeliveryRelease(r))]_vars
=============================================================================
