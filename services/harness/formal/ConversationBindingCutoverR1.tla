---- MODULE ConversationBindingCutoverR1 ----
EXTENDS Naturals

(***************************************************************************)
(* H04 source-bound ConversationBinding cutover; NOT a generic two-phase   *)
(* database transaction or deployed process-quiescence proof.             *)
(* PG commit can precede SQLite writer retirement. Old identities must    *)
(* remain preserved across this interruption and later PG-only growth.    *)
(***************************************************************************)

CONSTANTS LegacyIdentity, PgOnlyIdentity
ASSUME LegacyIdentity # PgOnlyIdentity
Identities == {LegacyIdentity, PgOnlyIdentity}

VARIABLES legacyRows, pgRows, oldWriterActive, pgCommitted,
          oldSealed, pgAdmitted, interrupted, retried
vars == <<legacyRows, pgRows, oldWriterActive, pgCommitted,
          oldSealed, pgAdmitted, interrupted, retried>>

TypeOK ==
    /\ legacyRows \subseteq Identities
    /\ pgRows \subseteq Identities
    /\ oldWriterActive \in BOOLEAN
    /\ pgCommitted \in BOOLEAN
    /\ oldSealed \in BOOLEAN
    /\ pgAdmitted \in BOOLEAN
    /\ interrupted \in BOOLEAN
    /\ retried \in BOOLEAN

Init ==
    /\ legacyRows = {LegacyIdentity}
    /\ pgRows = {}
    /\ oldWriterActive = TRUE
    /\ pgCommitted = FALSE
    /\ oldSealed = FALSE
    /\ pgAdmitted = FALSE
    /\ interrupted = FALSE
    /\ retried = FALSE

QuiesceOldWriter ==
    /\ oldWriterActive
    /\ oldWriterActive' = FALSE
    /\ UNCHANGED <<legacyRows, pgRows, pgCommitted, oldSealed,
                   pgAdmitted, interrupted, retried>>

CommitPgImport ==
    /\ ~oldWriterActive
    /\ ~pgCommitted
    /\ pgRows' = legacyRows
    /\ pgCommitted' = TRUE
    /\ UNCHANGED <<legacyRows, oldWriterActive, oldSealed,
                   pgAdmitted, interrupted, retried>>

LoseMigrationResponse ==
    /\ pgCommitted
    /\ ~oldSealed
    /\ ~interrupted
    /\ interrupted' = TRUE
    /\ UNCHANGED <<legacyRows, pgRows, oldWriterActive, pgCommitted,
                   oldSealed, pgAdmitted, retried>>

RecoverMigration ==
    /\ interrupted
    /\ interrupted' = FALSE
    /\ UNCHANGED <<legacyRows, pgRows, oldWriterActive, pgCommitted,
                   oldSealed, pgAdmitted, retried>>

SealOldWriter ==
    /\ pgCommitted
    /\ ~oldWriterActive
    /\ ~interrupted
    /\ pgRows = legacyRows
    /\ ~oldSealed
    /\ oldSealed' = TRUE
    /\ UNCHANGED <<legacyRows, pgRows, oldWriterActive, pgCommitted,
                   pgAdmitted, interrupted, retried>>

AdmitPgBinding ==
    /\ pgCommitted
    /\ oldSealed
    /\ ~oldWriterActive
    /\ ~pgAdmitted
    /\ pgAdmitted' = TRUE
    /\ UNCHANGED <<legacyRows, pgRows, oldWriterActive, pgCommitted,
                   oldSealed, interrupted, retried>>

PgOnlyAdoption ==
    /\ pgAdmitted
    /\ PgOnlyIdentity \notin pgRows
    /\ pgRows' = pgRows \cup {PgOnlyIdentity}
    /\ UNCHANGED <<legacyRows, oldWriterActive, pgCommitted,
                   oldSealed, pgAdmitted, interrupted, retried>>

ReplaySourceCutover ==
    /\ oldSealed
    /\ pgCommitted
    /\ legacyRows \subseteq pgRows
    /\ ~retried
    /\ retried' = TRUE
    /\ UNCHANGED <<legacyRows, pgRows, oldWriterActive, pgCommitted,
                   oldSealed, pgAdmitted, interrupted>>

Next ==
    \/ QuiesceOldWriter
    \/ CommitPgImport
    \/ LoseMigrationResponse
    \/ RecoverMigration
    \/ SealOldWriter
    \/ AdmitPgBinding
    \/ PgOnlyAdoption
    \/ ReplaySourceCutover

Spec == Init /\ [][Next]_vars

NoPGAdmissionBeforeSourceSeal ==
    pgAdmitted => oldSealed /\ pgCommitted /\ ~oldWriterActive

NoOldWriterAfterSealing ==
    oldSealed => ~oldWriterActive

CommittedSourceIdentityPreserved ==
    pgCommitted => legacyRows \subseteq pgRows

NoPGOnlyRowsBeforeAdmission ==
    ~pgAdmitted => PgOnlyIdentity \notin pgRows

SourceSealRequiresExactFirstImport ==
    oldSealed => pgCommitted /\ LegacyIdentity \in pgRows

(* Deliberately FALSE independent reachability witnesses. *)
PgAdmissionIsUnreachable == ~pgAdmitted
InterruptedImportIsUnreachable == ~(interrupted /\ pgCommitted /\ ~oldSealed)
PostCutoverGrowthReplayIsUnreachable ==
    ~(retried /\ PgOnlyIdentity \in pgRows)
=============================================================================
