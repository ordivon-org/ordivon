------------------------- MODULE RuntimePgCutoverR1 -------------------------
EXTENDS Naturals

\* Small finite abstraction of one Runtime registry migration. No file IO,
\* replication, network, PG pool or implementation refinement is asserted.
\* "owner" is the one durable writer authority, not two independent flags.
VARIABLES owner, sqliteRevision, pgRevision, copied, parityVerified,
          cutoverCertified, pgCommitted, rolledBack,
          sqliteWriterActive, pgWriterActive

Vars == <<owner, sqliteRevision, pgRevision, copied, parityVerified,
          cutoverCertified, pgCommitted, rolledBack,
          sqliteWriterActive, pgWriterActive>>

Init ==
    /\ owner = "sqlite"
    /\ sqliteRevision = 0
    /\ pgRevision = 0
    /\ copied = FALSE
    /\ parityVerified = FALSE
    /\ cutoverCertified = FALSE
    /\ pgCommitted = FALSE
    /\ rolledBack = FALSE
    /\ sqliteWriterActive = TRUE
    /\ pgWriterActive = FALSE

SqliteCommit ==
    /\ owner = "sqlite"
    /\ sqliteWriterActive
    /\ sqliteRevision < 2
    /\ sqliteRevision' = sqliteRevision + 1
    /\ copied' = FALSE
    /\ parityVerified' = FALSE
    /\ UNCHANGED <<owner, pgRevision, cutoverCertified, pgCommitted, rolledBack,
                   sqliteWriterActive, pgWriterActive>>

Freeze ==
    /\ owner = "sqlite"
    /\ sqliteWriterActive
    /\ owner' = "paused"
    /\ sqliteWriterActive' = FALSE
    /\ parityVerified' = FALSE
    /\ UNCHANGED <<sqliteRevision, pgRevision, copied, cutoverCertified,
                   pgCommitted, rolledBack, pgWriterActive>>

CopySnapshot ==
    /\ owner = "paused"
    /\ pgRevision' = sqliteRevision
    /\ copied' = TRUE
    /\ parityVerified' = FALSE
    /\ UNCHANGED <<owner, sqliteRevision, cutoverCertified, pgCommitted, rolledBack,
                   sqliteWriterActive, pgWriterActive>>

VerifyParity ==
    /\ owner = "paused"
    /\ copied
    /\ pgRevision = sqliteRevision
    /\ parityVerified' = TRUE
    /\ UNCHANGED <<owner, sqliteRevision, pgRevision, copied, cutoverCertified,
                   pgCommitted, rolledBack, sqliteWriterActive, pgWriterActive>>

Promote ==
    /\ owner = "paused"
    /\ parityVerified
    /\ pgRevision = sqliteRevision
    /\ ~sqliteWriterActive
    /\ ~pgWriterActive
    /\ owner' = "postgres"
    /\ pgWriterActive' = TRUE
    /\ cutoverCertified' = TRUE
    /\ rolledBack' = FALSE
    /\ UNCHANGED <<sqliteRevision, pgRevision, copied, parityVerified, pgCommitted,
                   sqliteWriterActive>>

PostgresCommit ==
    /\ owner = "postgres"
    /\ pgWriterActive
    /\ pgRevision < 2
    /\ pgRevision' = pgRevision + 1
    /\ pgCommitted' = TRUE
    /\ UNCHANGED <<owner, sqliteRevision, copied, parityVerified,
                   cutoverCertified, rolledBack, sqliteWriterActive, pgWriterActive>>

\* Rollback is legal only before the first independent PostgreSQL commit.
\* Otherwise the former SQLite revision would lose a committed effect.
Rollback ==
    /\ owner = "postgres"
    /\ pgWriterActive
    /\ ~pgCommitted
    /\ owner' = "sqlite"
    /\ pgWriterActive' = FALSE
    /\ sqliteWriterActive' = TRUE
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
    /\ sqliteWriterActive \in BOOLEAN
    /\ pgWriterActive \in BOOLEAN

PostgresRequiresCertifiedCutover ==
    owner = "postgres" => cutoverCertified

NoLostPostgresCommit ==
    pgCommitted => owner = "postgres"

VerifiedParityWasFrozen ==
    (owner = "paused" /\ parityVerified) => pgRevision = sqliteRevision

\* Independent installed-writer flags expose overlap hidden by the single owner enum.
\* Concrete Runtime must still prove that these flags reflect real processes.
NoConcurrentInstalledWriters == ~(sqliteWriterActive /\ pgWriterActive)

Spec == Init /\ [][Next]_Vars

=============================================================================
