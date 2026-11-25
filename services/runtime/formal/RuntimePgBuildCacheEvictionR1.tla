-------------------- MODULE RuntimePgBuildCacheEvictionR1 --------------------
EXTENDS Naturals
\* Bounded abstract MODEL of one PG-fenced Workspace build-cache eviction.
\* The PG advisory admission lock, source qualification and native OS process
\* ownership remain real implementation/installed obligations, not model proofs.
\* Detached bytes are rebuildable compiler outputs, NOT Git source or Artifact.
\* Hidden durable roots model earlier Attempts or independent allocations.
\* Their absence must be qualified before detach, not inferred from latest Job.
VARIABLES gate, job, cache, detached, qualified, source, phase, hiddenRoot
Vars == <<gate, job, cache, detached, qualified, source, phase, hiddenRoot>>

Init ==
    /\ gate = "free"
    /\ job = "idle"
    /\ cache = "present"
    /\ detached = FALSE
    /\ qualified = FALSE
    /\ source = "preserved"
    /\ phase = "ready"
    /\ hiddenRoot \in {"none", "unsettledAttempt", "unreleasedAllocation"}

AcquirePruneFence ==
    /\ gate = "free"
    /\ job = "idle"
    /\ phase = "ready"
    /\ gate' = "pruner"
    /\ phase' = "planning"
    /\ UNCHANGED <<job, cache, detached, qualified, source, hiddenRoot>>

RecheckUnderFence ==
    /\ gate = "pruner"
    /\ phase = "planning"
    /\ job = "idle"
    /\ hiddenRoot = "none"
    /\ qualified' = TRUE
    /\ phase' = "qualified"
    /\ UNCHANGED <<gate, job, cache, detached, source, hiddenRoot>>

DetachRebuildableCache ==
    /\ gate = "pruner"
    /\ phase \in {"planning", "qualified"}
    /\ qualified
    /\ job = "idle"
    /\ cache = "present"
    /\ cache' = "absent"
    /\ detached' = TRUE
    /\ phase' = "detached"
    /\ UNCHANGED <<gate, job, qualified, source, hiddenRoot>>

ReleaseAdmissionFence ==
    /\ gate = "pruner"
    /\ phase = "detached"
    /\ gate' = "free"
    /\ phase' = "outside_fence"
    /\ UNCHANGED <<job, cache, detached, qualified, source, hiddenRoot>>

DeleteAlreadyDetachedBytes ==
    /\ phase = "outside_fence"
    /\ detached
    /\ detached' = FALSE
    /\ phase' = "disposed"
    /\ UNCHANGED <<gate, job, cache, qualified, source, hiddenRoot>>

AcquireJobFence ==
    /\ gate = "free"
    /\ job = "idle"
    /\ gate' = "admitter"
    /\ UNCHANGED <<job, cache, detached, qualified, source, phase, hiddenRoot>>

AdmitJobAndRebuildIfNeeded ==
    /\ gate = "admitter"
    /\ job = "idle"
    /\ gate' = "free"
    /\ job' = "active"
    /\ cache' = "present"
    /\ UNCHANGED <<detached, qualified, source, phase, hiddenRoot>>

FinishJob ==
    /\ job = "active"
    /\ job' = "idle"
    /\ UNCHANGED <<gate, cache, detached, qualified, source, phase, hiddenRoot>>

Next ==
    \/ AcquirePruneFence
    \/ RecheckUnderFence
    \/ DetachRebuildableCache
    \/ ReleaseAdmissionFence
    \/ DeleteAlreadyDetachedBytes
    \/ AcquireJobFence
    \/ AdmitJobAndRebuildIfNeeded
    \/ FinishJob

TypeOK ==
    /\ gate \in {"free", "pruner", "admitter"}
    /\ job \in {"idle", "active"}
    /\ cache \in {"present", "absent"}
    /\ detached \in BOOLEAN
    /\ qualified \in BOOLEAN
    /\ source = "preserved"
    /\ hiddenRoot \in {"none", "unsettledAttempt", "unreleasedAllocation"}
    /\ phase \in {"ready", "planning", "qualified", "detached", "outside_fence", "disposed"}

NoActiveJobWithoutBuild == job = "active" => cache = "present"
DetachedRequiresQualified == detached => qualified
DetachedHasNoHiddenRoot == detached => hiddenRoot = "none"
SourceIsNeverEvicted == source = "preserved"
\* Anti-vacuity: MUST be violated in a reachable legitimate eviction.
NeverDetached == ~detached
Spec == Init /\ [][Next]_Vars
=============================================================================
