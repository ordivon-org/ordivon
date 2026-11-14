---------------- MODULE GatewayHostCutoverR1 ----------------
EXTENDS TLC

\* This is a BOUNDED cross-service RELEASE ORDER model, not an identity
\* authority or a physical/network availability proof. A true Boolean means
\* an already-qualified, independently observed condition, not a tool claim.
\* Gateway promotion requires Host anonymous reads DENIED before promotion.
\* Protecting Host first can strand direct clients and expose an old Gateway
\* without its object-level read PEP. A quiescence path is modeled, not a
\* guarantee that there is no downtime.

VARIABLES securityReady, mainBearer, peerMigrated, cloudMigrated,
          candidateStaged, hostProtected, gatewayPep, ingressOpen

vars == <<securityReady, mainBearer, peerMigrated, cloudMigrated,
          candidateStaged, hostProtected, gatewayPep, ingressOpen>>

Init ==
  /\ securityReady = FALSE
  /\ mainBearer = FALSE
  /\ peerMigrated = FALSE
  /\ cloudMigrated = FALSE
  /\ candidateStaged = FALSE
  /\ hostProtected = FALSE
  /\ gatewayPep = FALSE
  /\ ingressOpen = TRUE

QualifySecurity ==
  /\ ~securityReady
  /\ securityReady' = TRUE
  /\ UNCHANGED <<mainBearer, peerMigrated, cloudMigrated, candidateStaged,
                 hostProtected, gatewayPep, ingressOpen>>

ConfigureGatewayBearer ==
  /\ securityReady /\ ~mainBearer
  /\ mainBearer' = TRUE
  /\ UNCHANGED <<securityReady, peerMigrated, cloudMigrated, candidateStaged,
                 hostProtected, gatewayPep, ingressOpen>>

MigratePeerGateway ==
  /\ mainBearer /\ ~peerMigrated
  /\ peerMigrated' = TRUE
  /\ UNCHANGED <<securityReady, mainBearer, cloudMigrated, candidateStaged,
                 hostProtected, gatewayPep, ingressOpen>>

MigrateDirectCloudflare ==
  /\ securityReady /\ ~cloudMigrated
  /\ cloudMigrated' = TRUE
  /\ UNCHANGED <<securityReady, mainBearer, peerMigrated, candidateStaged,
                 hostProtected, gatewayPep, ingressOpen>>

PrepareCandidate ==
  /\ ~candidateStaged
  /\ candidateStaged' = TRUE
  /\ UNCHANGED <<securityReady, mainBearer, peerMigrated, cloudMigrated,
                 hostProtected, gatewayPep, ingressOpen>>

QuiescePublicIngress ==
  /\ ingressOpen /\ ~hostProtected
  /\ ingressOpen' = FALSE
  /\ UNCHANGED <<securityReady, mainBearer, peerMigrated, cloudMigrated,
                 candidateStaged, hostProtected, gatewayPep>>

ProtectHost ==
  /\ securityReady /\ mainBearer /\ peerMigrated /\ cloudMigrated
  /\ candidateStaged /\ ~hostProtected /\ ~ingressOpen
  /\ hostProtected' = TRUE
  /\ UNCHANGED <<securityReady, mainBearer, peerMigrated, cloudMigrated,
                 candidateStaged, gatewayPep, ingressOpen>>

PromoteGateway ==
  /\ hostProtected /\ securityReady /\ mainBearer
  /\ peerMigrated /\ cloudMigrated /\ candidateStaged
  /\ ~gatewayPep
  /\ gatewayPep' = TRUE
  /\ UNCHANGED <<securityReady, mainBearer, peerMigrated, cloudMigrated,
                 candidateStaged, hostProtected, ingressOpen>>

RestorePublicIngress ==
  /\ hostProtected /\ gatewayPep /\ ~ingressOpen
  /\ ingressOpen' = TRUE
  /\ UNCHANGED <<securityReady, mainBearer, peerMigrated, cloudMigrated,
                 candidateStaged, hostProtected, gatewayPep>>

Next ==
  \/ QualifySecurity
  \/ ConfigureGatewayBearer
  \/ MigratePeerGateway
  \/ MigrateDirectCloudflare
  \/ PrepareCandidate
  \/ QuiescePublicIngress
  \/ ProtectHost
  \/ PromoteGateway
  \/ RestorePublicIngress

Spec == Init /\ [][Next]_vars

TypeOK ==
  /\ securityReady \in BOOLEAN
  /\ mainBearer \in BOOLEAN
  /\ peerMigrated \in BOOLEAN
  /\ cloudMigrated \in BOOLEAN
  /\ candidateStaged \in BOOLEAN
  /\ hostProtected \in BOOLEAN
  /\ gatewayPep \in BOOLEAN
  /\ ingressOpen \in BOOLEAN

HostProtectedNeedsQualifiedConsumers ==
  hostProtected =>
    (securityReady /\ mainBearer /\ peerMigrated /\ cloudMigrated /\ candidateStaged)

GatewayPepNeedsProtectedHost ==
  gatewayPep => (hostProtected /\ securityReady /\ candidateStaged)

NoExposedOldReadPepAfterHostCutover ==
  (hostProtected /\ ingressOpen) => gatewayPep

\* Intentional false invariant: the safe path reaches the fully restored state.
NeverFinished ==
  ~(hostProtected /\ gatewayPep /\ ingressOpen)

\* Falsification-only mutation: premature Host switch, no peer qualification.
UnsafeProtectHost ==
  /\ ~hostProtected
  /\ hostProtected' = TRUE
  /\ UNCHANGED <<securityReady, mainBearer, peerMigrated, cloudMigrated,
                 candidateStaged, gatewayPep, ingressOpen>>

UnsafeNext == Next \/ UnsafeProtectHost
UnsafeSpec == Init /\ [][UnsafeNext]_vars

===============================================================
