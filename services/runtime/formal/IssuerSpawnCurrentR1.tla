-------------------------- MODULE IssuerSpawnCurrentR1 --------------------------
EXTENDS Naturals, TLC

\* Formal-only R24/R26 consumer model: NO production authorization.
\* Issuer-current at PostgreSQL Job admission is weaker than issuer-current
\* at a later systemd process spawn. This model does NOT prove that a late
\* SQL SELECT is atomic with OS exec. StrictLaunch=TRUE is the obligation
\* of a future qualified native launch receiver, not today's installed code.

CONSTANT StrictLaunch
VARIABLES issuer, job, osProcess, dispatchCount, spawnedAfterRevocation

vars == <<issuer, job, osProcess, dispatchCount, spawnedAfterRevocation>>

Init ==
    /\ issuer = "current"
    /\ job = "none"
    /\ osProcess = "not-started"
    /\ dispatchCount = 0
    /\ spawnedAfterRevocation = FALSE

\* R26 already has a same-PG original issuer/current Fence admission guard.
AdmitJob ==
    /\ job = "none"
    /\ issuer = "current"
    /\ job' = "admitted"
    /\ UNCHANGED <<issuer, osProcess, dispatchCount, spawnedAfterRevocation>>

\* Commit is durable dispatch INTENT, not a physical OS execution witness.
CommitDispatch ==
    /\ job = "admitted"
    /\ dispatchCount = 0
    /\ job' = "issued"
    /\ dispatchCount' = 1
    /\ UNCHANGED <<issuer, osProcess, spawnedAfterRevocation>>

\* Source Run Writer revokes or changes the original live Run revision.
RevokeIssuer ==
    /\ issuer = "current"
    /\ issuer' = "revoked"
    /\ UNCHANGED <<job, osProcess, dispatchCount, spawnedAfterRevocation>>

\* R24 real systemd gate: under Admission-only, this transition remains
\* enabled after revocation. The proposed strict receiver must block it.
\* Its atomicity with OS launch is an IMPLEMENTATION PROOF OBLIGATION.
PhysicalSpawn ==
    /\ job = "issued"
    /\ osProcess = "not-started"
    /\ (StrictLaunch = FALSE \/ issuer = "current")
    /\ osProcess' = "running"
    /\ spawnedAfterRevocation' = (issuer = "revoked")
    /\ UNCHANGED <<issuer, job, dispatchCount>>

ObservePhysicalExit ==
    /\ osProcess = "running"
    /\ osProcess' = "quiescent"
    /\ UNCHANGED <<issuer, job, dispatchCount, spawnedAfterRevocation>>

Next ==
    \/ AdmitJob
    \/ CommitDispatch
    \/ RevokeIssuer
    \/ PhysicalSpawn
    \/ ObservePhysicalExit

Spec == Init /\ [][Next]_vars

TypeOK ==
    /\ StrictLaunch \in BOOLEAN
    /\ issuer \in {"current", "revoked"}
    /\ job \in {"none", "admitted", "issued"}
    /\ osProcess \in {"not-started", "running", "quiescent"}
    /\ dispatchCount \in 0..1
    /\ spawnedAfterRevocation \in BOOLEAN

AtMostOnceDispatch ==
    dispatchCount <= 1

NoSpawnAfterIssuerRevocation ==
    ~spawnedAfterRevocation

\* Intentionally FALSE reachability probes in dedicated configs:
\* physical effects are possible while issuer is current; a committed
\* but still unlaunched Job can exist after issuer revocation.
PhysicalSpawnUnreachable == osProcess = "not-started"
RevokedIssuedUnreachable ==
    ~(job = "issued" /\ issuer = "revoked" /\ osProcess = "not-started")

=============================================================================
