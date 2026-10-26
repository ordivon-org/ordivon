-------------------- MODULE RuntimeWindowsFirstPgR1 --------------------
EXTENDS Naturals

\* Two-node *design* model. "Qualified" represents an externally supplied,
\* exact source/consumer/installed-writer receipt; TLC cannot manufacture
\* or authenticate that receipt from production Windows/PG observations.
\* Keep the existing RuntimePgCutoverR1 per-node data-parity model separate.
VARIABLES windows, linux, windowsReceipt, linuxReceipt

Vars == <<windows, linux, windowsReceipt, linuxReceipt>>
Phases == {"sqlite", "staged", "qualified", "postgres", "committed"}
PgPhases == {"postgres", "committed"}

Init ==
    /\ windows = "sqlite"
    /\ linux = "sqlite"
    /\ windowsReceipt = FALSE
    /\ linuxReceipt = FALSE

StageWindows ==
    /\ windows = "sqlite"
    /\ windows' = "staged"
    /\ UNCHANGED <<linux, windowsReceipt, linuxReceipt>>

\* Abstract acceptance of a real, independently validated Windows receipt.
QualifyWindows ==
    /\ windows = "staged"
    /\ windows' = "qualified"
    /\ UNCHANGED <<linux, windowsReceipt, linuxReceipt>>

PromoteWindows ==
    /\ windows = "qualified"
    /\ windows' = "postgres"
    /\ windowsReceipt' = TRUE
    /\ UNCHANGED <<linux, linuxReceipt>>

CommitWindows ==
    /\ windows = "postgres"
    /\ windows' = "committed"
    /\ UNCHANGED <<linux, windowsReceipt, linuxReceipt>>

\* Before the first independent Windows PG commit, Windows may roll back
\* only if Linux has NOT promoted. Its previous receipt becomes invalid.
RollbackWindows ==
    /\ windows = "postgres"
    /\ linux \in {"sqlite", "staged"}
    /\ windows' = "sqlite"
    /\ windowsReceipt' = FALSE
    /\ UNCHANGED <<linux, linuxReceipt>>

StageLinux ==
    /\ linux = "sqlite"
    /\ linux' = "staged"
    /\ UNCHANGED <<windows, windowsReceipt, linuxReceipt>>

QualifyLinux ==
    /\ linux = "staged"
    /\ windows \in PgPhases
    /\ windowsReceipt
    /\ linux' = "qualified"
    /\ UNCHANGED <<windows, windowsReceipt, linuxReceipt>>

PromoteLinux ==
    /\ linux = "qualified"
    /\ windows \in PgPhases
    /\ windowsReceipt
    /\ linux' = "postgres"
    /\ linuxReceipt' = TRUE
    /\ UNCHANGED <<windows, windowsReceipt>>

CommitLinux ==
    /\ linux = "postgres"
    /\ linux' = "committed"
    /\ UNCHANGED <<windows, windowsReceipt, linuxReceipt>>

Next ==
    \/ StageWindows
    \/ QualifyWindows
    \/ PromoteWindows
    \/ CommitWindows
    \/ RollbackWindows
    \/ StageLinux
    \/ QualifyLinux
    \/ PromoteLinux
    \/ CommitLinux

TypeOK ==
    /\ windows \in Phases
    /\ linux \in Phases
    /\ windowsReceipt \in BOOLEAN
    /\ linuxReceipt \in BOOLEAN

\* The user-specified physical deployment order, not merely a preference:
\* no Linux PG writer even enters its qualified phase without a Windows
\* accepted live-writer receipt. Source stage/copy may precede it.
WindowsBeforeLinuxPg ==
    linux \in {"qualified", "postgres", "committed"}
      => (windows \in PgPhases /\ windowsReceipt)

WindowsReceiptNotFromStaging ==
    windowsReceipt => windows \in PgPhases

LinuxReceiptNotFromStaging ==
    linuxReceipt => linux \in PgPhases

\* Only used for an independent reachability/anti-vacuity TLC run. It must
\* be falsified by the *valid* Windows-then-Linux promotion sequence.
LinuxNeverPromoted == linux \notin PgPhases

Spec == Init /\ [][Next]_Vars
=============================================================================
