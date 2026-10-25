------------------------- MODULE RuntimePgCutoverR1 -------------------------
EXTENDS Naturals

\* A finite abstraction, NOT the physical SQLite/PG migration or cryptographic
\* verification. Content identities are two opaque distinct values; a copied
\* source revision need not imply a matching source payload. The importer may
\* copy corrupt content; only explicit readback parity certifies promotion.
\* "owner" is one durable writer authority, not two independent booleans.
VARIABLES owner, sqliteRevision, pgRevision, sqliteContent, pgContent,
          copied, parityVerified, cutoverCertified, pgCommitted, rolledBack,
          sqliteWriterActive, pgWriterActive, consumersQualified

Vars == <<owner, sqliteRevision, pgRevision, sqliteContent, pgContent,
          copied, parityVerified, cutoverCertified, pgCommitted, rolledBack,
          sqliteWriterActive, pgWriterActive, consumersQualified>>

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
    /\ consumersQualified = FALSE

SqliteCommit ==
    /\ owner = "sqlite"
    /\ sqliteWriterActive
    /\ sqliteRevision < 2
    /\ sqliteRevision' = sqliteRevision + 1
    /\ sqliteContent' = IF sqliteContent = 0 THEN 1 ELSE 0
    /\ copied' = FALSE
    /\ parityVerified' = FALSE
    /\ consumersQualified' = FALSE
    /\ UNCHANGED <<owner, pgRevision, pgContent, cutoverCertified,
                   pgCommitted, rolledBack, sqliteWriterActive, pgWriterActive>>

Freeze ==
    /\ owner = "sqlite"
    /\ sqliteWriterActive
    /\ owner' = "paused"
    /\ sqliteWriterActive' = FALSE
    /\ parityVerified' = FALSE
    /\ consumersQualified' = FALSE
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
    /\ consumersQualified' = FALSE
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
                   sqliteWriterActive, pgWriterActive, consumersQualified>>

\* An independent real-consumer receipt must be qualified before promotion.
\* This action is explicitly an UNVERIFIED external oracle, not receipt
\* authentication or implementation refinement.
QualifyConsumers ==
    /\ owner = "paused"
    /\ copied
    /\ parityVerified
    /\ pgRevision = sqliteRevision
    /\ pgContent = sqliteContent
    /\ ~sqliteWriterActive
    /\ ~pgWriterActive
    /\ consumersQualified' = TRUE
    /\ UNCHANGED <<owner, sqliteRevision, pgRevision, sqliteContent,
                   pgContent, copied, parityVerified, cutoverCertified,
                   pgCommitted, rolledBack, sqliteWriterActive, pgWriterActive>>

Promote ==
    /\ owner = "paused"
    /\ parityVerified
    /\ consumersQualified
    /\ pgRevision = sqliteRevision
    /\ ~sqliteWriterActive
    /\ ~pgWriterActive
    /\ owner' = "postgres"
    /\ pgWriterActive' = TRUE
    /\ cutoverCertified' = TRUE
    /\ rolledBack' = FALSE
    /\ UNCHANGED <<sqliteRevision, pgRevision, sqliteContent, pgContent,
                   copied, parityVerified, pgCommitted, sqliteWriterActive,
                   consumersQualified>>

PostgresCommit ==
    /\ owner = "postgres"
    /\ pgWriterActive
    /\ pgRevision < 2
    /\ pgRevision' = pgRevision + 1
    /\ pgContent' = IF pgContent = 0 THEN 1 ELSE 0
    /\ pgCommitted' = TRUE
    /\ UNCHANGED <<owner, sqliteRevision, sqliteContent, copied,
                   parityVerified, cutoverCertified, rolledBack,
                   sqliteWriterActive, pgWriterActive, consumersQualified>>

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
    /\ consumersQualified' = FALSE
    /\ UNCHANGED <<sqliteRevision, pgRevision, sqliteContent, pgContent,
                   cutoverCertified, pgCommitted>>

\* If PG consumer/readback certification fails after we quiesce SQLite but
\* BEFORE PG's first commit, abandoning the proposed cutover may restart
\* the *same* SQLite authority. This is a design transition, not a claim
\* that the installed Rust Runtime implements a durable fencing protocol.
AbortPaused ==
    /\ owner = "paused"
    /\ ~sqliteWriterActive
    /\ ~pgWriterActive
    /\ ~pgCommitted
    /\ owner' = "sqlite"
    /\ sqliteWriterActive' = TRUE
    /\ copied' = FALSE
    /\ parityVerified' = FALSE
    /\ consumersQualified' = FALSE
    /\ rolledBack' = TRUE
    /\ UNCHANGED <<sqliteRevision, pgRevision, sqliteContent, pgContent,
                   cutoverCertified, pgCommitted, pgWriterActive>>

Next ==
    \/ SqliteCommit
    \/ Freeze
    \/ CopySnapshot
    \/ VerifyParity
    \/ QualifyConsumers
    \/ Promote
    \/ PostgresCommit
    \/ Rollback
    \/ AbortPaused

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
    /\ consumersQualified \in BOOLEAN

PostgresRequiresCertifiedCutover ==
    owner = "postgres" => cutoverCertified

\* Copy/readback parity alone cannot authorize a PostgreSQL writer when real
\* consumers still point at SQLite. Concrete receipt binding remains UNKNOWN.
PgWriterRequiresQualifiedConsumers ==
    pgWriterActive => consumersQualified

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


\* Lifecycle consistency is stronger than merely forbidding two concurrent
\* writers: a paused authority may have neither; a live one must have exactly
\* the corresponding process-level writer commitment.
InstalledWriterMatchesAuthority ==
    /\ (owner = "sqlite" => sqliteWriterActive /\ ~pgWriterActive)
    /\ (owner = "paused" => ~sqliteWriterActive /\ ~pgWriterActive)
    /\ (owner = "postgres" => pgWriterActive /\ ~sqliteWriterActive)

\* Failure/abort must never accidentally reuse copied PG content or old
\* consumer certification to promote an obsolete source snapshot.
NoRetainedQualificationOnSqlite ==
    owner = "sqlite" => ~parityVerified /\ ~consumersQualified

\* A failed PG candidate is a *recoverable design state*, not permanent
\* self-deadlock from quiescing SQLite. This is enabledness, NOT fairness.
PrecommitAbortEnabled ==
    (owner = "paused" /\ ~pgCommitted) => ENABLED AbortPaused

Spec == Init /\ [][Next]_Vars

=============================================================================
