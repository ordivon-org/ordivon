------------------------- MODULE RuntimePgCutoverR1 -------------------------
EXTENDS Naturals

\* A finite abstraction, NOT the physical SQLite/PG migration or cryptographic
\* verification. Content identities are two opaque distinct values; a copied
\* source revision need not imply a matching source payload. The importer may
\* copy corrupt content; only explicit readback parity certifies promotion.
\* "owner" is one durable writer authority, not two independent booleans.
VARIABLES owner, sqliteRevision, pgRevision, sqliteContent, pgContent,
          copied, parityVerified, cutoverCertified, pgCommitted, rolledBack,
          sqliteWriterActive, pgWriterActive

Vars == <<owner, sqliteRevision, pgRevision, sqliteContent, pgContent,
          copied, parityVerified, cutoverCertified, pgCommitted, rolledBack,
          sqliteWriterActive, pgWriterActive>>

Init ==
    /\ owner = "sqlite"
    /\ sqliteRevision = 0
    /\ pgRevision = 0
    /\ sqliteContent = 0
    /\ pgContent = 0
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
    /\ sqliteContent' = IF sqliteContent = 0 THEN 1 ELSE 0
    /\ copied' = FALSE
    /\ parityVerified' = FALSE
    /\ UNCHANGED <<owner, pgRevision, pgContent, cutoverCertified,
                   pgCommitted, rolledBack, sqliteWriterActive, pgWriterActive>>

Freeze ==
    /\ owner = "sqlite"
    /\ sqliteWriterActive
    /\ owner' = "paused"
    /\ sqliteWriterActive' = FALSE
    /\ parityVerified' = FALSE
    /\ UNCHANGED <<sqliteRevision, pgRevision, sqliteContent, pgContent,
                   copied, cutoverCertified, pgCommitted, rolledBack, pgWriterActive>>

CopySnapshot ==
    /\ owner = "paused"
    /\ pgRevision' = sqliteRevision
    \* Model a fallible import independently of the source's revision count.
    \* Equal revision with different symbolic content MUST NOT certify.
    /\ pgContent' \in 0..1
    /\ copied' = TRUE
    /\ parityVerified' = FALSE
    /\ UNCHANGED <<owner, sqliteRevision, sqliteContent, cutoverCertified,
                   pgCommitted, rolledBack, sqliteWriterActive, pgWriterActive>>

VerifyParity ==
    /\ owner = "paused"
    /\ copied
    /\ pgRevision = sqliteRevision
    /\ pgContent = sqliteContent
    /\ parityVerified' = TRUE
    /\ UNCHANGED <<owner, sqliteRevision, pgRevision, sqliteContent,
                   pgContent, copied, cutoverCertified, pgCommitted, rolledBack,
                   sqliteWriterActive, pgWriterActive>>

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
    /\ UNCHANGED <<sqliteRevision, pgRevision, sqliteContent, pgContent,
                   copied, parityVerified, pgCommitted, sqliteWriterActive>>

PostgresCommit ==
    /\ owner = "postgres"
    /\ pgWriterActive
    /\ pgRevision < 2
    /\ pgRevision' = pgRevision + 1
    /\ pgContent' = IF pgContent = 0 THEN 1 ELSE 0
    /\ pgCommitted' = TRUE
    /\ UNCHANGED <<owner, sqliteRevision, sqliteContent, copied,
                   parityVerified, cutoverCertified, rolledBack,
                   sqliteWriterActive, pgWriterActive>>

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
    /\ UNCHANGED <<sqliteRevision, pgRevision, sqliteContent, pgContent,
                   cutoverCertified, pgCommitted>>

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
    /\ sqliteContent \in 0..1
    /\ pgContent \in 0..1
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

VerifiedContentWasFrozen ==
    (owner = "paused" /\ parityVerified) => pgContent = sqliteContent

PromotedContentWasVerified ==
    (owner = "postgres" /\ ~pgCommitted) => pgContent = sqliteContent

\* Distinct installed writers expose real overlap hidden by the authority enum.
NoConcurrentInstalledWriters == ~(sqliteWriterActive /\ pgWriterActive)

Spec == Init /\ [][Next]_Vars

=============================================================================
