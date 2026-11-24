---------------- MODULE WorkspaceCrossDatabaseClaimR1 ----------------
EXTENDS Naturals, TLC, FiniteSets

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

\* Finite subject partition, not a wire format or authentication proof.
\* Exact means original Run/Job/Attempt/Artifact, byte digest and intended
\* independent recipient all match. Foreign classes isolate a mismatch
\* even when the other coordinates (including bytes) match.
SubjectClasses == {"exact", "wrongRun", "wrongJob", "wrongAttempt", "wrongArtifact",
                   "wrongDigest", "wrongRecipient", "unknown"}

\* Fixed finite original output obligations: two distinct subjects for A,
\* zero for B. The actual set must come from the non-reopenable original
\* Run cut, NOT from a partial artifact read or the recipient's claims.
OutputSlots == {"first", "second"}
RequiredOutputs(r) == IF r = "runA" THEN OutputSlots ELSE {}



VARIABLES phase, harness, claim, originalWorkspace, claimWorkspace, published, delivered, censusComplete, recipientWitnesses, liveJob, gitDependent, nativeHandoffPending, nativeHandoffEverQueued

AcceptedOutputs(r) ==
    {o \in RequiredOutputs(r) : <<r,o,"exact">> \in recipientWitnesses}

RecipientAccepted ==
    {r \in censusComplete : RequiredOutputs(r) \subseteq AcceptedOutputs(r)}

vars == <<phase, harness, claim, originalWorkspace, claimWorkspace, published, delivered, censusComplete, recipientWitnesses, liveJob, gitDependent, nativeHandoffPending, nativeHandoffEverQueued>>

Init ==
    /\ phase = "open"
    /\ harness = [r \in RunIds |-> "absent"]
    /\ claim = [r \in RunIds |-> "none"]
    /\ originalWorkspace = [r \in RunIds |-> "unknown"]
    /\ claimWorkspace = [r \in RunIds |-> "unknown"]
    /\ published = {}
    /\ delivered = {}
    /\ censusComplete = {}
    /\ recipientWitnesses = {}
    /\ liveJob = FALSE
    /\ gitDependent = FALSE
    /\ nativeHandoffPending = FALSE
    /\ nativeHandoffEverQueued = FALSE

HarnessPrepare(r,w) ==
    /\ phase = "open"
    /\ r \in RunIds
    /\ w \in WorkspaceIds
    /\ harness[r] = "absent"
    \* Original Workspace must be frozen at the same authoritative PG Run birth,
    \* not supplied for the first time by a later Agent on open/retry.
    /\ harness' = [harness EXCEPT ![r] = "prepared"]
    /\ originalWorkspace' = [originalWorkspace EXCEPT ![r] = w]
    /\ UNCHANGED <<phase, claim, claimWorkspace, published, delivered, liveJob, gitDependent, censusComplete, recipientWitnesses, nativeHandoffPending, nativeHandoffEverQueued>>

LegacyPrepareWithoutOriginal(r) ==
    /\ phase = "open"
    /\ r \in RunIds
    /\ harness[r] = "absent"
    \* A historical Run with no persisted original Workspace stays UNKNOWN.
    /\ harness' = [harness EXCEPT ![r] = "prepared"]
    /\ UNCHANGED <<phase, claim, originalWorkspace, claimWorkspace, published, delivered, liveJob, gitDependent, censusComplete, recipientWitnesses, nativeHandoffPending, nativeHandoffEverQueued>>

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
    /\ UNCHANGED <<phase, harness, originalWorkspace, published, delivered, liveJob, gitDependent, censusComplete, recipientWitnesses, nativeHandoffPending, nativeHandoffEverQueued>>

HarnessReady(r) ==
    /\ phase = "open"
    /\ r \in RunIds
    /\ harness[r] = "prepared"
    /\ claim[r] = "reserved"
    /\ harness' = [harness EXCEPT ![r] = "ready"]
    /\ UNCHANGED <<phase, claim, published, delivered, liveJob, gitDependent, originalWorkspace, claimWorkspace, censusComplete, recipientWitnesses, nativeHandoffPending, nativeHandoffEverQueued>>

NativeActivate(r) ==
    /\ phase = "open"
    /\ r \in RunIds
    /\ harness[r] = "ready"
    /\ claim[r] = "reserved"
    /\ claim' = [claim EXCEPT ![r] = "active"]
    /\ UNCHANGED <<phase, harness, published, delivered, liveJob, gitDependent, originalWorkspace, claimWorkspace, censusComplete, recipientWitnesses, nativeHandoffPending, nativeHandoffEverQueued>>

PublishToolGrant(r) ==
    /\ phase = "open"
    /\ r \in RunIds
    /\ harness[r] = "ready"
    /\ claim[r] = "active"
    /\ r \notin published
    /\ published' = published \cup {r}
    /\ UNCHANGED <<phase, harness, claim, delivered, liveJob, gitDependent, originalWorkspace, claimWorkspace, censusComplete, recipientWitnesses, nativeHandoffPending, nativeHandoffEverQueued>>

HarnessFinish(r) ==
    /\ phase = "open"
    /\ r \in published
    /\ harness[r] = "ready"
    /\ harness' = [harness EXCEPT ![r] = "finished"]
    /\ UNCHANGED <<phase, claim, published, delivered, liveJob, gitDependent, originalWorkspace, claimWorkspace, censusComplete, recipientWitnesses, nativeHandoffPending, nativeHandoffEverQueued>>

DeliverOutput(r) ==
    /\ phase = "open"
    /\ r \in published
    /\ harness[r] = "finished"
    /\ r \notin delivered
    \* Producer/caller has RECORDED delivery; neither original bytes nor
    \* their independent recipient acceptance are yet authenticated here.
    \* Caller accepted=true, digest or a lambda-True verifier is not proof.
    /\ delivered' = delivered \cup {r}
    /\ UNCHANGED <<phase, harness, claim, published, liveJob, gitDependent, originalWorkspace, claimWorkspace, censusComplete, recipientWitnesses, nativeHandoffPending, nativeHandoffEverQueued>>

\* Assumption/authority boundary: this action may be issued ONLY by an
\* independently observed recipient channel. The exact class means original
\* bytes and matching source/destination acceptance were read back. The model does NOT establish
\* this provenance from caller JSON, ActorRef, a digest, or Token possession.
\* A subject observation is not necessarily acceptance; the actual receiver
\* may observe a mismatching or unresolved subject.
IndependentRecipientObserve(r, output, subject) ==
    /\ phase = "open"
    /\ r \in delivered
    /\ output \in RequiredOutputs(r)
    /\ subject \in SubjectClasses
    /\ output \notin AcceptedOutputs(r)
    /\ (subject = "exact" \/
        ~\E c \in SubjectClasses: <<r,output,c>> \in recipientWitnesses)
    /\ harness[r] = "finished"
    /\ recipientWitnesses' =
        (recipientWitnesses \ {<<r,output,c>> : c \in SubjectClasses})
        \cup {<<r,output,subject>>}
    /\ UNCHANGED <<phase, harness, claim, originalWorkspace, claimWorkspace,
                  published, delivered, censusComplete, liveJob, gitDependent,
                  nativeHandoffPending, nativeHandoffEverQueued>>

\* A separate authority-qualified COMPLETE original census at the terminal
\* cut. This is an abstract proof obligation, not an implementation of
\* output discovery. Qualification for release is published only after the
\* producer's delivery record (capture may precede it); an absent/partial
\* census stays incomplete even if the
\* observed set happens to be empty. It cannot be reopened in this model.
QualifyCompleteOutputCensus(r) ==
    /\ phase = "open"
    /\ r \in delivered
    /\ harness[r] = "finished"
    /\ r \notin censusComplete
    /\ censusComplete' = censusComplete \cup {r}
    /\ UNCHANGED <<phase, harness, claim, originalWorkspace, claimWorkspace,
                  published, delivered, recipientWitnesses, liveJob,
                  gitDependent, nativeHandoffPending, nativeHandoffEverQueued>>

NativeRelease(r) ==
    /\ phase = "open"
    /\ r \in RunIds
    /\ claim[r] = "active"
    /\ harness[r] = "finished"
    /\ r \in delivered
    /\ r \in RecipientAccepted
    \* An independent Domain ACK is not authority to abandon an unresolved
    \* native Manager handoff or active original physical Job.
    /\ ~nativeHandoffPending
    /\ ~liveJob
    /\ claim' = [claim EXCEPT ![r] = "released"]
    /\ UNCHANGED <<phase, harness, published, delivered, liveJob, gitDependent, originalWorkspace, claimWorkspace, censusComplete, recipientWitnesses, nativeHandoffPending, nativeHandoffEverQueued>>

AbortNeverIssuedReservation(r) ==
    /\ phase = "open"
    /\ r \in RunIds
    /\ claim[r] = "reserved"
    /\ r \notin published
    \* Real code MUST prove the grant was never activated or exposed.
    \* A TTL without such proof cannot safely release an active consumer.
    /\ claim' = [claim EXCEPT ![r] = "released"]
    /\ harness' = [harness EXCEPT ![r] = "finished"]
    /\ UNCHANGED <<phase, published, delivered, liveJob, gitDependent, originalWorkspace, claimWorkspace, censusComplete, recipientWitnesses, nativeHandoffPending, nativeHandoffEverQueued>>

BeginJob ==
    /\ phase = "open"
    /\ ~liveJob
    /\ liveJob' = TRUE
    /\ UNCHANGED <<phase, harness, claim, published, delivered, gitDependent, originalWorkspace, claimWorkspace, censusComplete, recipientWitnesses, nativeHandoffPending, nativeHandoffEverQueued>>

EndJob ==
    /\ phase = "open"
    /\ liveJob
    /\ liveJob' = FALSE
    /\ UNCHANGED <<phase, harness, claim, published, delivered, gitDependent, originalWorkspace, claimWorkspace, censusComplete, recipientWitnesses, nativeHandoffPending, nativeHandoffEverQueued>>

\* OS Manager queued work is not necessarily a running PID or visible Unit.
\* The true issuer/manager handoff identity and its terminal observation are
\* external implementation proof obligations, modeled here as one Boolean.
\* This deliberately composes the independent IssuerRevokeEpochR1 #2518
\* negative with the original Workspace Claim/Recipient ACK model #2511.
QueueNativeManagerHandoff ==
    /\ phase = "open"
    /\ ~nativeHandoffPending
    /\ ~liveJob
    /\ \E r \in published: claim[r] = "active"
    /\ nativeHandoffPending' = TRUE
    /\ nativeHandoffEverQueued' = TRUE
    /\ UNCHANGED <<phase, harness, claim, originalWorkspace, claimWorkspace,
                  published, delivered, censusComplete, recipientWitnesses, liveJob, gitDependent>>

\* systemd may materialize the native attempt AFTER its submitter exited.
NativeManagerBirth ==
    /\ phase = "open"
    /\ nativeHandoffPending
    /\ ~liveJob
    /\ nativeHandoffPending' = FALSE
    /\ liveJob' = TRUE
    /\ UNCHANGED <<phase, harness, claim, originalWorkspace, claimWorkspace,
                  published, delivered, censusComplete, recipientWitnesses, gitDependent,
                  nativeHandoffEverQueued>>

AddGitDependent ==
    /\ phase = "open"
    /\ ~gitDependent
    /\ gitDependent' = TRUE
    /\ UNCHANGED <<phase, harness, claim, published, delivered, liveJob, originalWorkspace, claimWorkspace, censusComplete, recipientWitnesses, nativeHandoffPending, nativeHandoffEverQueued>>

RemoveGitDependent ==
    /\ phase = "open"
    /\ gitDependent
    /\ gitDependent' = FALSE
    /\ UNCHANGED <<phase, harness, claim, published, delivered, liveJob, originalWorkspace, claimWorkspace, censusComplete, recipientWitnesses, nativeHandoffPending, nativeHandoffEverQueued>>

Eligible ==
    /\ phase = "open"
    /\ \A r \in RunIds: claim[r] \notin {"reserved", "active"}
    /\ published \subseteq delivered
    /\ published \subseteq RecipientAccepted
    /\ ~liveJob
    /\ ~nativeHandoffPending
    /\ ~gitDependent

NativeClose ==
    /\ Eligible
    \* Close, reserve and activate share the Runtime DB admission lock.
    /\ phase' = "closed"
    /\ UNCHANGED <<harness, claim, published, delivered, liveJob, gitDependent, originalWorkspace, claimWorkspace, censusComplete, recipientWitnesses, nativeHandoffPending, nativeHandoffEverQueued>>

Progress ==
    \/ \E r \in RunIds: \E w \in WorkspaceIds: HarnessPrepare(r,w)
    \/ \E r \in RunIds: LegacyPrepareWithoutOriginal(r)
    \/ \E r \in RunIds: \E w \in WorkspaceIds: NativeReserve(r,w)
    \/ \E r \in RunIds: HarnessReady(r)
    \/ \E r \in RunIds: NativeActivate(r)
    \/ \E r \in RunIds: PublishToolGrant(r)
    \/ \E r \in RunIds: HarnessFinish(r)
    \/ \E r \in RunIds: DeliverOutput(r)
    \/ \E r \in RunIds: QualifyCompleteOutputCensus(r)
    \/ \E r \in RunIds: \E output \in RequiredOutputs(r):
        \E subject \in SubjectClasses: IndependentRecipientObserve(r, output, subject)
    \/ \E r \in RunIds: NativeRelease(r)
    \/ \E r \in RunIds: AbortNeverIssuedReservation(r)
    \/ BeginJob
    \/ EndJob
    \/ QueueNativeManagerHandoff
    \/ NativeManagerBirth
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
    /\ censusComplete \subseteq {r \in published : harness[r] = "finished"}
    /\ recipientWitnesses \subseteq
         UNION { {r} \X RequiredOutputs(r) \X SubjectClasses : r \in delivered}
    /\ \A r \in RunIds: \A o \in RequiredOutputs(r):
         Cardinality({c \in SubjectClasses : <<r,o,c>> \in recipientWitnesses}) <= 1
    /\ liveJob \in BOOLEAN
    /\ gitDependent \in BOOLEAN
    /\ nativeHandoffPending \in BOOLEAN
    /\ nativeHandoffEverQueued \in BOOLEAN

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

\* A native close must not follow a prematurely released original Workspace.
ClosedHasNoPrematurelyReleasedConsumers ==
    phase = "closed" =>
        (\A r \in RunIds:
            (originalWorkspace[r] \in WorkspaceIds /\ claim[r] = "released") =>
                harness[r] = "finished")

\* Even a completed Harness Run plus an apparently successful delivery
\* callback cannot unpin or close until the independent Domain recipient
\* authenticated its own original bytes and accepted them.
ReleaseRequiresIndependentRecipientAck ==
    \A r \in published: claim[r] = "released" => r \in RecipientAccepted

ClosedHasIndependentRecipientAcceptance ==
    phase = "closed" => published \subseteq RecipientAccepted

ClosedHasDeliveredOutputs ==
    phase = "closed" => published \subseteq delivered

\* OS admission handoff is independently observable even before a PID.
\* With no pending OS Manager delivery, a normal source-owned Claim pin
\* can be released after the independently authenticated Domain recipient.
NativePendingHasOriginalPin ==
    nativeHandoffPending =>
        \E r \in published: claim[r] = "active"

ClosedHasNoManagerQueue ==
    phase = "closed" => ~nativeHandoffPending

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

\* Must be FALSE: a real original Run with independent recipient acceptance
\* can reach a released Claim without deadlocking the Workspace forever.
IndependentAcceptedReleaseUnreachable ==
    \A r \in RunIds: ~(claim[r] = "released" /\ r \in RecipientAccepted)

\* Must be FALSE: pending Manager work may actually finish, and a Run
\* with real recipient ACK and an original native handoff can be released
\* and physically closed after that effect has settled.
ManagerHandoffDrainedCloseUnreachable ==
    ~(phase = "closed" /\ nativeHandoffEverQueued /\
      ~nativeHandoffPending /\ ~liveJob)

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
    /\ UNCHANGED <<harness, claim, published, delivered, liveJob, gitDependent, originalWorkspace, claimWorkspace, censusComplete, recipientWitnesses, nativeHandoffPending, nativeHandoffEverQueued>>

UnsafeCrossDbSpec == Init /\ [][Progress \/ UnsafeCrossDatabaseClose]_vars

\* Second bad case: after native closed tombstone, another database
\* admits a claim using its own lock, never checking Runtime OPEN state.
UnsafeLateForeignClaim(r) ==
    /\ phase = "closed"
    /\ r \in RunIds
    /\ claim[r] = "none"
    /\ claim' = [claim EXCEPT ![r] = "reserved"]
    /\ UNCHANGED <<phase, harness, published, delivered, liveJob, gitDependent, originalWorkspace, claimWorkspace, censusComplete, recipientWitnesses, nativeHandoffPending, nativeHandoffEverQueued>>

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
    /\ UNCHANGED <<phase, harness, claim, delivered, liveJob, gitDependent, originalWorkspace, claimWorkspace, censusComplete, recipientWitnesses, nativeHandoffPending, nativeHandoffEverQueued>>

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
    /\ UNCHANGED <<phase, harness, originalWorkspace, published, delivered, liveJob, gitDependent, censusComplete, recipientWitnesses, nativeHandoffPending, nativeHandoffEverQueued>>

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
    /\ UNCHANGED <<phase, harness, originalWorkspace, published, delivered, liveJob, gitDependent, censusComplete, recipientWitnesses, nativeHandoffPending, nativeHandoffEverQueued>>

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
    /\ UNCHANGED <<phase, harness, published, delivered, liveJob, gitDependent, originalWorkspace, claimWorkspace, censusComplete, recipientWitnesses, nativeHandoffPending, nativeHandoffEverQueued>>

UnsafeDirectReleaseSpec ==
    Init /\ [][SafeNext \/ (\E r \in RunIds: UnsafeDirectCallerRelease(r))]_vars

\* Real Harness/R29 negative: Run is FINISHED and a caller records a
\* delivery/accepted=true result, but the independently authorized recipient
\* has not read or accepted its original output bytes. A finalizer that
\* trusts that caller JSON can prematurely release the Native pin.
UnsafeSelfCertifiedRelease(r) ==
    /\ phase = "open"
    /\ r \in published
    /\ harness[r] = "finished"
    /\ r \in delivered
    /\ r \notin RecipientAccepted
    /\ claim[r] = "active"
    /\ claim' = [claim EXCEPT ![r] = "released"]
    /\ UNCHANGED <<phase, harness, originalWorkspace, claimWorkspace, published, delivered, censusComplete, recipientWitnesses, liveJob, gitDependent, nativeHandoffPending, nativeHandoffEverQueued>>

\* If native close ALSO trusts the caller's delivery declaration (instead
\* of a trustworthy recipient), the original workspace can be deleted.
UnsafeCloseAfterFakeAck ==
    /\ phase = "open"
    /\ \E r \in RunIds:
        /\ r \in published
        /\ harness[r] = "finished"
        /\ claim[r] = "released"
        /\ r \in delivered
        /\ r \notin RecipientAccepted
    /\ ~liveJob
    /\ ~gitDependent
    /\ phase' = "closed"
    /\ UNCHANGED <<harness, claim, originalWorkspace, claimWorkspace, published, delivered, censusComplete, recipientWitnesses, liveJob, gitDependent, nativeHandoffPending, nativeHandoffEverQueued>>

UnsafeSelfCertSpec ==
    Init /\ [][SafeNext
        \/ (\E r \in RunIds: UnsafeSelfCertifiedRelease(r))
        \/ UnsafeCloseAfterFakeAck]_vars

\* Real native OS manager race even with a genuinely accepted Domain ACK:
\* a caller has stopped, activeJobIds may be empty, but systemd still owns
\* a queued StartTransientUnit. This original Run may NOT release its pin.
UnsafeReleaseWhileManagerQueued(r) ==
    /\ phase = "open"
    /\ nativeHandoffPending
    /\ ~liveJob
    /\ r \in published
    /\ claim[r] = "active"
    /\ harness[r] = "finished"
    /\ r \in delivered
    /\ r \in RecipientAccepted
    /\ claim' = [claim EXCEPT ![r] = "released"]
    /\ UNCHANGED <<phase, harness, originalWorkspace, claimWorkspace,
                  published, delivered, censusComplete, recipientWitnesses, liveJob,
                  gitDependent, nativeHandoffPending, nativeHandoffEverQueued>>

\* If a close checks only PID/Job inventory and Domain ACK, it may delete
\* the Workspace while OS Manager is still holding delayed work.
UnsafeCloseWithQueuedManager ==
    /\ phase = "open"
    /\ nativeHandoffPending
    /\ ~liveJob
    /\ ~gitDependent
    /\ \A r \in RunIds: claim[r] \notin {"reserved", "active"}
    /\ published \subseteq delivered
    /\ published \subseteq RecipientAccepted
    /\ phase' = "closed"
    /\ UNCHANGED <<harness, claim, originalWorkspace, claimWorkspace,
                  published, delivered, censusComplete, recipientWitnesses, liveJob,
                  gitDependent, nativeHandoffPending, nativeHandoffEverQueued>>

\* The native OS action can materialize after original workspace deletion.
UnsafeManagerBirthAfterClose ==
    /\ phase = "closed"
    /\ nativeHandoffPending
    /\ ~liveJob
    /\ nativeHandoffPending' = FALSE
    /\ liveJob' = TRUE
    /\ UNCHANGED <<phase, harness, claim, originalWorkspace, claimWorkspace,
                  published, delivered, censusComplete, recipientWitnesses, gitDependent,
                  nativeHandoffEverQueued>>

UnsafeManagerSpec ==
    Init /\ [][SafeNext
        \/ (\E r \in RunIds: UnsafeReleaseWhileManagerQueued(r))
        \/ UnsafeCloseWithQueuedManager
        \/ UnsafeManagerBirthAfterClose]_vars
\* Independent safety oracle: do not rely on the acceptance projection.
\* Native validation of the subject tuple remains an implementation premise.
ReleaseRequiresExactRecipientSubject ==
    \A r \in published:
        claim[r] = "released" =>
            \A o \in RequiredOutputs(r): <<r,o,"exact">> \in recipientWitnesses

ReleaseRequiresCompleteOriginalCensus ==
    \A r \in published: claim[r] = "released" => r \in censusComplete

ClosedRequiresCompleteOriginalCensus ==
    phase = "closed" => published \subseteq censusComplete

AcceptanceRequiresDelivery == RecipientAccepted \subseteq delivered

\* Intentionally false reachability predicate. A wrong-subject observation
\* is possible; a correct gate may never promote it to acceptance.
ForeignRecipientObservationUnreachable ==
    \A r \in RunIds: \A o \in RequiredOutputs(r):
        \A c \in SubjectClasses \ {"exact"}: <<r,o,c>> \notin recipientWitnesses

\* Positive reachability controls (intentionally false).
CompleteEmptyReleaseUnreachable ==
    ~(claim["runB"] = "released" /\ "runB" \in published /\
      "runB" \in censusComplete /\ RequiredOutputs("runB") = {})

CompleteTwoOutputReleaseUnreachable ==
    ~(claim["runA"] = "released" /\ "runA" \in censusComplete /\
      \A o \in RequiredOutputs("runA"): <<"runA",o,"exact">> \in recipientWitnesses)

PartialReceiptUnreachable ==
    ~("runA" \in censusComplete /\ claim["runA"] = "active" /\
      Cardinality(AcceptedOutputs("runA")) = 1)

UnknownEmptyCensusUnreachable ==
    ~("runB" \in delivered /\ "runB" \notin censusComplete /\
      claim["runB"] = "active")

=============================================================================
