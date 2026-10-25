------------------------- MODULE RuntimePgCutoverR1 -------------------------
EXTENDS Naturals

\* Small finite abstraction of one Runtime registry migration. No file IO,
\* replication, network, PG pool or implementation refinement is asserted.
\* "owner" is the one durable writer authority, not two independent flags.
VARIABLES owner, sqliteRevision, pgRevision, copied, parityVerified,
          cutoverCertified, pgCommitted, rolledBack

Vars == <<owner, sqliteRevision, pgRevision, copied, parityVerified,
          cutoverCertified, pgCommitted, rolledBack>>

Init ==
    /\ owner = "sqlite"
    /\ sqliteRevision = 0
    /\ pgRevision = 0
    /\ copied = FALSE
    /\ parityVerified = FALSE
    /\ cutoverCertified = FALSE
    /\ pgCommitted = FALSE
    /\ rolledBack = FALSE

SqliteCommit ==
    /\ owner = "sqlite"
    /\ sqliteRevision < 2
    /\ sqliteRevision' = sqliteRevision + 1
    /\ copied' = FALSE
    /\ parityVerified' = FALSE
    /\ UNCHANGED <<owner, pgRevision, cutoverCertified, pgCommitted, rolledBack>>

Freeze ==
    /\ owner = "sqlite"
    /\ owner' = "paused"
    /\ parityVerified' = FALSE
    /\ UNCHANGED <<sqliteRevision, pgRevision, copied, cutoverCertified,
                   pgCommitted, rolledBack>>

CopySnapshot ==
    /\ owner = "paused"
    /\ pgRevision' = sqliteRevision
    /\ copied' = TRUE
    /\ parityVerified' = FALSE
    /\ UNCHANGED <<owner, sqliteRevision, cutoverCertified, pgCommitted, rolledBack>>

VerifyParity ==
    /\ owner = "paused"
    /\ copied
    /\ pgRevision = sqliteRevision
    /\ parityVerified' = TRUE
    /\ UNCHANGED <<owner, sqliteRevision, pgRevision, copied, cutoverCertified,
                   pgCommitted, rolledBack>>

Promote ==
    /\ owner = "paused"
    /\ parityVerified
    /\ pgRevision = sqliteRevision
    /\ owner' = "postgres"
    /\ cutoverCertified' = TRUE
    /\ rolledBack' = FALSE
    /\ UNCHANGED <<sqliteRevision, pgRevision, copied, parityVerified, pgCommitted>>

PostgresCommit ==
    /\ owner = "postgres"
    /\ pgRevision < 2
    /\ pgRevision' = pgRevision + 1
    /\ pgCommitted' = TRUE
    /\ UNCHANGED <<owner, sqliteRevision, copied, parityVerified,
                   cutoverCertified, rolledBack>>

\* Rollback is legal only before the first independent PostgreSQL commit.
\* Otherwise the former SQLite revision would lose a committed effect.
Rollback ==
    /\ owner = "postgres"
    /\ ~pgCommitted
    /\ owner' = "sqlite"
    /\ rolledBack' = TRUE
    /\ copied' = FALSE
    /\ parityVerified' = FALSE
    /\ UNCHANGED <<sqliteRevision, pgRevision, cutoverCertified, pgCommitted>>

Next ==
    \/ SqliteCommit
    \/ Freeze
    \/ CopySnapshot
    \/ VerifyParity
    \/ Promote
    \/ PostgresCommit
    \/ Rollback

TypeOK ==
    /\ owner \in {"sqlite", "paused", "postgres"}
    /\ sqliteRevision \in 0..2
    /\ pgRevision \in 0..2
    /\ copied \in BOOLEAN
    /\ parityVerified \in BOOLEAN
    /\ cutoverCertified \in BOOLEAN
    /\ pgCommitted \in BOOLEAN
    /\ rolledBack \in BOOLEAN

PostgresRequiresCertifiedCutover ==
    owner = "postgres" => cutoverCertified

NoLostPostgresCommit ==
    pgCommitted => owner = "postgres"

VerifiedParityWasFrozen ==
    (owner = "paused" /\ parityVerified) => pgRevision = sqliteRevision

Spec == Init /\ [][Next]_Vars

=============================================================================
