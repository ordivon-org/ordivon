-------------------------- MODULE IssuerSpawnCurrentR1 --------------------------
EXTENDS Naturals, TLC

\* Formal-only R24/R26 consumer model: NO production authorization.
\* Issuer-current at PostgreSQL Job admission is weaker than issuer-current
\* at a later systemd process spawn. This model does NOT prove that a late
\* SQL SELECT is atomic with OS exec. Even a late unlocked pre-spawn check
\* leaves a revocation window. atomicReceiver is an implementation proof
\* obligation of a future qualified native launch receiver, not deployed code.

CONSTANT LaunchPolicy
VARIABLES issuer, job, osProcess, dispatchCount, spawnedAfterRevocation, prechecked

vars == <<issuer, job, osProcess, dispatchCount, spawnedAfterRevocation, prechecked>>

Init ==
    /\ issuer = "current"
    /\ job = "none"
    /\ osProcess = "not-started"
    /\ dispatchCount = 0
    /\ spawnedAfterRevocation = FALSE
    /\ prechecked = FALSE

\* R26 already has a same-PG original issuer/current Fence admission guard.
AdmitJob ==
    /\ job = "none"
    /\ issuer = "current"
    /\ job' = "admitted"
    /\ UNCHANGED <<issuer, osProcess, dispatchCount, spawnedAfterRevocation, prechecked>>

\* Commit is durable dispatch INTENT, not a physical OS execution witness.
CommitDispatch ==
    /\ job = "admitted"
    /\ dispatchCount = 0
    /\ job' = "issued"
    /\ dispatchCount' = 1
    /\ UNCHANGED <<issuer, osProcess, spawnedAfterRevocation, prechecked>>

\* Source Run Writer revokes or changes the original live Run revision.
RevokeIssuer ==
    /\ issuer = "current"
    /\ issuer' = "revoked"
    /\ UNCHANGED <<job, osProcess, dispatchCount, spawnedAfterRevocation, prechecked>>

\* An unlocked SQL issuer check BEFORE native systemd-run is not atomic
\* with the later physical spawn. Revocation may win between those actions.
PreSpawnCheck ==
    /\ LaunchPolicy = "precheckOnly"
    /\ job = "issued"
    /\ osProcess = "not-started"
    /\ ~prechecked
    /\ issuer = "current"
    /\ prechecked' = TRUE
    /\ UNCHANGED <<issuer, job, osProcess, dispatchCount, spawnedAfterRevocation>>

\* R24 real systemd gate: admissionOnly allows OS launch after revoke.
\* precheckOnly also permits it after a stale once-valid separate check.
\* atomicReceiver means issuer read and OS startup have ONE linearization point
\* in this ABSTRACT model; production atomicity is NOT demonstrated by TLC.
PhysicalSpawn ==
    /\ job = "issued"
    /\ osProcess = "not-started"
    /\ CASE LaunchPolicy = "admissionOnly" -> TRUE
         [] LaunchPolicy = "precheckOnly" -> prechecked
         [] LaunchPolicy = "atomicReceiver" -> issuer = "current"
    /\ osProcess' = "running"
    /\ spawnedAfterRevocation' = (issuer = "revoked")
    /\ UNCHANGED <<issuer, job, dispatchCount, prechecked>>

ObservePhysicalExit ==
    /\ osProcess = "running"
    /\ osProcess' = "quiescent"
    /\ UNCHANGED <<issuer, job, dispatchCount, spawnedAfterRevocation, prechecked>>

Next ==
    \/ AdmitJob
    \/ CommitDispatch
    \/ RevokeIssuer
    \/ PreSpawnCheck
    \/ PhysicalSpawn
    \/ ObservePhysicalExit

Spec == Init /\ [][Next]_vars

TypeOK ==
    /\ LaunchPolicy \in {"admissionOnly", "precheckOnly", "atomicReceiver"}
    /\ issuer \in {"current", "revoked"}
    /\ job \in {"none", "admitted", "issued"}
    /\ osProcess \in {"not-started", "running", "quiescent"}
    /\ dispatchCount \in 0..1
    /\ spawnedAfterRevocation \in BOOLEAN
    /\ prechecked \in BOOLEAN

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
