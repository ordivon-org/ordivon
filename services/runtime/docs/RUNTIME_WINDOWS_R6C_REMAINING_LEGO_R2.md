# Native Windows R6c Remaining LEGO Plan R2

Status: active acceptance plan
Date: 2026-09-19
Candidate service: OrdivonRuntimeR6Candidate
Candidate node: windows-main-r6-candidate
Candidate endpoint: 127.0.0.1:18997
Production endpoint 127.0.0.1:8897 remains out of scope until final cutover.

## LEGO C1 — crash / SCM recovery

Authority owner:
- Windows SCM owns service failure detection and restart timing.

Fault:
- terminate only the candidate service process, never the live Linux Runtime.

Required evidence:
1. bind candidate PID before the fault;
2. cause an unambiguous non-graceful exit;
3. observe the candidate endpoint become unavailable or service process identity disappear;
4. observe SCM return the service to RUNNING;
5. bind a different process identity after restart;
6. authenticated MCP runtime.describe succeeds from the restarted process.

Acceptance:
- all six observations belong to one causally bound experiment.

Non-evidence:
- a lost external probe Attempt by itself;
- HTTP 401 without proof that a crash actually occurred;
- SCM configuration read-back without failure injection.

## LEGO C2 — active Job reconciliation

Authority owner:
- Runtime Registry/Attempt reconciliation owns physical execution truth after restart.

Setup:
- admit one candidate-owned Windows Job whose target remains live long enough to overlap a Runtime
  service crash.

Fault:
- crash the candidate Runtime service process while that Job is nonterminal.

Required evidence:
1. exact Job and Attempt identities are durable before the fault;
2. restart does not create a second Job for the same client request;
3. the surviving/terminated Windows Job Object state is observed by the restarted Runtime;
4. terminal classification is based on durable/native evidence, not guessed from transport loss;
5. global/workspace capacity is released only after terminal evidence is committed;
6. exact request replay returns the same Job identity.

Acceptance:
- no duplicate dispatch and no speculative success/failure classification.

## LEGO C3 — WSL independence

Authority owner:
- Windows SCM owns windows-main lifecycle.
- Microsoft wsl.exe owns WSL distribution lifecycle.

Precondition:
- observation of windows-main must not depend on a WSL-hosted Windows provider.

Experiment:
1. prove candidate RUNNING and authenticated MCP reachable;
2. from Windows authority invoke exact wsl.exe --terminate <distribution>;
3. observe that distribution is offline from Windows;
4. prove candidate service remains RUNNING and MCP reachable;
5. repeat later with wsl.exe --shutdown if safe for all current work.

Important:
- terminating WSL can interrupt the current live Linux Runtime and other conversations. Therefore
  C3 destructive execution is deferred until the candidate can become the observation/control
  carrier for the acceptance itself and all active WSL-dependent work has an explicit disposition.

Acceptance:
- Windows-main remains available while WSL is genuinely offline.

## LEGO C4 — cold boot / auto start

Authority owner:
- Windows boot + SCM AUTO_START.

Required evidence:
1. service is configured AUTO_START before reboot;
2. exact candidate artifact/config digests are recorded;
3. after a real Windows reboot, SCM reports a new boot/process identity and RUNNING;
4. MCP runtime.describe reports the same node/config identity;
5. Registry reconciliation completes without duplicate dispatch.

Safety:
- a real reboot is a host-wide destructive operation. It is deferred until active conversations,
  Runtime workspaces and other host workloads have an explicit recovery disposition.

Acceptance:
- no interactive login, WSL startup, Task Scheduler wrapper or manual command is required.

## LEGO C5 — final cutover and carrier deletion

Authority owner:
- release/cutover operation owns the single production transition.

Preconditions:
- C1 and C2 PASS;
- C3 PASS;
- C4 PASS or an explicitly accepted equivalent boot witness;
- production source/main has absorbed the accepted candidate chain without unresolved concurrent
  changes;
- full Windows/Linux regression gates pass on the exact release commit.

Cutover:
1. make accepted native Windows build windows-main;
2. verify production MCP/tool catalog and native node projection;
3. verify Host/clients can reach the new authority;
4. mark WSL-hosted Windows provider unreachable;
5. delete the WSL Windows control-plane carrier, obsolete watchdog/supervisor material and retired
   EF6 workflow artifacts only after claimant checks.

Terminal condition:
- no production semantic depends on the old WSL-hosted Windows control path.

## Dependency graph

C1 crash recovery
       |
       +------+
       |      |
       v      v
C2 reconciliation   C3 WSL independence
       |              |
       +------+-------+
              |
              v
          C4 cold boot
              |
              v
        C5 final cutover
              |
              v
     compatibility deletion

C3 and C4 remain deliberately gated because they can disrupt unrelated active work. C1/C2 are
side-by-side candidate experiments and can proceed without touching production 8897.
