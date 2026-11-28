---------------- MODULE GatewayHostCutoverR1 ----------------
EXTENDS TLC

\* This is a BOUNDED cross-service RELEASE ORDER model, not an identity
\* authority or a physical/network availability proof. A true Boolean means
\* an already-qualified, independently observed condition, not a tool claim.
\* Gateway promotion requires Host anonymous reads DENIED before promotion.
\* Protecting Host first can strand direct clients and expose an old Gateway
\* without its object-level read PEP. A quiescence path is modeled, not a
\* guarantee that there is no downtime.
\* mainBearer only means a declared service credential. hostBearerVerified
\* additionally means a successful MCP initialize to the authenticated Host,
\* using that actual workload secret after an independent anonymous denial.

VARIABLES securityReady, mainBearer, peerMigrated, cloudMigrated,
          candidateStaged, hostProtected, hostBearerVerified,
          gatewayPep, ingressOpen

vars == <<securityReady, mainBearer, peerMigrated, cloudMigrated,
          candidateStaged, hostProtected, hostBearerVerified,
          gatewayPep, ingressOpen>>

Init ==
  /\ securityReady = FALSE
  /\ mainBearer = FALSE
  /\ peerMigrated = FALSE
  /\ cloudMigrated = FALSE
  /\ candidateStaged = FALSE
  /\ hostProtected = FALSE
  /\ hostBearerVerified = FALSE
  /\ gatewayPep = FALSE
  /\ ingressOpen = TRUE

QualifySecurity ==
  /\ ~securityReady
  /\ securityReady' = TRUE
  /\ UNCHANGED <<mainBearer, peerMigrated, cloudMigrated, candidateStaged,
                 hostProtected, hostBearerVerified, gatewayPep, ingressOpen>>

ConfigureGatewayBearer ==
  /\ securityReady /\ ~mainBearer
  /\ mainBearer' = TRUE
  /\ UNCHANGED <<securityReady, peerMigrated, cloudMigrated, candidateStaged,
                 hostProtected, hostBearerVerified, gatewayPep, ingressOpen>>

MigratePeerGateway ==
  /\ mainBearer /\ ~peerMigrated
  /\ peerMigrated' = TRUE
  /\ UNCHANGED <<securityReady, mainBearer, cloudMigrated, candidateStaged,
                 hostProtected, hostBearerVerified, gatewayPep, ingressOpen>>

MigrateDirectCloudflare ==
  /\ securityReady /\ ~cloudMigrated
  /\ cloudMigrated' = TRUE
  /\ UNCHANGED <<securityReady, mainBearer, peerMigrated, candidateStaged,
                 hostProtected, hostBearerVerified, gatewayPep, ingressOpen>>

PrepareCandidate ==
  /\ ~candidateStaged
  /\ candidateStaged' = TRUE
  /\ UNCHANGED <<securityReady, mainBearer, peerMigrated, cloudMigrated,
                 hostProtected, hostBearerVerified, gatewayPep, ingressOpen>>

QuiescePublicIngress ==
  /\ ingressOpen /\ ~hostProtected
  /\ ingressOpen' = FALSE
  /\ UNCHANGED <<securityReady, mainBearer, peerMigrated, cloudMigrated,
                 candidateStaged, hostProtected, hostBearerVerified, gatewayPep>>

ProtectHost ==
  /\ securityReady /\ mainBearer /\ peerMigrated /\ cloudMigrated
  /\ candidateStaged /\ ~hostProtected /\ ~ingressOpen
  /\ hostProtected' = TRUE
  /\ UNCHANGED <<securityReady, mainBearer, peerMigrated, cloudMigrated,
                 candidateStaged, hostBearerVerified, gatewayPep, ingressOpen>>

VerifyHostBearer ==
  /\ hostProtected /\ mainBearer /\ ~hostBearerVerified /\ ~ingressOpen
  /\ hostBearerVerified' = TRUE
  /\ UNCHANGED <<securityReady, mainBearer, peerMigrated, cloudMigrated,
                 candidateStaged, hostProtected, gatewayPep, ingressOpen>>

PromoteGateway ==
  /\ hostProtected /\ securityReady /\ mainBearer /\ hostBearerVerified
  /\ peerMigrated /\ cloudMigrated /\ candidateStaged
  /\ ~gatewayPep
  /\ gatewayPep' = TRUE
  /\ UNCHANGED <<securityReady, mainBearer, peerMigrated, cloudMigrated,
                 candidateStaged, hostProtected, hostBearerVerified, ingressOpen>>

RestorePublicIngress ==
  /\ hostProtected /\ hostBearerVerified /\ gatewayPep /\ ~ingressOpen
  /\ ingressOpen' = TRUE
  /\ UNCHANGED <<securityReady, mainBearer, peerMigrated, cloudMigrated,
                 candidateStaged, hostProtected, hostBearerVerified, gatewayPep>>

Next ==
  \/ QualifySecurity
  \/ ConfigureGatewayBearer
  \/ MigratePeerGateway
  \/ MigrateDirectCloudflare
  \/ PrepareCandidate
  \/ QuiescePublicIngress
  \/ ProtectHost
  \/ VerifyHostBearer
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
  /\ hostBearerVerified \in BOOLEAN
  /\ gatewayPep \in BOOLEAN
  /\ ingressOpen \in BOOLEAN

HostProtectedNeedsQualifiedConsumers ==
  hostProtected =>
    (securityReady /\ mainBearer /\ peerMigrated /\ cloudMigrated /\ candidateStaged)

GatewayPepNeedsProtectedHost ==
  gatewayPep => (hostProtected /\ securityReady /\ candidateStaged)

GatewayPepNeedsVerifiedOwnerBearer ==
  gatewayPep => (hostProtected /\ hostBearerVerified /\ mainBearer)

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
                 candidateStaged, hostBearerVerified, gatewayPep, ingressOpen>>

UnsafeNext == Next \/ UnsafeProtectHost
UnsafeSpec == Init /\ [][UnsafeNext]_vars

\* Separate falsification: promotion with a merely declared bearer and no
\* authenticated live Host MCP initialize violates the new dependency.
UnsafePromoteWithoutBearer ==
  /\ hostProtected /\ ~hostBearerVerified /\ ~gatewayPep
  /\ gatewayPep' = TRUE
  /\ UNCHANGED <<securityReady, mainBearer, peerMigrated, cloudMigrated,
                 candidateStaged, hostProtected, hostBearerVerified, ingressOpen>>

UnsafeBearerNext == Next \/ UnsafePromoteWithoutBearer
UnsafeBearerSpec == Init /\ [][UnsafeBearerNext]_vars

===============================================================
