------------------------- MODULE RuntimePgCutoverR1 -------------------------
EXTENDS Naturals

\* A finite abstraction, NOT the physical SQLite/PG migration or cryptographic
\* verification. Content identities are two opaque distinct values; a copied
\* source revision need not imply a matching source payload. The importer may
\* copy corrupt content; only explicit readback parity certifies promotion.
\* "owner" is one durable writer authority, not two independent booleans.
VARIABLES owner, sqliteRevision, pgRevision, sqliteContent, pgContent,
          copied, parityVerified, cutoverCertified, pgCommitted, rolledBack

Vars == <<owner, sqliteRevision, pgRevision, sqliteContent, pgContent,
          copied, parityVerified, cutoverCertified, pgCommitted, rolledBack>>

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

SqliteCommit ==
    /\ owner = "sqlite"
    /\ sqliteRevision < 2
    /\ sqliteRevision' = sqliteRevision + 1
    /\ sqliteContent' = IF sqliteContent = 0 THEN 1 ELSE 0
    /\ copied' = FALSE
    /\ parityVerified' = FALSE
    /\ UNCHANGED <<owner, pgRevision, pgContent, cutoverCertified,
                   pgCommitted, rolledBack>>

Freeze ==
    /\ owner = "sqlite"
    /\ owner' = "paused"
    /\ parityVerified' = FALSE
    /\ UNCHANGED <<sqliteRevision, pgRevision, sqliteContent, pgContent,
                   copied, cutoverCertified, pgCommitted, rolledBack>>

CopySnapshot ==
    /\ owner = "paused"
    /\ pgRevision' = sqliteRevision
    \* Model a fallible import independently of the source's revision count.
    \* Equal revision with different symbolic content MUST NOT certify.
    /\ pgContent' \in 0..1
    /\ copied' = TRUE
    /\ parityVerified' = FALSE
    /\ UNCHANGED <<owner, sqliteRevision, sqliteContent, cutoverCertified,
                   pgCommitted, rolledBack>>

VerifyParity ==
    /\ owner = "paused"
    /\ copied
    /\ pgRevision = sqliteRevision
    /\ pgContent = sqliteContent
    /\ parityVerified' = TRUE
    /\ UNCHANGED <<owner, sqliteRevision, pgRevision, sqliteContent,
                   pgContent, copied, cutoverCertified, pgCommitted, rolledBack>>

Promote ==
    /\ owner = "paused"
    /\ parityVerified
    /\ pgRevision = sqliteRevision
    /\ owner' = "postgres"
    /\ cutoverCertified' = TRUE
    /\ rolledBack' = FALSE
    /\ UNCHANGED <<sqliteRevision, pgRevision, sqliteContent, pgContent,
                   copied, parityVerified, pgCommitted>>

PostgresCommit ==
    /\ owner = "postgres"
    /\ pgRevision < 2
    /\ pgRevision' = pgRevision + 1
    /\ pgContent' = IF pgContent = 0 THEN 1 ELSE 0
    /\ pgCommitted' = TRUE
    /\ UNCHANGED <<owner, sqliteRevision, sqliteContent, copied,
                   parityVerified, cutoverCertified, rolledBack>>

\* Rollback is legal only before the first independent PostgreSQL commit.
\* Otherwise the former SQLite revision would lose a committed effect.
Rollback ==
    /\ owner = "postgres"
    /\ ~pgCommitted
    /\ owner' = "sqlite"
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

Spec == Init /\ [][Next]_Vars

=============================================================================
