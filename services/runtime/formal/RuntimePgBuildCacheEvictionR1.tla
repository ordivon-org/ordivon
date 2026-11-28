-------------------- MODULE RuntimePgBuildCacheEvictionR1 --------------------
EXTENDS Naturals
\* Bounded abstract MODEL of one PG-fenced Workspace build-cache eviction.
\* The PG advisory admission lock, source qualification and native OS process
\* ownership remain real implementation/installed obligations, not model proofs.
\* Detached bytes are rebuildable compiler outputs, NOT Git source or Artifact.
VARIABLES gate, job, cache, detached, qualified, source, phase
Vars == <<gate, job, cache, detached, qualified, source, phase>>

Init ==
    /\ gate = "free"
    /\ job = "idle"
    /\ cache = "present"
    /\ detached = FALSE
    /\ qualified = FALSE
    /\ source = "preserved"
    /\ phase = "ready"

AcquirePruneFence ==
    /\ gate = "free"
    /\ job = "idle"
    /\ phase = "ready"
    /\ gate' = "pruner"
    /\ phase' = "planning"
    /\ UNCHANGED <<job, cache, detached, qualified, source>>

RecheckUnderFence ==
    /\ gate = "pruner"
    /\ phase = "planning"
    /\ job = "idle"
    /\ qualified' = TRUE
    /\ phase' = "qualified"
    /\ UNCHANGED <<gate, job, cache, detached, source>>

DetachRebuildableCache ==
    /\ gate = "pruner"
    /\ phase \in {"planning", "qualified"}
    /\ qualified
    /\ job = "idle"
    /\ cache = "present"
    /\ cache' = "absent"
    /\ detached' = TRUE
    /\ phase' = "detached"
    /\ UNCHANGED <<gate, job, qualified, source>>

ReleaseAdmissionFence ==
    /\ gate = "pruner"
    /\ phase = "detached"
    /\ gate' = "free"
    /\ phase' = "outside_fence"
    /\ UNCHANGED <<job, cache, detached, qualified, source>>

DeleteAlreadyDetachedBytes ==
    /\ phase = "outside_fence"
    /\ detached
    /\ detached' = FALSE
    /\ phase' = "disposed"
    /\ UNCHANGED <<gate, job, cache, qualified, source>>

AcquireJobFence ==
    /\ gate = "free"
    /\ job = "idle"
    /\ gate' = "admitter"
    /\ UNCHANGED <<job, cache, detached, qualified, source, phase>>

AdmitJobAndRebuildIfNeeded ==
    /\ gate = "admitter"
    /\ job = "idle"
    /\ gate' = "free"
    /\ job' = "active"
    /\ cache' = "present"
    /\ UNCHANGED <<detached, qualified, source, phase>>

FinishJob ==
    /\ job = "active"
    /\ job' = "idle"
    /\ UNCHANGED <<gate, cache, detached, qualified, source, phase>>

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
    /\ phase \in {"ready", "planning", "qualified", "detached", "outside_fence", "disposed"}

NoActiveJobWithoutBuild == job = "active" => cache = "present"
DetachedRequiresQualified == detached => qualified
SourceIsNeverEvicted == source = "preserved"
\* Anti-vacuity: MUST be violated in a reachable legitimate eviction.
NeverDetached == ~detached
Spec == Init /\ [][Next]_Vars
=============================================================================
