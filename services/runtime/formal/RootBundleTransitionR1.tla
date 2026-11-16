--------------------- MODULE RootBundleTransitionR1 ----------------------
EXTENDS Naturals

\* ROOT-BUNDLE MODEL, NOT AN INSTALLED ROOT INSTALLER.
\* Existing protected Git candidate + trusted Root administrator + original
\* release Postgres transaction-level advisory lock and qualified row +
\* original operator flock + systemd quiescence + one renameat2 exchange.
\* File identities are opaque values. Old/New each means all five Root files,
\* not per-file bytes. The model is a bounded design obligation, not an
\* implementation refinement, credential proof or power-loss certification.
\*
\* Concrete positive witnesses:
\*   NativePG job-01a1e59d-4e33-7541-adb1-831c6314eaaf
\*   NativePG job-01a1e5a0-93e6-73a5-8312-3311d1619727
\*   NativePG job-01a1e5a5-57e1-72ae-832b-3479d82078ad
\* Concrete negative: an old systemd Python entrypoint can import a new
\* module after changing the live directory while the old process runs:
\*   NativePG job-01a1e57a-a76c-727e-bd7e-94c8463cd909

VARIABLES pgAllowed, timerOn, activeProcess, pendingEffect, rootLock,
          rootAlive, unitQualified, live, spare, journal, postSwapCrashSeen
vars == <<pgAllowed, timerOn, activeProcess, pendingEffect, rootLock,
          rootAlive, unitQualified, live, spare, journal, postSwapCrashSeen>>

Old == "old-five-file-bundle"
New == "new-five-file-bundle"
Mixed == "one-of-five-files-replaced"

Init ==
    /\ pgAllowed = TRUE
    /\ timerOn = TRUE
    /\ activeProcess = "none"
    /\ pendingEffect = FALSE
    /\ rootLock = FALSE
    /\ rootAlive = TRUE
    /\ unitQualified = FALSE
    /\ live = Old
    /\ spare = New
    /\ journal = "none"
    /\ postSwapCrashSeen = FALSE

\* The PG release qualification is a durable committed row. Advisory xact
\* locks serialize this change but do not remain held after commit.
RevokeRelease ==
    /\ rootAlive /\ pgAllowed
    /\ journal \in {"none", "terminal"}
    /\ pgAllowed' = FALSE
    /\ UNCHANGED <<timerOn, activeProcess, pendingEffect, rootLock,
                   rootAlive, unitQualified, live, spare, journal, postSwapCrashSeen>>

\* A timer is a producer of independent one-shot services; stopping the
\* timer alone does not stop a process already admitted/running.
DisableTimer ==
    /\ rootAlive /\ ~pgAllowed /\ timerOn
    /\ timerOn' = FALSE
    /\ UNCHANGED <<pgAllowed, activeProcess, pendingEffect, rootLock,
                   rootAlive, unitQualified, live, spare, journal, postSwapCrashSeen>>

StartOldProcess ==
    /\ rootAlive /\ pgAllowed /\ timerOn /\ activeProcess = "none"
    /\ journal = "none"
    /\ activeProcess' = "old"
    /\ UNCHANGED <<pgAllowed, timerOn, pendingEffect, rootLock,
                   rootAlive, unitQualified, live, spare, journal, postSwapCrashSeen>>

FinishOldProcess ==
    /\ activeProcess = "old"
    /\ activeProcess' = "none"
    /\ UNCHANGED <<pgAllowed, timerOn, pendingEffect, rootLock,
                   rootAlive, unitQualified, live, spare, journal, postSwapCrashSeen>>

\* Reverse upgrade can race an already admitted NEW interpreter just
\* as forward upgrade can race an OLD interpreter. The two directions must
\* satisfy distinct process version quiescence.
StartNewProcess ==
    /\ rootAlive /\ pgAllowed /\ timerOn /\ activeProcess = "none"
    /\ journal = "terminal" /\ live = New
    /\ activeProcess' = "new"
    /\ UNCHANGED <<pgAllowed, timerOn, pendingEffect, rootLock,
                   rootAlive, unitQualified, live, spare, journal, postSwapCrashSeen>>

FinishNewProcess ==
    /\ activeProcess = "new"
    /\ activeProcess' = "none"
    /\ UNCHANGED <<pgAllowed, timerOn, pendingEffect, rootLock,
                   rootAlive, unitQualified, live, spare, journal, postSwapCrashSeen>>

AdmitOldEffect ==
    /\ pgAllowed /\ journal = "none" /\ ~pendingEffect
    /\ pendingEffect' = TRUE
    /\ UNCHANGED <<pgAllowed, timerOn, activeProcess, rootLock,
                   rootAlive, unitQualified, live, spare, journal, postSwapCrashSeen>>

AdmitNewEffect ==
    /\ pgAllowed /\ journal = "terminal" /\ live = New
    /\ ~pendingEffect
    /\ pendingEffect' = TRUE
    /\ UNCHANGED <<pgAllowed, timerOn, activeProcess, rootLock,
                   rootAlive, unitQualified, live, spare, journal, postSwapCrashSeen>>

SettleEffect ==
    /\ pendingEffect
    /\ pendingEffect' = FALSE
    /\ UNCHANGED <<pgAllowed, timerOn, activeProcess, rootLock,
                   rootAlive, unitQualified, live, spare, journal, postSwapCrashSeen>>

\* An effective compatible -B service unit is the sixth consumer,
\* outside the live five-file Root bundle. This abstraction assumes a
\* qualified Root installer applies and reads back that Unit.
\* A compatible packaged systemd unit can be installed before the old
\* one-shot has finished. No process-safety claim follows from doing so.
\* The later DurablePrepare must still explicitly prove process quiescence.
QualifyCompatibleUnit ==
    /\ rootAlive /\ ~pgAllowed /\ ~timerOn
    /\ ~unitQualified
    /\ unitQualified' = TRUE
    /\ UNCHANGED <<pgAllowed, timerOn, activeProcess, pendingEffect, rootLock,
                   rootAlive, live, spare, journal, postSwapCrashSeen>>

AcquireOriginalOperatorLock ==
    /\ rootAlive /\ ~pgAllowed /\ ~timerOn /\ ~rootLock
    /\ journal \in {"none", "prepared", "exchanged", "terminal",
                    "rollback_prepared", "rolledback"}
    /\ rootLock' = TRUE
    /\ UNCHANGED <<pgAllowed, timerOn, activeProcess, pendingEffect,
                   rootAlive, unitQualified, live, spare, journal, postSwapCrashSeen>>

DurablePrepare ==
    /\ rootAlive /\ rootLock /\ ~pgAllowed /\ ~timerOn
    /\ activeProcess = "none" /\ ~pendingEffect /\ unitQualified
    /\ journal = "none" /\ live = Old /\ spare = New
    /\ journal' = "prepared"
    /\ UNCHANGED <<pgAllowed, timerOn, activeProcess, pendingEffect,
                   rootLock, rootAlive, unitQualified, live, spare, postSwapCrashSeen>>

\* One atomic namespace linearization point, not five per-file copies.
AtomicBundleExchange ==
    /\ rootAlive /\ rootLock /\ ~pgAllowed /\ ~timerOn
    /\ activeProcess = "none" /\ ~pendingEffect /\ unitQualified
    /\ journal = "prepared" /\ live = Old /\ spare = New
    /\ live' = New /\ spare' = Old
    /\ UNCHANGED <<pgAllowed, timerOn, activeProcess, pendingEffect, rootLock,
                   rootAlive, unitQualified, journal, postSwapCrashSeen>>

\* Journal can still be PREPARED after rename committed but response was lost.
\* Native Root must rehash both directories before recording this transition.
RecoverExchangedBytes ==
    /\ rootAlive /\ rootLock /\ ~pgAllowed /\ ~timerOn
    /\ activeProcess = "none" /\ ~pendingEffect /\ unitQualified
    /\ journal = "prepared" /\ live = New /\ spare = Old
    /\ journal' = "exchanged"
    /\ UNCHANGED <<pgAllowed, timerOn, activeProcess, pendingEffect, rootLock,
                   rootAlive, unitQualified, live, spare, postSwapCrashSeen>>

WriteTrustedTerminalReceipt ==
    /\ rootAlive /\ rootLock /\ ~pgAllowed /\ ~timerOn
    /\ activeProcess = "none" /\ ~pendingEffect /\ unitQualified
    /\ journal = "exchanged" /\ live = New /\ spare = Old
    /\ journal' = "terminal"
    /\ UNCHANGED <<pgAllowed, timerOn, activeProcess, pendingEffect, rootLock,
                   rootAlive, unitQualified, live, spare, postSwapCrashSeen>>

\* PG may only reopen after trusted bytes, imports and receipt were certified.
ResumeQualifiedRelease ==
    /\ rootAlive /\ rootLock /\ ~pgAllowed /\ ~timerOn
    /\ journal = "terminal" /\ live = New /\ spare = Old
    /\ pgAllowed' = TRUE
    /\ UNCHANGED <<timerOn, activeProcess, pendingEffect, rootLock,
                   rootAlive, unitQualified, live, spare, journal, postSwapCrashSeen>>

ResumeTimer ==
    /\ rootAlive /\ rootLock /\ pgAllowed /\ ~timerOn
    /\ journal \in {"terminal", "abort_terminal", "rolledback"}
    /\ timerOn' = TRUE
    /\ UNCHANGED <<pgAllowed, activeProcess, pendingEffect, rootLock,
                   rootAlive, unitQualified, live, spare, journal, postSwapCrashSeen>>

ReleaseOriginalOperatorLock ==
    /\ rootAlive /\ rootLock /\ timerOn /\ pgAllowed
    /\ journal \in {"terminal", "abort_terminal", "rolledback"}
    /\ rootLock' = FALSE
    /\ UNCHANGED <<pgAllowed, timerOn, activeProcess, pendingEffect,
                   rootAlive, unitQualified, live, spare, journal, postSwapCrashSeen>>

\* A failure before swap can resume the intact old package only if the
\* physical bytes are still definitely old; unknown/revised states HOLD.
AbortBeforeExchange ==
    /\ rootAlive /\ rootLock /\ ~pgAllowed /\ ~timerOn
    /\ journal = "prepared" /\ live = Old /\ spare = New
    /\ activeProcess = "none" /\ ~pendingEffect
    /\ journal' = "abort_terminal"
    /\ UNCHANGED <<pgAllowed, timerOn, activeProcess, pendingEffect, rootLock,
                   rootAlive, unitQualified, live, spare, postSwapCrashSeen>>

ResumeAbortedOldRelease ==
    /\ rootAlive /\ rootLock /\ ~pgAllowed /\ ~timerOn
    /\ journal = "abort_terminal" /\ live = Old /\ spare = New
    /\ pgAllowed' = TRUE
    /\ UNCHANGED <<timerOn, activeProcess, pendingEffect, rootLock,
                   rootAlive, unitQualified, live, spare, journal, postSwapCrashSeen>>

\* Rollback is another new qualified effect, not a blind replay of a
\* possibly committed forward exchange.
PrepareNewRollback ==
    /\ rootAlive /\ rootLock /\ ~pgAllowed /\ ~timerOn
    /\ journal = "terminal" /\ live = New /\ spare = Old
    /\ activeProcess = "none" /\ ~pendingEffect
    /\ journal' = "rollback_prepared"
    /\ UNCHANGED <<pgAllowed, timerOn, activeProcess, pendingEffect, rootLock,
                   rootAlive, unitQualified, live, spare, postSwapCrashSeen>>

AtomicRollback ==
    /\ rootAlive /\ rootLock /\ ~pgAllowed /\ ~timerOn
    /\ journal = "rollback_prepared" /\ live = New /\ spare = Old
    /\ activeProcess = "none" /\ ~pendingEffect
    /\ live' = Old /\ spare' = New
    /\ UNCHANGED <<pgAllowed, timerOn, activeProcess, pendingEffect,
                   rootLock, rootAlive, unitQualified, journal, postSwapCrashSeen>>

RecoverRolledBackBytes ==
    /\ rootAlive /\ rootLock /\ ~pgAllowed /\ ~timerOn
    /\ journal = "rollback_prepared" /\ live = Old /\ spare = New
    /\ journal' = "rolledback"
    /\ UNCHANGED <<pgAllowed, timerOn, activeProcess, pendingEffect,
                   rootLock, rootAlive, unitQualified, live, spare, postSwapCrashSeen>>

ResumeRolledBackOld ==
    /\ rootAlive /\ rootLock /\ ~pgAllowed /\ ~timerOn
    /\ journal = "rolledback" /\ live = Old /\ spare = New
    /\ pgAllowed' = TRUE
    /\ UNCHANGED <<timerOn, activeProcess, pendingEffect, rootLock,
                   rootAlive, unitQualified, live, spare, journal, postSwapCrashSeen>>

\* Root administrator crash drops its process-held flock. PG committed
\* qualification, persistent Timer configuration, directory bytes, and Root
\* journal remain; the next Root process must re-qualify/reconcile.
\* Only a crash after exchange under an unchanged PREPARED journal sets
\* postSwapCrashSeen; an arbitrary earlier crash does not satisfy recovery
\* path non-vacuity.
CrashRootController ==
    /\ rootAlive /\ rootLock /\ ~timerOn
    /\ rootAlive' = FALSE
    /\ rootLock' = FALSE
    /\ postSwapCrashSeen' =
          (postSwapCrashSeen \/ (journal = "prepared" /\ live = New /\ spare = Old))
    /\ UNCHANGED <<pgAllowed, timerOn, activeProcess, pendingEffect,
                   unitQualified, live, spare, journal>>

ReopenRootController ==
    /\ ~rootAlive /\ ~timerOn
    /\ rootAlive' = TRUE
    /\ UNCHANGED <<pgAllowed, timerOn, activeProcess, pendingEffect, rootLock,
                   unitQualified, live, spare, journal, postSwapCrashSeen>>

Next ==
    \/ RevokeRelease \/ DisableTimer \/ StartOldProcess
    \/ FinishOldProcess \/ StartNewProcess \/ FinishNewProcess
    \/ AdmitOldEffect \/ AdmitNewEffect \/ SettleEffect
    \/ QualifyCompatibleUnit \/ AcquireOriginalOperatorLock
    \/ DurablePrepare \/ AtomicBundleExchange
    \/ RecoverExchangedBytes \/ WriteTrustedTerminalReceipt
    \/ ResumeQualifiedRelease \/ ResumeTimer
    \/ ReleaseOriginalOperatorLock
    \/ AbortBeforeExchange \/ ResumeAbortedOldRelease
    \/ PrepareNewRollback \/ AtomicRollback \/ RecoverRolledBackBytes
    \/ ResumeRolledBackOld
    \/ CrashRootController \/ ReopenRootController

TypeOK ==
    /\ pgAllowed \in BOOLEAN /\ timerOn \in BOOLEAN
    /\ activeProcess \in {"none", "old", "new"} /\ pendingEffect \in BOOLEAN
    /\ rootLock \in BOOLEAN /\ rootAlive \in BOOLEAN
    /\ unitQualified \in BOOLEAN
    /\ postSwapCrashSeen \in BOOLEAN
    /\ live \in {Old, New, Mixed} /\ spare \in {Old, New}
    /\ journal \in {"none", "prepared", "exchanged", "terminal",
                    "abort_terminal", "rollback_prepared", "rolledback"}

NoPartialRootBundle == (live = Old /\ spare = New) \/
                       (live = New /\ spare = Old)
NoOldInterpreterDuringNewPackage == (live = New) => (activeProcess # "old")
NoOutstandingPreterminalEffectAfterSwap ==
    (live = New /\ journal \in {"prepared", "exchanged"}) => ~pendingEffect
NoNewInterpreterDuringRolledBackPackage ==
    (live = Old /\ journal \in {"rollback_prepared", "rolledback"}) =>
        (activeProcess # "new")
NoOutstandingPendingAfterRollback ==
    (live = Old /\ journal \in {"rollback_prepared", "rolledback"}) =>
        ~pendingEffect
NoReleaseAdmissionDuringAmbiguousExchange ==
    (journal \in {"prepared", "exchanged", "rollback_prepared"}) => ~pgAllowed
NoTimerDuringAmbiguousExchange ==
    (journal \in {"prepared", "exchanged", "rollback_prepared"}) => ~timerOn
TrustedTerminalHasPhysicalCandidate ==
    (journal = "terminal") => (live = New /\ spare = Old /\ unitQualified)
RolledBackHasOldPhysicalPackage ==
    (journal = "rolledback") => (live = Old /\ spare = New)

QualifiedNewRootIsReachable ==
    journal = "terminal" /\ pgAllowed /\ timerOn /\ ~rootLock /\
    live = New /\ spare = Old
RecoveryAfterRootCrashIsReachable ==
    postSwapCrashSeen /\ journal = "terminal" /\ pgAllowed /\ timerOn /\
    live = New /\ ~rootLock
QualifiedRollbackIsReachable ==
    journal = "rolledback" /\ pgAllowed /\ timerOn /\ ~rootLock /\
    live = Old /\ spare = New

\* Three intentionally forbidden alternatives, used only by falsifiers:
\* 1. Timer/PG stopped, but an *old process* has not exited. A swap can
\*    cause OLD entrypoint plus NEW late-bound Python module.
UnsafeSwapWhileOldInterpreter ==
    /\ rootAlive /\ rootLock /\ ~pgAllowed /\ ~timerOn
    /\ activeProcess = "old" /\ ~pendingEffect /\ unitQualified
    /\ live = Old /\ spare = New /\ journal = "none"
    /\ live' = New /\ spare' = Old /\ journal' = "prepared"
    /\ UNCHANGED <<pgAllowed, timerOn, activeProcess, pendingEffect, rootLock,
                   rootAlive, unitQualified, postSwapCrashSeen>>

\* 2. An 'exchange happened' observation without trusted terminal receipt
\*    cannot reopen the PostgreSQL release row.
UnsafeResumeWithOnlyPreparedJournal ==
    /\ rootAlive /\ rootLock /\ ~pgAllowed /\ ~timerOn
    /\ journal = "prepared" /\ live = New /\ spare = Old
    /\ pgAllowed' = TRUE /\ timerOn' = TRUE
    /\ UNCHANGED <<activeProcess, pendingEffect, rootLock, rootAlive,
                   unitQualified, live, spare, journal, postSwapCrashSeen>>

\* 3. An apparently quiescent timer with a NEW interpreter still running
\*    cannot authorize an exchange back to OLD bytes.
UnsafeRollbackWhileNewInterpreter ==
    /\ rootAlive /\ rootLock /\ ~pgAllowed /\ ~timerOn
    /\ activeProcess = "new" /\ ~pendingEffect
    /\ journal = "terminal" /\ live = New /\ spare = Old
    /\ live' = Old /\ spare' = New /\ journal' = "rollback_prepared"
    /\ UNCHANGED <<pgAllowed, timerOn, activeProcess, pendingEffect,
                   rootLock, rootAlive, unitQualified, postSwapCrashSeen>>

\* 3. Atomicity lost by copying just one of the five Root files.
UnsafeCopySingleRootFile ==
    /\ rootAlive /\ rootLock /\ ~pgAllowed /\ ~timerOn
    /\ journal = "prepared" /\ live = Old /\ spare = New
    /\ live' = Mixed
    /\ UNCHANGED <<pgAllowed, timerOn, activeProcess, pendingEffect, rootLock,
                   rootAlive, unitQualified, spare, journal, postSwapCrashSeen>>

Spec == Init /\ [][Next]_vars
UnsafeOldProcessSpec == Init /\ [][Next \/ UnsafeSwapWhileOldInterpreter]_vars
UnsafeEarlyResumeSpec == Init /\ [][Next \/ UnsafeResumeWithOnlyPreparedJournal]_vars
UnsafeRollbackProcessSpec == Init /\ [][Next \/ UnsafeRollbackWhileNewInterpreter]_vars
UnsafeFileCopySpec == Init /\ [][Next \/ UnsafeCopySingleRootFile]_vars

=============================================================================
